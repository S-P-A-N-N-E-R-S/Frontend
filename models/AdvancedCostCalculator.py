from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
from .ExtGraph import ExtGraph
from .AStarOnRasterData import *
import random
from qgis import processing
import math
import operator
import re
import statistics
import time
import numpy as np


class AdvancedCostCalculator():
    """
    Class to calculate the edge costs of a graph by analysis of a cost function. The cost function
    can use different variables and operators.    
    """
    def __init__(self, rLayers, vLayer, graph, polygons, usePolygons, rasterBands):
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
        self.pointValuesForEdge = []  
        self.polygons = polygons
        self.usePolygons = usePolygons        
        self.rasterBands = rasterBands
        self.operators = ["+","-","*","/","(",")"]
        self.mathOperatorsWithTwoVar = ["pow","dist","comb", "copysign", "fmod", "ldexp", "remainder", "log", "atan2"]
        self.translatedParts = []
        self.formulaParts = []
        self.aStarAlgObjects = [None] * len(self.rLayers)
    
    def __translate(self, part, edgeID, sampledPointsLayer, edgesInPolygonsList = None, edgesCrossingPolygonsList = None):          
        # check if part string was already translated
        for i in range(len(self.translatedParts)):
            if self.formulaParts[i] == part:
                return self.translatedParts[i]
                                  
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
        
        elif part == "manhattan":
            return str(self.graph.manhattanDist(edgeID))
        
        elif part == "geodesic":
            return str(self.graph.geodesicDist(edgeID))
        
        elif part == "ellipsoidal":
            return str(self.graph.ellipsoidalDist(edgeID))
               
        # translate polygon construct
        regex = re.compile(r'polygon\[[0-9]\]:crossesPolygon')
        res = regex.search(part)
        if res != None:
            index = int(res.group().split("[")[1].split("]")[0])
            for feature in edgesCrossingPolygonsList[index].getFeatures():
                if edgeID == feature["ID"]:
                    return "True"                       
            return "False" 
                      
        # translate polygon construct
        regex = re.compile(r'polygon\[[0-9]\]:insidePolygon')
        res = regex.search(part)
        if res != None:
            index = int(res.group().split("[")[1].split("]")[0])
            for feature in edgesInPolygonsList[index].getFeatures():
                if edgeID == feature["ID"]:
                    return "True"                       
            return "False" 
                                            
        # translate if part
        elif "if" in part:                    
            expression = part.split(";")[0].split("{",1)[1]
            variables = re.split("and|or|not|<|>|==|!=", expression) 
            varTranslations = []        
            
            for i in range (len(variables)):
                variables[i] = variables[i].replace("=", "")
                                                  
            for var in variables:                       
                varTranslations.append(self.__translate(var, edgeID, sampledPointsLayer, edgesInPolygonsList, edgesCrossingPolygonsList))                                            
                      
            counter = 0
            for var in variables:             
                expression = expression.replace(var, str(varTranslations[counter]))  
                counter+=1                                     
                    
            v1 = self.__translate(part.split(";")[1], edgeID, sampledPointsLayer)
            v2 = self.__translate(part.split(";")[2][:-1], edgeID, sampledPointsLayer)            
            expression = expression.replace("and", " and ")
            expression = expression.replace("or", " or ")
            expression = expression.replace("not", " not ")                       
            # expression and variables to set are translated
            return "if" + "{" + expression + ";" + str(v1) + ";" + str(v2) + "}"
                
        # python math method
        elif "math." in part:                     
            mathOperation = part.split(".",1)[1].split("%")[0]           
            if mathOperation in self.mathOperatorsWithTwoVar:          
                # recursive calls               
                var1 = self.__translate(part.split("%")[1].split(",")[0], edgeID, sampledPointsLayer)
                var2 = self.__translate(part.split("$")[0].split(",")[1], edgeID, sampledPointsLayer)
                return "math." + mathOperation + "(" + var1 + "," + var2 + ")" 
            else:
                # recursive call             
                var = self.__translate(part.split("$")[0].split("%")[1], edgeID, sampledPointsLayer)
                return "math." + mathOperation + "(" + var + ")"    
                
        # get specified field information from feature
        elif "field:" in part:                       
            name = part.split(":")[1]            
            if self.vLayer.geometryType() == QgsWkbTypes.LineGeometry and not self.usePolygons:                                        
                return (self.graph.featureMatchings[edgeID])[name]
                                    
            # if polygons are used edges get deleted thus its not possible to just iterate the edges
            elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry and self.usePolygons:                                           
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()
                    if QgsWkbTypes.isMultiType(geom.wkbType()):  
                         for part in geom.asMultiPolyline():
                            for i in range(1,len(part)):                               
                                if part[i-1] == self.graph.vertex(edge.fromVertex()).point() and part[i] == self.graph.vertex(edge.toVertex()).point():
                                    return str(feature[name])
                    else:
                        vertices = geom.asPolyline()                       
                        for i in range(len(vertices)-1):    
                            if vertices[i] == self.graph.vertex(edge.fromVertex()).point() and vertices[i+1] == self.graph.vertex(edge.toVertex()).point():
                                return str(feature[name]) 
            
            # use information from points to set the edge weights
            # only incoming edges are considered         
            elif self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:                                            
                return (self.graph.pointsToFeatureHash[self.graph.vertex(edge.toVertex()).point().toString()])[name]
                                  
        # analysis of raster data
        elif "raster[" in part:           
            rasterDataID = int(part.split("[")[1].split("]")[0])                
            bandForRaster = self.rasterBands[rasterDataID]    
            stringForLookup = "SAMPLE_" + str(bandForRaster)
            self.pointValuesForEdge = []
            #search for the right edgeID
            for feature in sampledPointsLayer[rasterDataID].getFeatures():
                if feature["line_id"] == edgeID:
                    pointValue = feature[stringForLookup]                                      
                    if pointValue is None:
                        pointValue = 0                       
                    self.pointValuesForEdge.append(pointValue)
            
            # check which analysis should be used        
            if ":sum" in part:                
                return str(sum(self.pointValuesForEdge))
            elif ":mean" in part:
                return str(statistics.mean(self.pointValuesForEdge))
            elif ":median" in part:
                return str(statistics.median(self.pointValuesForEdge))
            elif ":min" in part:
                return str(min(self.pointValuesForEdge))
            elif ":max" in part:
                return str(max(self.pointValuesForEdge))
            elif ":variance" in part:
                return str(statistics.variance(self.pointValuesForEdge))
            elif ":standDev" in part:
                return str(statistics.stdev(self.pointValuesForEdge))
            elif ":gradientSum" in part:
                f = np.array(self.pointValuesForEdge, dtype=float)
                gradient = np.gradient(f)
                return str(np.sum(gradient))
            elif ":gradientMin" in part:
                f = np.array(self.pointValuesForEdge, dtype=float)
                gradient = np.gradient(f)
                return str(np.min(gradient))
            elif ":gradientMax" in part:
                f = np.array(self.pointValuesForEdge, dtype=float)
                gradient = np.gradient(f)
                return str(np.max(gradient))
            elif ":ascent" in part:
                ascent = 0
                for i in range(len(self.pointValuesForEdge)-1):
                    if self.pointValuesForEdge[i] < self.pointValuesForEdge[i+1]:
                        ascent = ascent + (self.pointValuesForEdge[i+1] - self.pointValuesForEdge[i])
                return str(ascent)                             
            elif ":descent" in part:
                descent = 0
                for i in range(len(self.pointValuesForEdge)-1):
                    if self.pointValuesForEdge[i] > self.pointValuesForEdge[i+1]:
                        descent = descent + (self.pointValuesForEdge[i] - self.pointValuesForEdge[i+1])
                return str(descent)        
            elif ":totalClimb" in part:
                totalClimb = 0
                for i in range(len(self.pointValuesForEdge)-1):
                    totalClimb = totalClimb + abs(self.pointValuesForEdge[i] - self.pointValuesForEdge[i+1])
                return str(totalClimb) 
            # last two types can only occur in if construct
            elif ":pixelValue" in part:                 
                listOfPixelValuesAsString = "pixelValue("
                for i in range(0, len(self.pointValuesForEdge)-1):                                                                          
                    listOfPixelValuesAsString = listOfPixelValuesAsString + str(self.pointValuesForEdge[i]) + ","                 
                 
                listOfPixelValuesAsString = listOfPixelValuesAsString + str(self.pointValuesForEdge[len(self.pointValuesForEdge)-1]);   
                 
                listOfPixelValuesAsString = listOfPixelValuesAsString + ")";                 
                return listOfPixelValuesAsString                              
            elif ":percentOfValues" in part:
                findPercentage = re.search("percentOfValues[0-9]+",part)
                help = findPercentage.group()
                percentage = help.split("percentOfValues")[1]
                    
                listOfPixelValuesAsString = "percentOfValues(" + percentage
                for pValue in self.pointValuesForEdge:                                                                
                    listOfPixelValuesAsString = listOfPixelValuesAsString + "," + str(pValue)                
                    
                listOfPixelValuesAsString = listOfPixelValuesAsString + ")";                   
                return listOfPixelValuesAsString
            
            elif ":shortestPath" in part:
                return self.aStarAlgObjects[rasterDataID].getShortestPathWeight(self.graph.vertex(edge.fromVertex()).point(), self.graph.vertex(edge.toVertex()).point())
                                                
        elif "rnd?" in part:
            lb = part.split("?")[1].split(",")[0]
            ub = part.split("&")[0].split(",")[1]
                                             
            try:
                convertedLB = float(lb)
                convertedUB = float(ub)
                if "." in lb or "." in ub:                    
                    return random.uniform(convertedLB,convertedUB)
            except ValueError:
                pass
          
            translated = False                        
            if not lb.isnumeric():
                lb = self.__translate(lb, edgeID, sampledPointsLayer)
                translated = True
            if not ub.isnumeric():
                ub = self.__translate(ub, edgeID, sampledPointsLayer)
                translated = True
            if translated == True:
                convertedLB = float(lb)
                convertedUB = float(ub)
                return random.uniform(convertedLB,convertedUB)           
            
            return random.randint(int(lb),int(ub))
            
        return str("0")
        
    def __evaluateIfs(self, part):
        """
        Evaluate if expression and return the correct value.
        If construct should look like: if(v1<op>v2;v3;v4) 
        
        :type part: String
        """            
        if "if" in part:                 
            expression = part.split(";")[0].split("{",1)[1]                                   
            expressionParts = re.split("and|or", expression)          
            for expPart in expressionParts: 
                if "pixelValue" in expPart:                    
                    listString = expPart.split("(")[1].split(")")[0]
                    if "," in listString:                        
                        list = listString.split(",")
                        equalTrue = False
                        for l in list:
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
                    list = listString.split(",")
                    percentage = list[0]
                    
                    trueExpFount = 0

                    for l in range(1, len(list)):
                        toEval = re.sub(r"percentOfValues\(([0-9]+,)+[0-9]+\)", "", expPart) 
                        toEval = list[l] + toEval
                      
                        if eval(toEval) == True:
                            trueExpFount+=1  
                   
                                       
                    if int(percentage) <= (trueExpFount / (len(list)-1))*100:
                        expression = expression.replace(expPart, " True ")
                    else:
                        expression = expression.replace(expPart, " False ")       
                      
            if eval(expression) == True:              
                return part.split(";")[1]
            else:
                return part.split(";")[2].split("}")[0]
        
        return part    
            
    def __createEdgeLayer(self): 
        """
        Creates an edge layer for the graph. This is used to call QGIS-Tools which
        require vector layers as attributes
        
        :return QgsVectorLayer
        """
        graphLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")        
        dpEdgeLayer = graphLayerEdges.dataProvider()
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int),])
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
        
    def setEdgeCosts(self, costFunction, edgeID = None, costFunctionCount = None):    
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
                result = processing.run("qgis:generatepointspixelcentroidsalongline", {"INPUT_RASTER": self.rLayers[i], "INPUT_VECTOR": edgeLayer, "OUTPUT": "memory:"})
                result2 = processing.run("qgis:rastersampling",{"INPUT": result["OUTPUT"], "RASTERCOPY": self.rLayers[i], "COLUMN_PREFIX": "SAMPLE_", "OUTPUT": "memory:"})
                sampledPointsLayers.append(result2["OUTPUT"])  
        
        # initialize all necessary AStarOnRasterData objects
        regex = re.compile(r'raster\[[0-9]\]:shortestPath')
        res = regex.findall(costFunction)
        for matchString in res:
            rasterIndex = int(matchString.split("[")[1].split("]")[0])
            self.aStarAlgObjects[rasterIndex] = AStarOnRasterData(self.rLayers[rasterIndex], self.rasterBands[rasterIndex], self.vLayer.crs())
        
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
                    polygonResult = processing.run("native:extractbylocation", {"INPUT": edgeLayer, "PREDICATE": 6, "INTERSECT": polygon, "OUTPUT": "memory:"})
                    edgesInPolygons = polygonResult["OUTPUT"]  
                    edgesInPolygonsList.append(edgesInPolygons)             
                if "crossesPolygon" in costFunction:
                    polygonResult = processing.run("native:extractbylocation", {"INPUT": edgeLayer, "PREDICATE": 7, "INTERSECT": polygon, "OUTPUT": "memory:"})
                    edgesCrossingPolygons = polygonResult["OUTPUT"]
                    edgesCrossingPolygonsList.append(edgesCrossingPolygons)
                                    
        costFunction = costFunction.replace(" ", "").replace('"', '')           
        self.formulaParts = re.split("\+|-|\*|/", costFunction)
        variables = []
                       
        for i in range(len(self.formulaParts)):
            self.formulaParts[i] = self.formulaParts[i].replace("(","").replace(")","")
            variables.append(self.formulaParts[i])
                                                   
        # since the function value depends on the edge the function needs to be evaluated for every edge separately                                                                  
        #if edgeID == None:            
        for i in range(self.graph.edgeCount()):  
            self.translatedParts = []                                                                 
            # call function to translate the  parts            
            for j in range(len(self.formulaParts)):
                   
                self.translatedParts.append(self.__translate(self.formulaParts[j], i, sampledPointsLayers, edgesInPolygonsList, edgesCrossingPolygonsList))  
                                                                                                                    
            # after all variables are translated to numbers if conditions can be evaluated
            for j in range(len(self.formulaParts)):
                self.translatedParts[j] = self.__evaluateIfs(str(self.translatedParts[j]))                    
                       
                            
            counter = 0                       
            translatedFormula = costFunction
            for var in variables:        
                
                while re.search("percentOfValues[0-9]+", var):
                    find = re.search("percentOfValues[0-9]+",var)
                    findStartEnd = find.span()
                    findStart = findStartEnd[0]
                    findEnd = findStartEnd[1]
                    startOfNumbers = re.search("[0-9]+", find.group()).span()[0]
                    endOfNumbers = re.search("[0-9]+", find.group()).span()[1]
                    var = var[:findStart+startOfNumbers] + "(" + var[startOfNumbers+findStart:endOfNumbers+findStart] + ")" + var[endOfNumbers+findStart:]
                    
                    #translatedFormula = translatedFormula.replace("(","").replace(")","")               
                translatedFormula = translatedFormula.replace(var,str(self.translatedParts[counter]),1)
               
                counter+=1    
                                                                     
            weights.append(eval(translatedFormula))                                             
            
        # append the list        
        self.graph.edgeWeights.append(weights)
        """
        FOR EDETING WITH ADVANCED COSTS:
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
                    translatedParts.append(self.__translate(formulaParts[j], edgeID, sampledPointsLayers, edgesInPolygons, edgesCrossingPolygons))  
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
    