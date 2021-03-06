#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Tim Hartmann
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

import math
import random
import re
import statistics

import numpy as np

from qgis.core import (QgsWkbTypes, QgsField, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint, QgsPointXY,
                       QgsDistanceArea, QgsProcessingUtils, QgsRasterLayer, QgsCoordinateTransform, QgsProject)
from qgis.PyQt.QtCore import QVariant
from qgis import processing
from osgeo import gdal, osr

from .aStarOnRasterData import AStarOnRasterData


class AdvancedCostCalculator():
    """
    Class to calculate the edge costs of a graph by analysis of a cost function. The cost function
    can use different variables and operators.
    """

    def __init__(self, rLayers, vLayer, graph, polygons, usePolygons, rasterBands, task, allowDoubleEdges,
                 createShortestPathView=False):
        """
        Constructor

        :type rLayer: List of QgsRasterLayer
        :type vLayer: QgsVectorLayer
        :type graph: ExtGraph
        :type usePolygons: Boolean
        :type rasterBands: List of Integer [1..numberOfBands]
        """
        self.rLayers = rLayers
        self.vLayerFields = []
        self.vLayer = vLayer
        self.graph = graph
        self.allowDoubleEdges = allowDoubleEdges

        self.pointValuesForEdge = [None] * len(self.rLayers)
        self.pixelValuesForEdge = [None] * len(self.rLayers) * 6
        self.spForPointPairs = {}

        self.polygons = polygons
        self.usePolygons = usePolygons
        self.rasterBands = rasterBands
        self.operators = ["+", "-", "*", "/", "(", ")"]
        self.mathOperatorsWithTwoVar = ["pow", "dist", "comb", "copysign", "fmod", "ldexp", "remainder", "log", "atan2"]
        self.translatedParts = {}
        self.formulaParts = []
        self.aStarAlgObjects = []
        self.task = task
        self.createShortestPathView = createShortestPathView
        self.shortestPathViewLayers = []
        self.euclDistPixelNeighbors = []
        self.manDistPixelNeighbors = []
        self.geoDistPixelNeighbors = []
        self.ellDistPixelNeighbors = []

    def __translate(self, part, edgeID, sampledPointsLayer, edgesInPolygonsList=None,
                    edgesCrossingPolygonsList=None):
        """
        Method translates the given part into a number that can replace the variable in the formula.

        :type part: String
        :type edgeID: Int defining the edge that gets the translated weight
        :type sampledPointsLayer: List of features
        :type edgesInPolygonList: List of features
        :type edgesCrossingPolygonsList: List of features
        :return translated part as string
        """

        # check if part string was already translated
        if part in self.translatedParts.keys():
            return self.translatedParts[part]
        edge = self.graph.edge(edgeID)
        # operator or bracket do not need to be translated
        if part in self.operators or part.isnumeric() or part == "True" or part == "False":
            return str(part)

        try:
            float(part)
            return str(part)
        except ValueError:
            pass

        # normal distance metrics
        if part == "euclidean":
            return str(self.graph.euclideanDist(edgeID))

        if part == "manhattan":
            return str(self.graph.manhattanDist(edgeID))

        if part == "geodesic":
            return str(self.graph.geodesicDist(edgeID))

        if part == "ellipsoidal":
            return str(self.graph.ellipsoidalDist(edgeID))

        # translate polygon construct
        regex = re.compile(r'polygon\[[0-9]\]:crossesPolygon')
        res = regex.search(part)
        if res is not None:
            index = int(res.group().split("[")[1].split("]")[0])
            for feature in edgesCrossingPolygonsList[index].getFeatures():
                if edgeID == feature["ID"]:
                    return "True"
            return "False"

        # translate polygon construct
        regex = re.compile(r'polygon\[[0-9]\]:insidePolygon')
        res = regex.search(part)
        if res is not None:
            index = int(res.group().split("[")[1].split("]")[0])
            for feature in edgesInPolygonsList[index].getFeatures():
                if edgeID == feature["ID"]:
                    return "True"
            return "False"

        # python math method
        if "math." in part:
            try:
                mathOperation = part.split(".", 1)[1].split("%")[0]
                if mathOperation in self.mathOperatorsWithTwoVar:
                    # recursive calls
                    var1 = part.split("%")[1].split(",")[0]
                    var2 = part.split("$")[0].split(",")[1]
                    return "math." + mathOperation + "(" + var1 + "," + var2 + ")"
                else:
                    # recursive call
                    var = part.split("$")[0].split("%")[1]
                    return "math." + mathOperation + "(" + var + ")"
            except Exception:
                pass

        if "rnd?" in part:
            lb = part.split("?")[1].split("??")[0]
            ub = part.split("&")[0].split("??")[1]

            if lb.isnumeric() and ub.isnumeric():
                if int(lb) > int(ub):
                    return str(0)
                return str(random.randint(int(lb), int(ub)))
            try:
                convertedLB = float(eval(lb))
                convertedUB = float(eval(ub))
                if convertedLB > convertedUB:
                    return str(0)
                return str(random.uniform(convertedLB, convertedUB))
            except Exception:
                pass

            return part

        # translate if part
        if "if" in part:
            expression = part.split(";")[0].split("{", 1)[1]
            expression = expression.replace("and", " and ")
            expression = expression.replace("or", " or ")
            expressionParts = re.split("and|or", expression)
            for expPart in expressionParts:
                if "pixelValue" in expPart:
                    listString = expPart.split("(")[1].split(")")[0]
                    if "," in listString:
                        listStringSplit = listString.split(",")
                        equalTrue = False
                        for l in listStringSplit:
                            toEval = re.sub(r"pixelValue\(([0-9]+,)+[0-9]+\)", "", expPart)
                            toEval = l + toEval
                            if eval(toEval) == True:
                                expression = expression.replace(expPart, " True ")
                                equalTrue = True
                                break
                        if equalTrue == False:
                            expression = expression.replace(expPart, " False ")

                    # only one value in list
                    else:
                        toEval = re.sub(r"pixelValue\([0-9]\)", "", expPart)
                        toEval = listString + toEval
                        if eval(toEval) == True:
                            expression = expression.replace(expPart, " True ")
                            break
                        else:
                            expression = expression.replace(expPart, " False ")

                if "percentOfValues" in expPart:
                    # percentage is first value in the list
                    listString = expPart.split("(")[1].split(")")[0]
                    listStringSplit = listString.split(",")
                    percentage = listStringSplit[0]
                    trueExpFount = 0
                    for l in range(1, len(listStringSplit)):
                        toEval = re.sub(r"percentOfValues\(([0-9]+,)+[0-9]+\)", "", expPart)
                        toEval = listStringSplit[l] + toEval

                        if eval(toEval) == True:
                            trueExpFount += 1
                    if int(percentage) <= (trueExpFount / (len(listStringSplit)-1))*100:
                        expression = expression.replace(expPart, " True ")
                    else:
                        expression = expression.replace(expPart, " False ")

            if eval(expression) == True:
                return str(eval(part.split(";")[1]))
            else:
                return str(eval(part.split(";")[2].split("}")[0]))

        # get specified field information from feature
        if "field:" in part:
            name = part.split(":")[1]
            if self.vLayer.geometryType() == QgsWkbTypes.LineGeometry and not self.usePolygons:
                return str((self.graph.featureMatchings[edgeID])[name])

            # if polygons are used edges get deleted thus its not possible to just iterate the edges
            elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry and self.usePolygons:
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()
                    if QgsWkbTypes.isMultiType(geom.wkbType()):
                        for part in geom.asMultiPolyline():
                            for i in range(1, len(part)):
                                if part[i-1] == self.graph.vertex(edge.fromVertex()).point() and\
                                   part[i] == self.graph.vertex(edge.toVertex()).point():
                                    return str(feature[name])
                    else:
                        vertices = geom.asPolyline()
                        for i in range(len(vertices)-1):
                            if vertices[i] == self.graph.vertex(edge.fromVertex()).point() and\
                               vertices[i+1] == self.graph.vertex(edge.toVertex()).point():
                                return str(feature[name])

            # use information from points to set the edge weights
            # only incoming edges are considered
            elif self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                return str((self.graph.pointsToFeatureHash[self.graph.vertex(edge.toVertex()).point()
                                                                                             .toString()])[name])

        # analysis of raster data
        if "raster[" in part:
            rasterDataID = int(part.split("[")[1].split("]")[0])
            bandForRaster = self.rasterBands[rasterDataID]
            stringForLookup = "SAMPLE_" + str(bandForRaster)
            # check if the pointValues are already created for this edge
            if self.pointValuesForEdge[rasterDataID] is None:
                self.pointValuesForEdge[rasterDataID] = []
                # search for the right edgeID
                for feature in sampledPointsLayer[rasterDataID].getFeatures():
                    if feature["line_id"] == edgeID:
                        pointValue = feature[stringForLookup]
                        if pointValue is None:
                            pointValue = 0
                        self.pointValuesForEdge[rasterDataID].append(pointValue)

            if ":sp" in part:
                # search for correct aStarAlgObject
                if "," in part:
                    heurID = int(part.split("(")[1].split(")")[0].split(",")[0])
                else:
                    heurID = int(part.split("(")[1].split(")")[0])
                numberOfDiagonals = None
                for aStarObj in self.aStarAlgObjects:
                    if aStarObj.heuristicID == heurID and aStarObj.rasterID == rasterDataID:
                        if self.pixelValuesForEdge[rasterDataID*6 + heurID] is None:
                            if self.allowDoubleEdges and (self.graph.vertex(edge.fromVertex()).point(),
                                                          self.graph.vertex(edge.toVertex()).point()) in\
                                    self.spForPointPairs.keys():
                                pixelValues = self.spForPointPairs[self.graph.vertex(edge.fromVertex()).point(),
                                                                   self.graph.vertex(edge.toVertex()).point()]
                            else:
                                pixelValues = aStarObj.getShortestPathWeight(
                                    self.graph.vertex(edge.fromVertex()).point(),
                                    self.graph.vertex(edge.toVertex()).point())
                                if self.allowDoubleEdges:
                                    self.spForPointPairs[(self.graph.vertex(edge.toVertex()).point(),
                                                          self.graph.vertex(edge.fromVertex()).point())] = pixelValues
                            self.pixelValuesForEdge[rasterDataID*6 + heurID] = pixelValues
                        numberOfDiagonals = aStarObj.getNumberOfDiagonals()
                if "," in part:
                    part = part.split("(")[0] + "(" + part.split(",")[1]

                return self.__calculateRasterAnalysis(self.pixelValuesForEdge[rasterDataID*6 + heurID],
                                                      part.split(":sp")[1], rasterDataID, numberOfDiagonals)
            else:
                return self.__calculateRasterAnalysis(self.pointValuesForEdge[rasterDataID], part.split(":")[1])

        for operator in self.operators:
            if operator in part:
                return str(eval(part))

        return str("0")

    def __calculateRasterAnalysis(self, values, analysis, rLayerIndex=0, numberOfDiagonals=None):
        """
        Method is responsible to translate all the raster analysis constructs.

        :type values: List of pixel values
        :type analysis: String defining the type of analysis
        :return translated raster analysis as string usually containing a number
        """
        if "sum" in analysis.lower():
            return str(sum(values))
        elif "mean" in analysis.lower():
            return str(statistics.mean(values))
        elif analysis.lower() == "median":
            return str(statistics.median(values))
        elif "min" in analysis.lower():
            return str(min(values))
        elif "max" in analysis.lower():
            return str(max(values))
        elif "variance" in analysis.lower():
            return str(statistics.variance(values))
        elif analysis == "standdev":
            return str(statistics.stdev(values))
        elif "gradientsum" in analysis.lower():
            f = np.array(values, dtype=float)
            gradient = np.gradient(f)
            return str(np.sum(gradient))
        elif "gradientmin" in analysis.lower():
            f = np.array(values, dtype=float)
            gradient = np.gradient(f)
            return str(np.min(gradient))
        elif "gradientmax" in analysis.lower():
            f = np.array(values, dtype=float)
            gradient = np.gradient(f)
            return str(np.max(gradient))
        elif "ascent" in analysis.lower():
            ascent = 0
            for i in range(len(values)-1):
                if values[i] < values[i+1]:
                    ascent = ascent + (values[i+1] - values[i])
            return str(ascent)
        elif "descent" in analysis.lower():
            descent = 0
            for i in range(len(values)-1):
                if values[i] > values[i+1]:
                    descent = descent + (values[i] - values[i+1])
            return str(descent)
        elif "totalclimb" in analysis.lower():
            totalClimb = 0
            for i in range(len(values)-1):
                totalClimb = totalClimb + abs(values[i] - values[i+1])
            return str(totalClimb)
        # last two types can only occur in if construct
        elif "pixelvalue" in analysis.lower():
            listOfPixelValuesAsString = "pixelValue(" + str(values[0])
            for pValue in values:
                listOfPixelValuesAsString = listOfPixelValuesAsString + "," + str(pValue)
            listOfPixelValuesAsString = listOfPixelValuesAsString + ")"
            return listOfPixelValuesAsString
        elif "percentofvalues" in analysis.lower():
            findPercentage = re.search(r"percentofvalues\([0-9]+\)", analysis.lower())
            findPercentageHelp = findPercentage.group().replace("(", "").replace(")", "")
            percentage = findPercentageHelp.split("percentofvalues")[1]

            listOfPixelValuesAsString = "percentOfValues(" + percentage
            for pValue in values:
                listOfPixelValuesAsString = listOfPixelValuesAsString + "," + str(pValue)

            listOfPixelValuesAsString = listOfPixelValuesAsString + ")"
            return listOfPixelValuesAsString
        elif "euclidean" in analysis.lower():
            diagonalLength = numberOfDiagonals * (math.sqrt(math.pow(self.euclDistPixelNeighbors[rLayerIndex], 2) +
                                                            math.pow(self.euclDistPixelNeighbors[rLayerIndex], 2)))
            nonDiagonalLength = self.euclDistPixelNeighbors[rLayerIndex] * (len(values)-1-numberOfDiagonals)
            shortestPathEucl = diagonalLength + nonDiagonalLength
            return str(shortestPathEucl)
        elif "manhattan" in analysis.lower():
            shortestPathMan = self.manDistPixelNeighbors[rLayerIndex] * len(values)-1
            diagonalLength = numberOfDiagonals * (math.sqrt(math.pow(self.manDistPixelNeighbors[rLayerIndex], 2) +
                                                            math.pow(self.manDistPixelNeighbors[rLayerIndex], 2)))
            nonDiagonalLength = self.manDistPixelNeighbors[rLayerIndex] * (len(values)-1-numberOfDiagonals)
            shortestPathMan = diagonalLength + nonDiagonalLength
            return str(shortestPathMan)
        elif "geodesic" in analysis.lower():
            diagonalLength = numberOfDiagonals * (math.sqrt(math.pow(self.geoDistPixelNeighbors[rLayerIndex], 2) +
                                                            math.pow(self.geoDistPixelNeighbors[rLayerIndex], 2)))
            nonDiagonalLength = self.geoDistPixelNeighbors[rLayerIndex] * (len(values)-1-numberOfDiagonals)
            shortestPathGeo = diagonalLength + nonDiagonalLength
            return str(shortestPathGeo)
        elif "ellipsoidal" in analysis.lower():
            diagonalLength = numberOfDiagonals * (math.sqrt(math.pow(self.ellDistPixelNeighbors[rLayerIndex], 2) +
                                                            math.pow(self.ellDistPixelNeighbors[rLayerIndex], 2)))
            nonDiagonalLength = self.ellDistPixelNeighbors[rLayerIndex] * (len(values)-1-numberOfDiagonals)
            shortestPathEll = diagonalLength + nonDiagonalLength
            return str(shortestPathEll)

    def __createEdgeLayer(self):
        """
        Creates an edge layer for the graph. This is used to call QGIS-Tools which
        require vector layers as attributes

        :return QgsVectorLayer
        """
        graphLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")
        dpEdgeLayer = graphLayerEdges.dataProvider()
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int), ])
        graphLayerEdges.updateFields()

        graphLayerEdges.setCrs(self.vLayer.crs())

        for i in range(self.graph.edgeCount()):
            newFeature = QgsFeature()
            fromVertex = self.graph.vertex(self.graph.edge(i).fromVertex()).point()
            toVertex = self.graph.vertex(self.graph.edge(i).toVertex()).point()
            newFeature.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))
            newFeature.setAttributes([i])
            dpEdgeLayer.addFeature(newFeature)

        return graphLayerEdges

    def __translateRegexSearch(self, costFunction, regex, edgeID, sampledPointsLayers, edgesInPolygonsList,
                               edgesCrossingPolygonsList, constructCall):
        """
        The method iteratively calls the translate method with different parts of the formula.
        The parts are found by checking the formula for the given regular expression that matches one specific formula
        construct.

        :type costFunction: Formula for the edge weight calculation
        :type regex: String defining a regular expression
        :type edgeID: Int defining the edge that gets the translated weight
        :type sampledPointsLayers: List of features
        :type edgesInPolygonList: List of features
        :type edgesCrossingPolygonsList: List of features
        :type constructCall: Boolean
        :return translated formula
        """
        rasterReg = False
        rasterRegexString = r'raster\[[0-9]+\]:(percentOfValues\([0-9]+\)|sp[A-z]+\([0-9]+(,[0-9]+)?\)|[A-z]+)'
        if regex == rasterRegexString:
            rasterReg = True
        regex = re.compile(regex)
        matches = regex.finditer(costFunction)

        matchesTranslationHash = {}

        for res in matches:
            if rasterReg:
                partBeforeAndOr = re.split(r'and|or', res.group())[0]
                translated = self.__translate(partBeforeAndOr, edgeID, sampledPointsLayers, edgesInPolygonsList,
                                              edgesCrossingPolygonsList)
                if not constructCall:
                    self.translatedParts[partBeforeAndOr] = translated
                matchesTranslationHash[partBeforeAndOr] = translated
            else:
                translated = self.__translate(costFunction[res.start():res.end()], edgeID, sampledPointsLayers,
                                              edgesInPolygonsList, edgesCrossingPolygonsList)
                if not constructCall:
                    self.translatedParts[costFunction[res.start():res.end()]] = translated
                matchesTranslationHash[res.group()] = translated

        for key in matchesTranslationHash:
            costFunction = costFunction.replace(key, matchesTranslationHash[key])

        if rasterReg and "raster" in costFunction:
            costFunction = self.__translateRegexSearch(costFunction, rasterRegexString, edgeID, sampledPointsLayers,
                                                       edgesInPolygonsList, edgesCrossingPolygonsList, constructCall)

        return costFunction

    def __fullyTranslatedCheck(self, costFunction):
        """
        Checks if the formula is fully translated, which means it consists only of
        +,-,*,/,(,) and numbers.

        :type costFunction: String
        :return Boolean
        """
        try:
            eval(costFunction)
        except Exception:
            return False
        return True

    def setEdgeCosts(self, costFunction, edgeID=None, costFunctionCount=None):
        """
        Set the cost function for the edge cost calculation.

        :type costFunction: String
        :return graph with set edge costs
        """
        weights = []

        # call QGIS-Tools to get the pixel values for the edges
        # sampledPointsLayers holds the sampled raster values of all edges
        sampledPointsLayers = []
        if len(self.rLayers) > 0:
            edgeLayer = self.__createEdgeLayer()
            for i in range(len(self.rLayers)):
                result = processing.run("qgis:generatepointspixelcentroidsalongline", {"INPUT_RASTER": self.rLayers[i],
                                                                                       "INPUT_VECTOR": edgeLayer,
                                                                                       "OUTPUT": "memory:"})
                result2 = processing.run(
                    "qgis:rastersampling",
                    {"INPUT": result["OUTPUT"],
                     "RASTERCOPY": self.rLayers[i],
                     "COLUMN_PREFIX": "SAMPLE_", "OUTPUT": "memory:"})
                sampledPointsLayers.append(result2["OUTPUT"])

        # initialize all necessary AStarOnRasterData objects
        regex = re.compile(r'raster\[[0-9]\]:sp[A-z]+\([0-9]+,?[0-9]*\)')
        res = regex.findall(costFunction)
        for matchString in res:
            rasterIndex = int(matchString.split("[")[1].split("]")[0])
            heuristicIndexString = matchString.split("(")[1].split(")")[0]

            if "," in heuristicIndexString:
                heuristicIndex = int(heuristicIndexString.split(",")[0])
                # costFunction = costFunction.replace(matchString, matchString.split("(")[0] + "(" +\
                #                                    matchString.split(",")[1])
            else:
                heuristicIndex = int(heuristicIndexString)
            found = False
            for aStarObj in self.aStarAlgObjects:
                if aStarObj.rasterID == rasterIndex and aStarObj.heuristicID == heuristicIndex:
                    found = True
                    break
            if not found:
                self.aStarAlgObjects.append(AStarOnRasterData(self.rLayers[rasterIndex], self.rasterBands[rasterIndex],
                                                              self.vLayer.crs(), heuristicIndex,
                                                              self.createShortestPathView, rasterIndex, heuristicIndex))

        # precalculate the distance between neighboring pixels
        if "spEuclidean" in costFunction or "spManhattan" in costFunction or "spGeodesic" in costFunction or\
           "spEllipsoidal" in costFunction:

            for rLayer in self.rLayers:
                ds = gdal.Open(rLayer.source())
                transform = ds.GetGeoTransform()
                xOrigin = transform[0]
                yOrigin = transform[3]
                pixelWidth = transform[1]
                pixelHeight = -transform[5]

                # get coordinates of top left pixel
                xCoord = xOrigin + (pixelWidth/2)
                yCoord = yOrigin + (pixelHeight/2)
                originalPoint = QgsPointXY(xCoord, yCoord)

                # get coordinates of a neighbor
                xCoordN = xOrigin + (pixelWidth/2)
                yCoordN = (pixelHeight*1) + yOrigin + (pixelHeight/2)
                originalPointN = QgsPointXY(xCoordN, yCoordN)

                # make coordinate transformation from raster crs to the vLayer crs
                tr = QgsCoordinateTransform(rLayer.crs(), self.vLayer.crs(), QgsProject.instance())
                transformedPoint = tr.transform(originalPoint)
                transformedPointN = tr.transform(originalPointN)
                if "spEuclidean" in costFunction:
                    euclDist = math.sqrt(pow(transformedPoint.x()-transformedPointN.x(), 2) +
                                         pow(transformedPoint.y()-transformedPointN.y(), 2))
                    self.euclDistPixelNeighbors.append(euclDist)

                if "spManhattan" in costFunction:
                    manhattenDist = abs(transformedPoint.x()-transformedPointN.x()) +\
                        abs(transformedPoint.y()-transformedPointN.y())
                    self.manDistPixelNeighbors.append(manhattenDist)

                if "spGeodesic" in costFunction:
                    radius = 6371000
                    phi1 = math.radians(transformedPoint.y())
                    phi2 = math.radians(transformedPointN.y())
                    deltaPhi = math.radians(transformedPointN.y()-transformedPoint.y())
                    deltaLambda = math.radians(transformedPointN.x()-transformedPoint.x())
                    a = math.sin(deltaPhi/2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(deltaLambda / 2.0) ** 2
                    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
                    geoDist = radius*c
                    self.geoDistPixelNeighbors.append(geoDist)

                if "spEllipsoidal" in costFunction:
                    distArea = QgsDistanceArea()
                    distArea.setEllipsoid(self.vLayer.crs().ellipsoidAcronym())
                    ellDist = distArea.measureLine(transformedPoint, transformedPointN)
                    if str(ellDist) == "nan":
                        self.ellDistPixelNeighbors.append(0)
                    else:
                        self.ellDistPixelNeighbors.append(ellDist)

        edgesInPolygonsList = []
        edgesCrossingPolygonsList = []
        edgesInPolygons = QgsVectorLayer()
        edgesCrossingPolygons = QgsVectorLayer()

        # check if polygons for cost functions are set
        if len(self.polygons) > 0:
            # check if edgeLayer was already created
            if len(self.rLayers) == 0:
                edgeLayer = self.__createEdgeLayer()
            for polygon in self.polygons:
                if "insidePolygon" in costFunction:
                    polygonResult = processing.run("native:extractbylocation", {"INPUT": edgeLayer, "PREDICATE": 6,
                                                                                "INTERSECT": polygon,
                                                                                "OUTPUT": "memory:"})
                    edgesInPolygons = polygonResult["OUTPUT"]
                    edgesInPolygonsList.append(edgesInPolygons)
                if "crossesPolygon" in costFunction:
                    polygonResult = processing.run("native:extractbylocation", {"INPUT": edgeLayer, "PREDICATE": 7,
                                                                                "INTERSECT": polygon,
                                                                                "OUTPUT": "memory:"})
                    edgesCrossingPolygons = polygonResult["OUTPUT"]
                    edgesCrossingPolygonsList.append(edgesCrossingPolygons)

        costFunction = costFunction.replace(" ", "").replace('"', '')
        costFunctionSave = costFunction

        for i in range(self.graph.edgeCount()):
            if self.task is not None and self.task.isCanceled():
                break

            if self.task is not None:
                newProgress = self.task.progress() + 70/self.graph.edgeCount()
                if newProgress <= 100:
                    self.task.setProgress(round(newProgress, 2))
            self.pointValuesForEdge = [None] * len(self.rLayers)
            self.pixelValuesForEdge = [None] * len(self.rLayers) * 6

            costFunction = costFunctionSave
            self.translatedParts = {}
            # translate different formula parts by searching constructs with regular expressions:
            # Call translate method with each extracted construct and replace in formula

            regexList = [
                r'euclidean', r'manhattan', r'ellipsoidal', r'geodesic', r'field:[A-z]+',
                r'raster\[[0-9]+\]:(percentOfValues\([0-9]+\)|sp[A-z]+\([0-9]+(,[0-9]+)?\)|[A-z]+)',
                r'polygon\[[0-9]?\]:(crossesPolygon|insidePolygon)']

            for regex in regexList:
                costFunction = self.__translateRegexSearch(costFunction, regex, i, sampledPointsLayers,
                                                           edgesInPolygonsList, edgesCrossingPolygonsList, False)

            constructRegexList = [r'math\.[a-z]+%.+?\$', r'rnd\?.+???.+?&', r'if\{.+?;.+?;.+?\}']
            while not self.__fullyTranslatedCheck(costFunction):
                if self.task is not None and self.task.isCanceled():
                    break
                for regex in constructRegexList:
                    costFunction = self.__translateRegexSearch(costFunction, regex, i, sampledPointsLayers,
                                                               edgesInPolygonsList, edgesCrossingPolygonsList, True)

            weights.append(eval(costFunction))

        # append the list
        self.graph.edgeWeights.append(weights)

        if self.createShortestPathView:
            self.shortestPathViewLayers = []
            for aStarObj in self.aStarAlgObjects:
                if aStarObj is not None:
                    fileName = "SPView" + "_" + str(aStarObj.rasterID) + "_" + str(aStarObj.heuristicID)
                    tmpPath = QgsProcessingUtils.generateTempFilename(fileName + ".tif")
                    driver = gdal.GetDriverByName('GTiff')
                    ds = driver.Create(tmpPath, ysize=aStarObj.matrixRowSize, xsize=aStarObj.matrixColSize, bands=3,
                                       eType=gdal.GDT_Byte)
                    ds.GetRasterBand(1).WriteArray(aStarObj.getShortestPathMatrix1())
                    ds.GetRasterBand(2).WriteArray(aStarObj.getShortestPathMatrix2())
                    ds.GetRasterBand(3).WriteArray(aStarObj.getShortestPathMatrix3())
                    ds.GetRasterBand(1).SetColorInterpretation(gdal.GCI_RedBand)
                    ds.GetRasterBand(2).SetColorInterpretation(gdal.GCI_GreenBand)
                    ds.GetRasterBand(3).SetColorInterpretation(gdal.GCI_BlueBand)
                    dsRasterLayer = gdal.Open(self.rLayers[aStarObj.rasterID].source())
                    geot = dsRasterLayer.GetGeoTransform()
                    srs = osr.SpatialReference()
                    if "EPSG" in self.rLayers[aStarObj.rasterID].crs().authid():
                        importID = self.rLayers[aStarObj.rasterID].crs().authid().split(":")[1]
                        srs.ImportFromEPSG(int(importID))
                    elif "ESRI" in self.rLayers[aStarObj.rasterID].crs().authid():
                        importID = self.rLayers[aStarObj.rasterID].crs().authid().split(":")[1]
                        srs.ImportFromESRI(int(importID))
                    ds.SetGeoTransform(geot)
                    ds.SetProjection(srs.ExportToWkt())
                    ds.FlushCache()
                    ds = None
                    viewRasterLayer = QgsRasterLayer(tmpPath, fileName)
                    self.shortestPathViewLayers.append(viewRasterLayer)

        """
        FOR EDITING WITH ADVANCED COSTS:
        else:
            translatedParts = []
            # call function to translate the  parts
            for j in range(len(formulaParts)):
                # check if the current variables was already analyzed
                alreadyDone = False
                foundIndex = 0
                for o in range(j):
                    if formulaParts[o] == formulaParts[j]:
                        alreadyDone = True
                        foundIndex = o
                        break
                # only translate if not already done
                if alreadyDone == False:
                    translatedParts.append(self.__translate(formulaParts[j], edgeID, sampledPointsLayers,
                                           edgesInPolygons, edgesCrossingPolygons))
                else:
                    translatedParts.append(translatedParts[foundIndex])

            # after all variables are translated to numbers if conditions can be evaluated
            for j in range(len(formulaParts)):
                translatedParts[j] = self.__evaluateIfs(str(translatedParts[j]))

            counter = 0
            translatedFormula = costFunction
            for var in variables:
                translatedFormula = translatedFormula.replace(var,str(translatedParts[counter]))
                counter+=1

            self.graph.edgeWeights[costFunctionCount].append(eval(translatedFormula))
        """
        return self.graph
