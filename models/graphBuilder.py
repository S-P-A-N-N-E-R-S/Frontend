#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Dennis Benz, Tim Hartmann
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
import sys

from qgis.core import (QgsVectorLayer, QgsUnitTypes, QgsWkbTypes, QgsPointXY, QgsField, QgsCoordinateReferenceSystem,
                       QgsFeature, QgsGeometry, QgsProject, QgsPoint, QgsPalLayerSettings, QgsTextFormat,
                       QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, QgsMessageLog, Qgis)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtCore import QVariant
from qgis import processing

from .extGraph import ExtGraph
from .formulaCheck import formulaCheck
from .advancedCostCalculator import AdvancedCostCalculator
from .graphLayer import GraphLayer

from ..lib.kdtree import kdtree


class GraphBuilder:
    """
    The GraphBuilder offers the possibility to build different graphs in QGIS. Define the desired graph
    by setting options and layers before calling the makeGraph method.

    Options:
        - connectionType: None, Complete, Nearest neighbor, ClusterComplete, ClusterNN, DistanceNN, LineLayerBased
        - neighborNumber: int
        - distance: (float, QgsUnitTypes::DistanceUnit) (euclidean distance)
        - nnAllowDoubleEdges": True, False
        - clusterNumber": int
        - edgeDirection: Undirected, Directed (do not use undirected with Nearest neighbor connectionType)
        - distanceStrategy: Euclidean, Manhattan, Geodesic, Advanced, None
        - createGraphAsLayers: False, True
        - createRandomGraph: False, True
        - usePolygonsAsForbidden: False, True
        - usePolygonsInCostFunction: False, True
        - useAdditionalPoints: False, True
        - createShortestPathView: False, True
        - randomConnectionNumber: int
        - createFeatureInfos: False, True
        - degreeThreshold: int

    Random options:
        - numberOfVertices: int
        - area: Area of the globe you want the random Graph to be in. Can be one of the specified countries
                or user defined
    """

    def __init__(self):
        """
        Constructor:
        Initial setting for the GraphBuilder. If no additional options or layers are set, a random
        graph with a nearest neighbor connection is generated.
        """
        self.graph = ExtGraph()
        self.vLayer = QgsVectorLayer()
        self.connectionLineLayer = QgsVectorLayer()
        self.rLayers = []
        self.forbiddenAreas = QgsVectorLayer()
        self.additionalPointLayer = QgsVectorLayer()
        self.costFunctions = []
        self.rasterBands = []
        self.polygonsForCostFunction = []
        self.kdTree = None
        self.layerWithClusterIDS = None
        self.shortestPathViewLayers = []
        # is set if graph builder is running as task
        self.task = None

        self.__options = {
            "connectionType": "Nearest neighbor",
            "neighborNumber": 2,
            "distance": (0.3, QgsUnitTypes.DistanceMeters),
            "nnAllowDoubleEdges": False,
            "clusterNumber": 5,
            "edgeDirection": "Directed",
            "distanceStrategy": "Euclidean",
            "useRasterData": False,
            "createGraphAsLayers": True,
            "createRandomGraph": True,
            "usePolygonsAsForbidden": False,
            "usePolygonsInCostFunction": False,
            "useAdditionalPoints": False,
            "createShortestPathView": False,
            "randomConnectionNumber": 100,
            "createFeatureInfos": False,
            "degreeThreshold": 3
        }

        self.__randomOptions = {
            "numberOfVertices": 100,
            "seed": None,
            "area": "Germany"
        }

    def setPolygonsForCostFunction(self, vectorLayer):
        """
        Set polygons for use in the cost function. Call method multiple times
        to set multiple polygon layers.

        :type vectorLayer: QgsVectorLayer containing polygons
        """
        if vectorLayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise TypeError("Not a polygon geometry")

        self.__options["usePolygonsInCostFunction"] = True
        self.polygonsForCostFunction.append(vectorLayer)

    def setForbiddenAreas(self, vectorLayer):
        """
        All edges crossing the polygon will be deleted from the graph.

        :type vectorLayer: QgsVectorLayer containing polygons
        """
        if vectorLayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise TypeError("Not a polygon geometry")

        self.__options["usePolygonsAsForbidden"] = True
        self.forbiddenAreas = vectorLayer

    def setAdditionalPointLayer(self, vectorLayer):
        """
        Additional points to a given line layer. The points will be added in addition to the
        network generated for the line layer and connected to the nearest point.

        :type vectorLayer: QgsVectorLayer containing points
        """
        if vectorLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point geometry")

        self.__options["useAdditionalPoints"] = True
        self.additionalPointLayer = vectorLayer

    def setVectorLayer(self, vectorLayer):
        """
        Set the basis vector layer for the graph creation.

        :type vectorLayer: QgsVectorLayer containing lines or points
        """
        if vectorLayer.geometryType() != QgsWkbTypes.LineGeometry and\
           vectorLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point or line geometry")

        self.__options["createRandomGraph"] = False
        self.vLayer = vectorLayer

    def setRasterLayer(self, rasterLayer, band=1):
        """
        Set raster data to be used in the AdvancedCostCalculator class.

        :type QgsRasterLayer
        """
        self.__options["useRasterData"] = True
        self.rasterBands.append(band)
        self.rLayers.append(rasterLayer)

    def setLineLayer(self, layer):
        if layer.geometryType() != QgsWkbTypes.LineGeometry:
            raise TypeError("Not a line layer")

        self.connectionLineLayer = layer

    def addCostFunction(self, function):
        """
        Set the cost function for an advanced distance strategy. Returns if the
        function has a valid format and the function is set.

        :type function: String
        :return Boolean
        """
        self.__options["distanceStrategy"] = "Advanced"

        syntaxCheckResult = self.syntaxCheck(function, self.vLayer.fields(), len(self.rLayers),
                                             len(self.polygonsForCostFunction))
        if syntaxCheckResult[0] == "No error found":
            function = syntaxCheckResult[1]
            self.costFunctions.append(function)

        return syntaxCheckResult[0]

    @staticmethod
    def syntaxCheck(function, fields, numberOfRasterData, numberOfPolygons):
        # formulaCheck method in FormulaCheck.py file
        return formulaCheck(function, fields, numberOfRasterData, numberOfPolygons)

    def getCostFunction(self, index):
        return self.costFunctions[index]

    def setOption(self, optionType, value):
        if not optionType in self.__options:
            raise KeyError("Option not found")
        self.__options[optionType] = value

    def getOption(self, optionType):
        if not optionType in self.__options:
            raise KeyError("Option not found")
        return self.__options[optionType]

    def setRandomOption(self, optionType, value):
        if not optionType in self.__randomOptions:
            raise KeyError("Option not found")
        self.__randomOptions[optionType] = value

    def __createRandomVertices(self):
        """
        Create random vertices in specified area of the globe.
        CRS is set to EPSG:4326 and the number of vertices can be defined as an option   .
        """
        seed = self.__randomOptions["seed"]
        if seed is None:
            random.seed()  # reset initial seed
            seed = random.randrange(sys.maxsize)  # create seed because not possible to get seed from random
        random.seed(seed)
        self.graph.setRandomSeed(seed)

        for _ in range(self.__randomOptions["numberOfVertices"]):
            if self.task is not None and self.task.isCanceled():
                break
            if self.task is not None:
                self.task.setProgress(self.task.progress() + 10/self.__randomOptions["numberOfVertices"])
            if self.__randomOptions["area"] == "Germany":
                self.graph.addVertex(QgsPointXY(random.uniform(6.803, 13.480), random.uniform(47.420, 55.000)))
            elif self.__randomOptions["area"] == "France":
                self.graph.addVertex(QgsPointXY(random.uniform(-3.163, 6.426), random.uniform(43.830, 50.055)))
            elif self.__randomOptions["area"] == "Osnabrueck":
                self.graph.addVertex(QgsPointXY(random.uniform(8.01050, 8.09776), random.uniform(52.24311, 52.30802)))
            elif self.__randomOptions["area"] == "United States":
                self.graph.addVertex(QgsPointXY(random.uniform(-122.892, -74.157), random.uniform(33.725, 46.052)))
            elif self.__randomOptions["area"] == "Rome":
                self.graph.addVertex(QgsPointXY(random.uniform(12.40009, 12.57946), random.uniform(41.83013, 41.97905)))
            elif self.__randomOptions["area"] == "Australia":
                self.graph.addVertex(QgsPointXY(random.uniform(115.157, 150.167), random.uniform(-37.211, -14.210)))
            elif isinstance(self.__randomOptions["area"], tuple):
                rectangleExtent, _ = self.__randomOptions["area"]
                self.graph.addVertex(QgsPointXY(random.uniform(rectangleExtent.xMinimum(), rectangleExtent.xMaximum()),
                                                random.uniform(rectangleExtent.yMinimum(), rectangleExtent.yMaximum())))

    def __createVerticesForPoints(self):
        """
        Method creates a new vertex in the graph for every point inside
        the given vectorLayer.
        """
        for feat in self.vLayer.getFeatures():
            if self.task is not None and self.task.isCanceled():
                break
            if self.task is not None:
                self.task.setProgress(self.task.progress() + 10/self.vLayer.featureCount())
            geom = feat.geometry()

            if self.__options["distanceStrategy"] == "Advanced":
                self.graph.pointsToFeatureHash[geom.asPoint().toString()] = feat
            self.graph.addVertex(geom.asPoint())

    def __createLineBasedConnections(self):
        # initialize buckets: every bucket stands for one line segment and contains all assigned points
        buckets = {}
        # dictionary for the graph vertices containing a list of dictionaries
        attributeDictsForVertices = {}
        dictsForOrigVertices = {}

        # split up the polylines into individual line segments
        result = processing.run("native:explodelines", {"INPUT": self.connectionLineLayer, "OUTPUT": "memory:"})
        explodedLines = result["OUTPUT"]

        originalLineLayerFields = []
        for field in self.connectionLineLayer.fields():
            originalLineLayerFields.append(field.name())

        # add an id field to the exploded line layer for later identification
        explodedLinesFieldFetch = {}
        dp = explodedLines.dataProvider()
        dp.addAttributes([QgsField("newUniqueID", QVariant.Int)])
        explodedLines.updateFields()
        placeOfID = len(explodedLines.fields())-1
        explodedLines.startEditing()
        for feat in explodedLines.getFeatures():
            theID = feat.id()
            # bucket init
            buckets[theID] = []
            attrValue = {placeOfID: theID}
            dp.changeAttributeValues({theID: attrValue})
            explodedLinesFieldFetch[theID] = {}
            for field in originalLineLayerFields:
                explodedLinesFieldFetch[theID][field] = feat[field]
        explodedLines.commitChanges()

        if self.task is not None:
            self.task.setProgress(self.task.progress() + 5)

        # find for each point the line segment or segments the point is closest to
        if self.__options["distance"][0] == 0:
            result = processing.run("native:joinbynearest", {"INPUT": self.vLayer, "INPUT_2": explodedLines,
                                                             "PREFIX": "new_", "OUTPUT": "memory:"})
        else:
            if self.__options["createRandomGraph"] == True:
                crsUnitRead = QgsCoordinateReferenceSystem("EPSG:4326")
            else:
                crsUnitRead = self.vLayer.crs()
            distConverted = self.__options["distance"][0] *\
                QgsUnitTypes.fromUnitToUnitFactor(self.__options["distance"][1], crsUnitRead.mapUnits())
            result = processing.run("native:joinbynearest", {"INPUT": self.vLayer, "INPUT_2": explodedLines,
                                                             "PREFIX": "new_",
                                                             "NEIGHBORS": explodedLines.featureCount(),
                                                             "MAX_DISTANCE": distConverted,
                                                             "OUTPUT": "memory:"})
        joinedLayer = result["OUTPUT"]

        if self.task is not None:
            self.task.setProgress(self.task.progress() + 5)

        # fill buckets
        graphVertexCounter = -1
        for currFeat in joinedLayer.getFeatures():
            if self.task is not None and self.task.isCanceled():
                break
            if currFeat["n"] == 1 or currFeat["n"] == 0 or currFeat["n"] == None:
                # it is possible that there are multiple matches for one vertex
                graphVertexCounter += 1
            if currFeat["n"] is None:
                continue
            # uniqueID gives matching to line segment
            buckets[currFeat["new_newUniqueID"]].append((graphVertexCounter, currFeat))

            if self.__options["createFeatureInfos"]:
                # assume that every point just has one nearest edge found by the joinbynearest operation
                attributeDictsForVertices[graphVertexCounter] = [explodedLinesFieldFetch[currFeat["new_newUniqueID"]]]
                dictsForOrigVertices[graphVertexCounter] = [explodedLinesFieldFetch[currFeat["new_newUniqueID"]]]

        # create edges between the vertices in one bucket
        for key, bucket in buckets.items():
            if len(bucket) == 2:
                for i in range(len(bucket)-1):
                    if self.__options["createFeatureInfos"]:
                        feat1 = attributeDictsForVertices[bucket[i][0]][0]
                        feat2 = attributeDictsForVertices[bucket[i+1][0]][0]
                        if feat1 == feat2:
                            toAdd = [feat1]
                        else:
                            # can happen because of the assumption
                            toAdd = [feat1, feat2]
                    else:
                        toAdd = None
                    self.graph.addEdge(bucket[i][0], bucket[i+1][0], feat=toAdd)
            # if there are more then two points, the features have to be sorted by their distance to the
            # start point of the line segement
            elif len(bucket) > 2:
                startPoint = explodedLines.getFeature(key).geometry().asPolyline()[0]
                for i in range(len(bucket)):
                    feat = bucket[i][1]
                    geom = feat.geometry()
                    point = geom.asPoint()
                    dist = math.sqrt(pow(startPoint.x()-point.x(), 2) + pow(startPoint.y()-point.y(), 2))
                    bucket[i] = bucket[i] + (dist,)

                sortedList = sorted(bucket, key=lambda tri: tri[2])
                for index in range(len(sortedList)-1):
                    if self.__options["createFeatureInfos"]:
                        feat1 = attributeDictsForVertices[sortedList[index][0]][0]
                        feat2 = attributeDictsForVertices[sortedList[index+1][0]][0]
                        if feat1 == feat2:
                            toAdd = [feat1]
                        else:
                            # can happen because of the assumption
                            toAdd = [feat1, feat2]
                    else:
                        toAdd = None
                    self.graph.addEdge(sortedList[index][0], sortedList[index+1][0], feat=toAdd)

        if self.task is not None:
            self.task.setProgress(self.task.progress() + 5)

        originalNumberOfVertices = self.graph.vertexCount()

        # build help graph for the exploded line layer
        gbHelp = GraphBuilder()
        gbHelp.setVectorLayer(explodedLines)
        gbHelp.setOption("createGraphAsLayers", False)
        gbHelp.setOption("edgeDirection", "Undirected")
        gbHelp.makeGraph()
        helpGraph = gbHelp.getGraph()

        # add additional points for each line segment which does not have a point associated
        newlyAddedVertexIds = []
        for edgeID in helpGraph.edges():
            edge = helpGraph.edge(edgeID)
            if len(buckets[edge.feature.id()]) == 0:
                vFrom = helpGraph.vertex(edge.fromVertex())
                vTo = helpGraph.vertex(edge.toVertex())
                newID = self.graph.addVertex(QgsPointXY((vFrom.point().x() + vTo.point().x())/2,
                                                        (vFrom.point().y() + vTo.point().y())/2))
                buckets[edge.feature.id()].append((newID, None))
                newlyAddedVertexIds.append(newID)
                if self.__options["createFeatureInfos"]:
                    # get field information of the polylines for the new points too
                    attributeDictsForVertices[newID] = [explodedLinesFieldFetch[edge.feature.id()]]

        # do deep first searches until every vertex in the help graph is visited
        visited = [False] * helpGraph.vertexCount()
        visitedCounter = 0
        for vertexID in helpGraph.vertices():
            if self.task is not None:
                self.task.setProgress(self.task.progress() + 15/helpGraph.vertexCount())
            # start at a degree 1 node because otherwise some connections might not be made
            if not visited[vertexID] and helpGraph.vertex(vertexID).degree() == 1:
                visitedCounter += self.__dfs(vertexID, helpGraph, visited, buckets, attributeDictsForVertices)

        # control loops in case there are cycles
        if visitedCounter != helpGraph.vertexCount():
            for vertexID in helpGraph.vertices():
                if self.task is not None:
                    self.task.setProgress(self.task.progress() + 15/helpGraph.vertexCount())
                if not visited[vertexID]:
                    self.__dfs(vertexID, helpGraph, visited, buckets, attributeDictsForVertices)

        # delete help nodes and insert correct edges
        for vertexID in reversed(newlyAddedVertexIds):
            if self.task is not None:
                self.task.setProgress(self.task.progress() + 60/len(newlyAddedVertexIds))
            if self.task is not None and self.task.isCanceled():
                break

            v = self.graph.vertex(vertexID)
            # get all neighbors of v
            connectedVertices = []
            for edgeId in v.incomingEdges():
                neighbor = self.graph.edge(edgeId).opposite(vertexID)
                connectedVertices.append(neighbor)
            for edgeId in v.outgoingEdges():
                neighbor = self.graph.edge(edgeId).opposite(vertexID)
                connectedVertices.append(neighbor)

            if self.__options["createFeatureInfos"]:
                for neighbor in connectedVertices:
                    if neighbor < originalNumberOfVertices:
                        attributeDictsForVertices[neighbor] = dictsForOrigVertices[neighbor]
                    else:
                        for lineInfos in attributeDictsForVertices[vertexID]:
                            attributeDictsForVertices[neighbor].append(lineInfos)

            # in some sets the amount of neighbors can be very high so exclude this cases
            if len(connectedVertices) <= self.__options["degreeThreshold"]:
                # add edges between all neighbor pairs
                for i in range(len(connectedVertices)-1):
                    for j in range(i+1, len(connectedVertices)):
                        if self.task is not None and self.task.isCanceled():
                            break
                        if connectedVertices[i] != connectedVertices[j] and\
                           self.graph.hasEdge(connectedVertices[i], connectedVertices[j]) == -1:
                            if self.__options["createFeatureInfos"]:
                                combined = attributeDictsForVertices[connectedVertices[i]] +\
                                    attributeDictsForVertices[connectedVertices[j]]
                                # remove duplicates
                                toAdd = {frozenset(item.items()): item for item in combined}.values()
                            else:
                                toAdd = None

                            self.graph.addEdge(connectedVertices[i], connectedVertices[j], feat=toAdd)

            self.graph.deleteVertex(vertexID)
            # remove dicts to safe memory
            if self.__options["createFeatureInfos"]:
                del attributeDictsForVertices[vertexID]

    def __dfs(self, vertexId, graph, visited, buckets, attributeDictsForVertices):
        stack = []
        visitedCounter = 0
        stack.append(vertexId)
        # this dictionary stores for a vertex the edge it was last visited by
        usedEdges = {}
        while len(stack) != 0:
            v = stack.pop()
            if not visited[v]:
                visited[v] = True
                visitedCounter += 1
                neighborEdges = []
                neighbors = []
                for edgeId in graph.vertex(v).incomingEdges():
                    usedEdges[graph.edge(edgeId).opposite(v)] = edgeId
                    neighborEdges.append(edgeId)
                    neighbors.append(graph.edge(edgeId).opposite(v))
                for edgeId in graph.vertex(v).outgoingEdges():
                    usedEdges[graph.edge(edgeId).opposite(v)] = edgeId
                    neighborEdges.append(edgeId)
                    neighbors.append(graph.edge(edgeId).opposite(v))
                for neighbor in neighbors:
                    stack.append(neighbor)
                if self.task is not None and self.task.isCanceled():
                    break
                # make necessary connections
                for neighborEdge in neighborEdges:
                    # the first start node is not in usedEdges
                    if v in usedEdges and\
                       graph.edge(neighborEdge).feature.id() != graph.edge(usedEdges[v]).feature.id():
                        # since multiple points can be associated with the neighbor lines
                        # find and connect only the nearest paints
                        nearestV1 = None
                        nearestV2 = None
                        minDist = sys.maxsize
                        # connect to nearest
                        for entry in buckets[graph.edge(neighborEdge).feature.id()]:
                            if self.task is not None and self.task.isCanceled():
                                break
                            thePoint = self.graph.vertex(entry[0]).point()
                            for entry2 in buckets[graph.edge(usedEdges[v]).feature.id()]:
                                thePoint2 = self.graph.vertex(entry2[0]).point()
                                dist = math.sqrt(
                                    pow(thePoint.x() - thePoint2.x(),
                                        2) + pow(thePoint.y() - thePoint2.y(),
                                                 2))
                                if dist < minDist:
                                    minDist = dist
                                    nearestV1 = entry[0]
                                    nearestV2 = entry2[0]
                        if nearestV1 != nearestV2:
                            if self.__options["createFeatureInfos"]:
                                feat1 = attributeDictsForVertices[nearestV1][0]
                                feat2 = attributeDictsForVertices[nearestV2][0]
                                if feat1 == feat2:
                                    toAdd = [feat1]
                                else:
                                    toAdd = [feat1, feat2]
                            else:
                                toAdd = None

                            if self.graph.hasEdge(nearestV1, nearestV2) == -1:
                                self.graph.addEdge(nearestV1, nearestV2, feat=toAdd)

        return visitedCounter

    def __createComplete(self):
        """
        Create an edge for every pair of vertices
        """
        for i in range(self.graph.vertexCount()-1):
            if self.task is not None and self.task.isCanceled():
                return
            if self.task is not None:
                if self.__options["distanceStrategy"] == "Advanced":
                    newProgress = self.task.progress() + 20/self.graph.vertexCount()
                else:
                    newProgress = self.task.progress() + 90/self.graph.vertexCount()
                if newProgress <= 100:
                    self.task.setProgress(newProgress)
            for j in range(i+1, self.graph.vertexCount()):
                if self.__options["distanceStrategy"] == "Advanced":
                    self.graph.featureMatchings.append(self.graph.mVertices[j].mCoordinates)
                self.graph.addEdge(i, j)
                if self.__options["edgeDirection"] == "Directed":
                    self.graph.addEdge(j, i)

    def __createRandomConnections(self):
        notUsedVertexPairs = []
        for i in range(self.graph.vertexCount()-1):
            if self.__options["distanceStrategy"] == "Advanced":
                newProgress = self.task.progress() + 20/self.graph.vertexCount()
            else:
                newProgress = self.task.progress() + 90/self.graph.vertexCount()
            if newProgress <= 100:
                self.task.setProgress(newProgress)

            for j in range(i+1, self.graph.vertexCount()):
                if self.__options["edgeDirection"] == "Directed":
                    notUsedVertexPairs.append((i, j))
                    notUsedVertexPairs.append((j, i))
                else:
                    notUsedVertexPairs.append((i, j))

        for i in range(self.__options["randomConnectionNumber"]):
            if len(notUsedVertexPairs) == 0:
                break
            pairID = random.randint(0, len(notUsedVertexPairs)-1)
            p1 = notUsedVertexPairs[pairID][0]
            p2 = notUsedVertexPairs[pairID][1]
            self.graph.addEdge(p1, p2)
            del notUsedVertexPairs[pairID]

    def __createNearestNeighbor(self):
        """
        The edges for the options DistanceNN and Nearest neighbor are created inside
        this method. A KD-Tree is used to find the nearest points.
        """
        points = []
        for i in range(self.graph.vertexCount()):
            point = self.graph.vertex(i).point()
            points.append([point.x(), point.y(), i])

        self.kdTree = kdtree.create(points)

        if self.__options["connectionType"] == "DistanceNN":
            if self.__options["createRandomGraph"] == True:
                crsUnitRead = QgsCoordinateReferenceSystem("EPSG:4326")
            else:
                crsUnitRead = self.vLayer.crs()

        for i in range(self.graph.vertexCount()):
            if self.task is not None and self.task.isCanceled():
                return
            if self.task is not None:
                if self.__options["distanceStrategy"] == "Advanced":
                    _newProgress = self.task.progress() + 20/self.graph.vertexCount()
                else:
                    _newProgress = self.task.progress() + 90/self.graph.vertexCount()

            point = self.graph.vertex(i).point()

            if self.__options["connectionType"] == "Nearest neighbor":
                if self.__options["edgeDirection"] == "Directed":
                    listOfNeighbors = self.kdTree.search_knn(
                        [point.x(), point.y(), i], self.__options["neighborNumber"]+1)
                else:
                    if len(self.graph.mVertices[i].mIncomingEdges) < self.__options["neighborNumber"]:
                        listOfNeighbors = self.kdTree.search_knn([point.x(), point.y(), i],
                                                                 self.__options["neighborNumber"]+1 -
                                                                 len(self.graph.mVertices[i].mIncomingEdges))
                    else:
                        listOfNeighbors = []
            elif self.__options["connectionType"] == "DistanceNN":
                # make distance transformation
                transDistValue = self.__options["distance"][0] *\
                    QgsUnitTypes.fromUnitToUnitFactor(self.__options["distance"][1],
                                                      crsUnitRead.mapUnits())
                listOfNeighbors = self.kdTree.search_nn_dist([point.x(), point.y(), i], pow(transDistValue, 2))
            for neighbor in listOfNeighbors:
                if self.__options["connectionType"] == "Nearest neighbor":
                    neighborPoint = neighbor[0].data
                elif self.__options["connectionType"] == "DistanceNN":
                    neighborPoint = neighbor
                if i != neighborPoint[2]:
                    self.graph.addEdge(i, neighborPoint[2])

                if self.__options["distanceStrategy"] == "Advanced":
                    self.graph.featureMatchings.append(self.graph.mVertices[neighborPoint[2]].mCoordinates)

            if (self.__options["connectionType"] == "Nearest neighbor" or
                    self.__options["connectionType"] == "DistanceNN") and self.__options["nnAllowDoubleEdges"] == False:
                self.kdTree = self.kdTree.remove([point.x(), point.y(), i])

    def __createCluster(self):
        """
        The edges for the options ClusterNN and ClusterComplete are created inside
        this method. A KD-Tree is used to find the nearest points.
        """
        # if a random graph was created the vLayer has to be set manually
        if self.__options["createRandomGraph"] == True:

            self.vLayer = QgsVectorLayer("Point", "TempVertexLayer", "memory")
            dpVerticeLayer = self.vLayer.dataProvider()

            for i in range(self.graph.vertexCount()):
                newFeature = QgsFeature()
                newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))
                dpVerticeLayer.addFeature(newFeature)

        # change so you only go throw the features ones and store in 2d array
        result = processing.run("qgis:kmeansclustering", {"INPUT": self.vLayer,
                                                          "CLUSTERS": self.__options["clusterNumber"],
                                                          "OUTPUT": "memory:"})
        self.layerWithClusterIDS = result["OUTPUT"]

        for cluster in range(self.__options["clusterNumber"]):
            allPointsInCluster = []
            featureCounter = 0
            for feature in self.layerWithClusterIDS.getFeatures():
                if feature["CLUSTER_ID"] == cluster:
                    allPointsInCluster.append(featureCounter)
                featureCounter += 1

            if self.__options["connectionType"] == "ClusterNN":
                points = []
                for pointInCluster in allPointsInCluster:
                    vertex = self.graph.vertex(pointInCluster)
                    vertex.setClusterID(cluster)
                    point = vertex.point()
                    points.append([point.x(), point.y(), pointInCluster])

                # build kd tree
                self.kdTree = kdtree.create(points)
                for pointInCluster in allPointsInCluster:
                    if self.task is not None:
                        if self.__options["distanceStrategy"] == "Advanced":
                            _newProgress = self.task.progress() + 20/self.graph.vertexCount()
                        else:
                            _newProgress = self.task.progress() + 90/self.graph.vertexCount()

                    if self.task is not None and self.task.isCanceled():
                        return
                    if len(allPointsInCluster) > 1:
                        vertex = self.graph.vertex(pointInCluster).point()

                        if self.__options["edgeDirection"] == "Directed":
                            nearestPoints = self.kdTree.search_knn([vertex.x(), vertex.y(),
                                                                    pointInCluster],
                                                                   self.__options["neighborNumber"]+1)
                        else:
                            nearestPoints = []
                            if len(self.graph.vertex(pointInCluster).mIncomingEdges) <\
                               self.__options["neighborNumber"]:
                                nearestPoints = self.kdTree.search_knn(
                                    [vertex.x(),
                                     vertex.y(),
                                     pointInCluster],
                                    self.__options["neighborNumber"] + 1 -
                                    (len(self.graph.vertex(pointInCluster).mIncomingEdges)))

                        for t in range(1, len(nearestPoints)):
                            neighborPoint = nearestPoints[t][0].data

                            self.graph.addEdge(pointInCluster, neighborPoint[2])

                            if self.__options["distanceStrategy"] == "Advanced":
                                self.graph.featureMatchings.append(self.graph.mVertices[neighborPoint[2]].mCoordinates)

                        if self.__options["nnAllowDoubleEdges"] == False:
                            self.kdTree = self.kdTree.remove([vertex.x(), vertex.y(), pointInCluster])

            elif self.__options["connectionType"] == "ClusterComplete":
                for i in range(len(allPointsInCluster)-1):
                    self.graph.vertex(allPointsInCluster[i]).setClusterID(cluster)
                    if self.task is not None and self.task.isCanceled():
                        return
                    if self.task is not None:
                        if self.__options["distanceStrategy"] == "Advanced":
                            _newProgress = self.task.progress() + 20/self.graph.vertexCount()
                        else:
                            _newProgress = self.task.progress() + 90/self.graph.vertexCount()
                    for j in range(i+1, len(allPointsInCluster)):
                        self.graph.addEdge(allPointsInCluster[i], allPointsInCluster[j])
                        if self.__options["edgeDirection"] == "Directed":
                            self.graph.addEdge(allPointsInCluster[j], allPointsInCluster[i],)
                        if self.__options["distanceStrategy"] == "Advanced":
                            self.graph.featureMatchings.append(self.graph.mVertices[allPointsInCluster[j]].mCoordinates)

    def __createGraphForLineGeometry(self):
        """
        Method is called if the input consists of lines. Every start and end of
        very edge is a vertex in the graph and an edge is added between them.
        """
        # get all the lines and set end nodes as vertices and connections as edges
        vertexHash = {}
        lastVertexID = None
        for feature in self.vLayer.getFeatures():
            if feature.id() == 1 and "cost_0" in feature.fields().names():
                self.advancedImport = True
                self.importedCostFunctions = []
                for name in feature.fields().names():
                    # get all cost functions to be parsed
                    if "cost_" in name:
                        self.importedCostFunctions.append(name)

            if self.task is not None:
                if self.__options["distanceStrategy"] == "Advanced":
                    newProgress = self.task.progress() + 30/self.vLayer.featureCount()
                else:
                    newProgress = self.task.progress() + 100/self.vLayer.featureCount()
                if newProgress <= 100:
                    self.task.setProgress(newProgress)

            if self.task is not None and self.task.isCanceled():
                return
            geom = feature.geometry()
            if QgsWkbTypes.isMultiType(geom.wkbType()):
                for part in geom.asMultiPolyline():
                    for i in range(len(part)):
                        if part[i].toString() in vertexHash:
                            searchVertex = vertexHash[part[i].toString()]
                            if i != 0:
                                self.graph.addEdge(lastVertexID, searchVertex, feat=feature)
                                if self.__options["distanceStrategy"] == "Advanced":
                                    self.graph.featureMatchings.append(feature)
                            lastVertexID = searchVertex
                        else:
                            addedID = self.graph.addVertex(part[i])
                            vertexHash[part[i].toString()] = addedID
                            if i != 0:
                                self.graph.addEdge(lastVertexID, addedID, feat=feature)
                                self.graph.featureMatchings.append(feature)
                            lastVertexID = addedID
            else:
                vertices = geom.asPolyline()
                for i in range(len(vertices)-1):
                    startVertex = vertices[i]
                    endVertex = vertices[i+1]
                    if startVertex.toString() in vertexHash and endVertex.toString() in vertexHash:
                        searchVertex1 = vertexHash[startVertex.toString()]
                        searchVertex2 = vertexHash[endVertex.toString()]
                        self.graph.addEdge(searchVertex1, searchVertex2, feat=feature)

                    elif startVertex.toString() in vertexHash:
                        searchVertex = vertexHash[startVertex.toString()]
                        id2 = self.graph.addVertex(endVertex)
                        vertexHash[endVertex.toString()] = id2
                        self.graph.addEdge(searchVertex, id2, feat=feature)

                    elif endVertex.toString() in vertexHash:
                        searchVertex = vertexHash[endVertex.toString()]
                        id1 = self.graph.addVertex(startVertex)
                        vertexHash[startVertex.toString()] = id1
                        self.graph.addEdge(id1, searchVertex, feat=feature)

                    else:
                        id1 = self.graph.addVertex(startVertex)
                        id2 = self.graph.addVertex(endVertex)
                        vertexHash[startVertex.toString()] = id1
                        vertexHash[endVertex.toString()] = id2
                        self.graph.addEdge(id1, id2, feat=feature)
                        if self.__options["distanceStrategy"] == "Advanced":
                            self.graph.featureMatchings.append(feature)

        # add points and connection to network if additional points are given
        # use kd tree to get the nearest point
        if self.__options["useAdditionalPoints"] == True:
            points = []
            for i in range(self.graph.vertexCount()):
                point = self.graph.vertex(i).point()
                points.append([point.x(), point.y(), i])

            # build kd tree
            self.kdTree = kdtree.create(points)
            counter = 0
            for feature in self.additionalPointLayer.getFeatures():
                if self.task is not None and self.task.isCanceled():
                    return
                counter += 1
                geom = feature.geometry()
                pointID = self.graph.addVertex(geom.asPoint())

                nearestPointID = self.kdTree.search_knn([self.graph.vertex(pointID).point().x(),
                                                         self.graph.vertex(pointID).point().y(), counter],
                                                        2)[0][0].data[2]
                self.graph.addEdge(pointID, nearestPointID)

    def __importAdvancedCosts(self):
        self.graph.setDistanceStrategy("Advanced")
        for feature in self.vLayer.getFeatures():
            for name in self.importedCostFunctions:
                cost = feature.attribute(name)
                functionIndex = name.split("_")[1]
                if functionIndex.isnumeric() and isinstance(cost, float):
                    # feature.id() - 1 since feature.id() starts at 1
                    self.graph.setCostOfEdge(feature.id() - 1, int(functionIndex), cost)

    def __removeIntersectingEdges(self):
        """
        Method is called if polygons as forbidden areas are given. All the intersecting edges
        get deleted from the graph.
        """
        # create the current edge layer
        currentEdges = self.createEdgeLayer(False, True)
        # call QGIS tool to extract all the edges which cross the polygon
        result1 = processing.run("native:extractbylocation", {"INPUT": currentEdges, "PREDICATE": 2,
                                                              "INTERSECT": self.forbiddenAreas,
                                                              "OUTPUT": "memory:"})
        layerWithDelEdges = result1["OUTPUT"]

        # copy the result of the QGIS tool into a new graph
        newGraph = ExtGraph()
        for feature in layerWithDelEdges.getFeatures():
            if self.task is not None and self.task.isCanceled():
                return
            geom = feature.geometry()

            vertices = geom.asPolyline()
            for i in range(len(vertices)-1):
                startVertex = vertices[i]
                endVertex = vertices[i+1]
                id1 = newGraph.addVertex(startVertex)
                id2 = newGraph.addVertex(endVertex)
                newGraph.addEdge(id1, id2)

        newGraph.setDistanceStrategy(self.graph.distanceStrategy)
        self.graph = newGraph

    def createVertexLayer(self, addToCanvas):
        """
        Method creates a QgsVectorLayer containing points. The points are the vertices of the graph.

        :type addToCanvas: Boolean
        :return QgsVectorLayer
        """
        if self.task is not None and self.task.isCanceled():
            return
        graphLayerVertices = QgsVectorLayer("Point", "GraphVertices", "memory")
        dpVerticeLayer = graphLayerVertices.dataProvider()
        dpVerticeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("X", QVariant.Double),
                                      QgsField("Y", QVariant.Double)])
        graphLayerVertices.updateFields()

        if self.__options["createRandomGraph"] == False:
            graphLayerVertices.setCrs(self.vLayer.crs())
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayerVertices.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayerVertices.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        # add the vertices and edges to the layers
        for i in range(self.graph.vertexCount()):
            if self.task is not None and self.task.isCanceled():
                return
            newFeature = QgsFeature()
            newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))
            newFeature.setAttributes([i, self.graph.vertex(i).point().x(), self.graph.vertex(i).point().y()])
            dpVerticeLayer.addFeature(newFeature)

        if addToCanvas == True:
            QgsProject.instance().addMapLayer(graphLayerVertices)

        return graphLayerVertices

    def createEdgeLayer(self, addToCanvas, skipEdgeCosts=False):
        """
        Method creates a QgsVectorLayer containing lines. The lines are the edges of the graph. The weights are
        visible by creating labels.

        :type addToCanvas: Boolean
        :return QgsVectorLayer
        """
        if self.task is not None and self.task.isCanceled():
            return
        graphLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")
        dpEdgeLayer = graphLayerEdges.dataProvider()
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("fromVertex", QVariant.Double),
                                   QgsField("toVertex", QVariant.Double), QgsField("weight", QVariant.Double)])
        graphLayerEdges.updateFields()

        if self.__options["createRandomGraph"] == False:
            graphLayerEdges.setCrs(self.vLayer.crs())
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayerEdges.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayerEdges.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        for i in self.graph.edges():
            if self.task is not None and self.task.isCanceled():
                return
            newFeature = QgsFeature()
            fromVertex = self.graph.vertex(self.graph.edge(i).fromVertex()).point()
            toVertex = self.graph.vertex(self.graph.edge(i).toVertex()).point()
            newFeature.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))
            if skipEdgeCosts == True:
                newFeature.setAttributes([i, self.graph.edge(i).fromVertex(), self.graph.edge(i).toVertex(), 0])
            else:
                newFeature.setAttributes([i, self.graph.edge(i).fromVertex(), self.graph.edge(i).toVertex(),
                                          self.graph.costOfEdge(i)])

            dpEdgeLayer.addFeature(newFeature)

        if addToCanvas == True:
            layerSettings = QgsPalLayerSettings()
            textFormat = QgsTextFormat()

            textFormat.setFont(QFont("Arial", 12))
            textFormat.setSize(12)

            bufferSettings = QgsTextBufferSettings()
            bufferSettings.setEnabled(True)
            bufferSettings.setSize(0.1)
            bufferSettings.setColor(QColor("black"))

            textFormat.setBuffer(bufferSettings)
            layerSettings.setFormat(textFormat)

            layerSettings.fieldName = "weight"
            layerSettings.placement = 2

            layerSettings.enabled = True

            layerSettings = QgsVectorLayerSimpleLabeling(layerSettings)
            graphLayerEdges.setLabelsEnabled(True)
            graphLayerEdges.setLabeling(layerSettings)
            graphLayerEdges.triggerRepaint()
            QgsProject.instance().addMapLayer(graphLayerEdges)

        # make sure output is valid
        result = processing.run("qgis:checkvalidity", {"INPUT_LAYER": graphLayerEdges, "METHOD": 1,
                                                       "VALID_OUTPUT": "memory:"})
        graphLayerEdges = result["VALID_OUTPUT"]

        return graphLayerEdges

    def createGraphLayer(self, addToCanvas):
        """
        Create graph layer from created graph
        :type addToCanvas: Boolean
        :return GraphLayer
        """
        graphLayer = GraphLayer()

        if self.__options["createRandomGraph"] == False:
            graphLayer.setCrs(self.vLayer.crs())
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayer.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        graphLayer.setGraph(self.graph)

        if addToCanvas == True:
            QgsProject.instance().addMapLayer(graphLayer)

        return graphLayer

    def getNearestVertex(self, vertexIndex):
        vertex = self.graph.vertex(vertexIndex).point()
        currentVertex = self.graph.vertex(0).point()
        shortestDist = math.sqrt(pow(vertex.x()-currentVertex.x(), 2) + pow(vertex.y()-currentVertex.y(), 2))
        shortestIndex = []
        for v in range(self.graph.vertexCount()):
            if v != vertexIndex:
                currentVertex = self.graph.vertex(v).point()
                currentDist = math.sqrt(pow(vertex.x()-currentVertex.x(), 2) + pow(vertex.y()-currentVertex.y(), 2))
                if currentDist < shortestDist:
                    shortestDist = currentDist
                    shortestIndex = v

        return shortestIndex

    def addVertices(self, vertexLayer):
        """
        Add multiple points by using a vectorLayer

        :type vertexLayer: QgsVectorLayer containing points
        """
        if self.vLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point geometry")
        for feat in vertexLayer.getFeatures():
            geom = feat.geometry()
            self.graph.addVertexWithEdges([geom.asPoint().x(), geom.asPoint().y()])

    def getGraph(self):
        return self.graph

    def setGraph(self, graph):
        self.graph = graph

    def makeGraph(self):
        """
        If this method is called the creation of the graph starts. The set options are read and
        methods are called accordingly.

        :return ExtGraph
        """
        self.graph = ExtGraph()
        if not self.__options["createRandomGraph"]:
            self.graph.setVectorLayer(self.vLayer)
        if self.__options["connectionType"] == "LineLayerBased":
            self.graph.setLineLayerForConnection(self.connectionLineLayer)

        # set distance strategy
        self.graph.setDistanceStrategy(self.__options["distanceStrategy"])
        self.graph.setConnectionType(self.__options["connectionType"])
        self.graph.setGraphBuilderInformation(self.__options["neighborNumber"], self.__options["edgeDirection"],
                                              self.__options["clusterNumber"], self.__options["nnAllowDoubleEdges"],
                                              self.__options["distance"])

        if self.__options["createRandomGraph"] == True:
            self.__createRandomVertices()
        else:
            # self.graph.crs = self.vLayer.crs()
            if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                self.__createVerticesForPoints()
            self.graph.updateCrs(self.vLayer.crs())

        # create vertices and edges
        if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry or self.__options["createRandomGraph"] == True:
            if self.__options["connectionType"] == "Complete":
                self.__createComplete()
            elif self.__options["connectionType"] == "Nearest neighbor" or\
                    self.__options["connectionType"] == "DistanceNN":
                self.__createNearestNeighbor()
            elif self.__options["connectionType"] == "ClusterComplete" or\
                    self.__options["connectionType"] == "ClusterNN":
                self.__createCluster()
            elif self.__options["connectionType"] == "Random":
                self.__createRandomConnections()
            elif self.__options["connectionType"] == "LineLayerBased":
                self.__createLineBasedConnections()

        # user gives lines as input
        elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:
            self.__createGraphForLineGeometry()

        # vector file was exported from a graph layer earlier -> import advanced costs,
        # prevent AdvancedCostCalculations below
        if hasattr(self, "advancedImport") and self.advancedImport:
            self.__importAdvancedCosts()

        # remove edges that cross the polygons
        if self.__options["usePolygonsAsForbidden"] == True:
            self.__removeIntersectingEdges()

        # call AdvancedCostCalculations methods
        if self.__options["distanceStrategy"] == "Advanced" and not (hasattr(self, "advancedImport") and
           not self.advancedImport):
            # create AdvancedCostCalculator object with the necessary parameters
            costCalculator = AdvancedCostCalculator(self.rLayers, self.vLayer, self.graph, self.polygonsForCostFunction,
                                                    self.__options["usePolygonsAsForbidden"], self.rasterBands,
                                                    self.task, self.__options["nnAllowDoubleEdges"],
                                                    self.__options["createShortestPathView"])

            # call the setEdgeCosts method of the AdvancedCostCalculator for every defined cost function
            # the costCalculator returns a ExtGraph where costs are assigned multiple weights,
            # if more then one cost function is defined
            for func in self.costFunctions:
                self.graph = costCalculator.setEdgeCosts(func)
                self.shortestPathViewLayers = costCalculator.shortestPathViewLayers

        # create the layers for QGIS
        if self.__options["createGraphAsLayers"] == True:
            self.createVertexLayer(True)
            self.createEdgeLayer(True)

        return self.graph

    def makeGraphTask(self, task, graphLayer, graphName=""):
        """
        Task function of makeGraph() to build a graph in the background
        :param task: Own QgsTask instance
        :return dictionary
        """
        QgsMessageLog.logMessage('Started task {}'.format(task.description()), level=Qgis.Info)
        # save task in instance for usage in other methods
        self.task = task

        # build graph
        graph = self.makeGraph()

        if self.__options["createRandomGraph"] == False:
            graphLayer.setCrs(self.vLayer.crs())
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayer.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        if not self.task.isCanceled():
            # set graph to graph layer
            graphLayer.setGraph(self.graph)

        if self.task.isCanceled():
            # if task is canceled by User or QGIS
            QgsMessageLog.logMessage('Task {} cancelled'.format(task.description()), level=Qgis.Info)
            self.task = None
            return None
        else:
            QgsMessageLog.logMessage("Make graph finished", level=Qgis.Info)
            self.task = None
            return {"graph": graph, "graphLayer": graphLayer, "graphName": graphName,
                    "shortestPathViewLayers": self.shortestPathViewLayers}
