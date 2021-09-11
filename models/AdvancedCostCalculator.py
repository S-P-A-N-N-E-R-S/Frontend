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
    def __init__(self, rLayers, vLayer, graph, polygons, usePolygons, rasterBands, task):
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
        self.translatedParts = {}
        self.formulaParts = []
        self.aStarAlgObjects = [None] * len(self.rLayers)
        self.task = task
    
    def __translate(self, part, edgeID, sampledPointsLayer, edgesInPolygonsList = None, edgesCrossingPolygonsList = None):          
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
        
        
        # python math method       
        if "math." in part:  
            try:                                         
                mathOperation = part.split(".",1)[1].split("%")[0]           
                if mathOperation in self.mathOperatorsWithTwoVar:          
                    # recursive calls               
                    var1 = part.split("%")[1].split(",")[0]
                    var2 = part.split("$")[0].split(",")[1]
                    return "math." + mathOperation + "(" + var1 + "," + var2 + ")" 
                else:
                    # recursive call            
                    var = part.split("$")[0].split("%")[1]              
                    return "math." + mathOperation + "(" + var + ")"    
            except:
                pass
                     
        if "rnd?" in part:                            
            lb = part.split("?")[1].split("§")[0]
            ub = part.split("&")[0].split("§")[1]                                 
            
            if lb.isnumeric() and ub.isnumeric():               
                return str(random.randint(int(lb),int(ub)))              
            try:
                convertedLB = float(eval(lb))
                convertedUB = float(eval(ub))                               
                return str(random.uniform(convertedLB,convertedUB))               
            except:
                pass    
                                                             
            return part
                                                   
        # translate if part        
        if "if" in part:                                
            expression = part.split(";")[0].split("{",1)[1]    
            expression = expression.replace("and", " and ")
            expression = expression.replace("or", " or ")                                
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
                return str((self.graph.pointsToFeatureHash[self.graph.vertex(edge.toVertex()).point().toString()])[name])
                                  
        # analysis of raster data
        if "raster[" in part:           
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
                findPercentage = re.search("percentOfValues\([0-9]+\)",part)
                findPercentage = findPercentage
                help = findPercentage.group().replace("(","").replace(")","")
                percentage = help.split("percentOfValues")[1]
                    
                listOfPixelValuesAsString = "percentOfValues(" + percentage
                for pValue in self.pointValuesForEdge:                                                                
                    listOfPixelValuesAsString = listOfPixelValuesAsString + "," + str(pValue)                
                    
                listOfPixelValuesAsString = listOfPixelValuesAsString + ")";                   
                return listOfPixelValuesAsString
            
            elif ":shortestPath" in part:
                return self.aStarAlgObjects[rasterDataID].getShortestPathWeight(self.graph.vertex(edge.fromVertex()).point(), self.graph.vertex(edge.toVertex()).point())
                   
        for operator in self.operators:
            if operator in part:
                return str(eval(part))    
        
        return str("0")
          
            
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
    
    def __translateRegexSearch(self, costFunction, regex, edgeID, sampledPointsLayers, edgesInPolygonsList, edgesCrossingPolygonsList, constructCall):
        found = True
        while found:
            found = False
            regex = re.compile(regex)
            res = regex.search(costFunction)
            if res != None:
                found = True             
                translated = self.__translate(costFunction[res.start():res.end()], edgeID, sampledPointsLayers, edgesInPolygonsList, edgesCrossingPolygonsList)
                if not constructCall:
                    self.translatedParts[costFunction[res.start():res.end()]] = translated
                
                costFunction = costFunction[:res.start()] + translated + costFunction[res.end():]                
                
        return costFunction
     
    def __fullyTranslatedCheck(self, costFunction):
        try:
            eval(costFunction)
        except:
            return False
        return True     
        
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
        costFunctionSave = costFunction
        
        for i in range(self.graph.edgeCount()):            
            if self.task is not None and self.task.isCanceled():
                break

            costFunction = costFunctionSave
            self.translatedParts = {} 
            # translate different formula parts by searching constructs with regular expressions: 
            # Call translate method with each extracted construct and replace in formula
                       
            regexList = ['euclidean', 'manhattan', 'ellipsoidal', 'geodesic', 'field:[A-z]+', 
                         'raster\[[0-9]+\]:(percentOfValues\([0-9]+\)|shortestPath|[a-z]+)',
                         'polygon\[[0-9]?\]:(crossesPolygon|insidePolygon)']
            
            for regex in regexList:
                costFunction = self.__translateRegexSearch(costFunction, regex, i, sampledPointsLayers, edgesInPolygonsList, edgesCrossingPolygonsList, False)
            
            constructRegexList = ['math\.[a-z]+%.+?\$', 'rnd\?.+?§.+?&', 'if\{.+?;.+?;.+?\}']
            while not self.__fullyTranslatedCheck(costFunction):
                if self.task is not None and self.task.isCanceled():
                    break
                for regex in constructRegexList:
                    costFunction = self.__translateRegexSearch(costFunction, regex, i, sampledPointsLayers, edgesInPolygonsList, edgesCrossingPolygonsList, True)      

            weights.append(eval(costFunction))
            
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
    