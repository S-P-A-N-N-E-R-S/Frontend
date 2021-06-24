from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
from .PGGraph import PGGraph
from random import *
from qgis import processing
import math
import operator
import re
import statistics
import numpy as np


class AdvancedCostCalculator():
    """
    Class to calculate the edge costs of a graph by analysis of a cost function. The cost function
    can use different variables and operators.    
    """
    def __init__(self, rLayers, vLayer, graph, buildShortestPathNetwork, usePolygons, rasterBands):
        """
        Constructor
        
        :type rLayer: List of QgsRasterLayer
        :type vLayer: QgsVectorLayer
        :type graph: PGGraph
        :type buildShortestPathNetwork: Boolean
        :type usePolygons: Boolean
        :type rasterBands: List of Integer [1..numberOfBands]
        """
        self.rLayers = rLayers
        self.vLayerFields = []        
        self.vLayer = vLayer
        self.graph = graph
        self.buildShortestPathNetwork = buildShortestPathNetwork
        self.usePolygons = usePolygons        
        self.rasterBands = rasterBands
        self.operators = ["+","-","*","/","(",")"]
    
    def __translate(self, part, edgeID, sampledPointsLayer):
        edge = self.graph.edge(edgeID)       
        # operator or bracket do not need to be translated
        if part in self.operators or part.isnumeric():                       
            return str(part)          
       
        # normal distance metrics
        if "euclidean" in part:
            return str(self.graph.euclideanDist(edgeID))
        
        elif "manhattan" in part:
            return str(self.graph.manhattanDist(edgeID))
        
        elif "geodesic" in part:
            return str(self.graph.geodesicDist(edgeID))
                        
        # translate if part
        elif "if" in part:            
            expression = part.split(",")[0].split("[",1)[1]
            variables = re.split("and|or|not|<|>|==|!=", expression) 
            varTranslations = []        
            
            for i in range (len(variables)):
                variables[i] = variables[i].replace("=", "")
                                       
            for var in variables:
                varTranslations.append(self.__translate(var, edgeID, sampledPointsLayer))                                            
            
            counter = 0
            for var in variables:             
                expression = expression.replace(var, str(varTranslations[counter]))  
                counter+=1                                     
            
            #print(part.split(",")[1])
            #print(part.split(",")[2].split("]")[0])
            
            v1 = self.__translate(part.split(",")[1], edgeID, sampledPointsLayer)
            v2 = self.__translate(part.split(",")[2][:-1], edgeID, sampledPointsLayer)            
            expression = expression.replace("and", " and ")
            expression = expression.replace("or", " or ")
            expression = expression.replace("not", " not ")
                                    
            # expression and variables to set are translated
            return "if" + "[" + expression + "," + str(v1) + "," + str(v2) + "]"
        
        # python math method
        elif "math." in part:           
            mathOperation = part.split(".")[1].split("(")[0]
            if "," in part:          
                # recursive calls               
                var1 = self.__translate(part.split("(")[1].split(",")[0], edgeID, sampledPointsLayer)
                var2 = self.__translate(part.split(")")[0].split(",")[1], edgeID, sampledPointsLayer)
                return "math." + mathOperation + "(" + var1 + "," + var2 + ")" 
            else:
                # recursive call             
                var = self.__translate(part.split(")")[0].split(",")[1], edgeID, sampledPointsLayer)
                return "math." + mathOperation + "(" + var + ")"    
        
        # get specified field information from feature
        elif "field:" in part:           
            name = part.split(":")[1]
            if self.vLayer.geometryType() == QgsWkbTypes.LineGeometry and not self.usePolygons and not self.buildShortestPathNetwork:  
                count = 0
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()                                     
                    # check if geom and edgeID match
                    if QgsWkbTypes.isMultiType(geom.wkbType()):                 
                        for part in geom.asMultiPolyline():
                            for i in range(1,len(part)):                                                                                                                                                              
                                    if count == edgeID:                                                                                                     
                                        return str(feature[name])
                                    count+=1                                            
                    else:                        
                        vertices = geom.asPolyline()                       
                        for i in range(len(vertices)-1):                                                                                             
                            if count == edgeID:
                                return str(feature[name])
                            count+=1
            
            # if polygons are used edges get deleted thus its not possible to just iterate the edges
            # same if you use points and the vLayer represents the additional line layer for the network 
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
                            if vertices[i] == self.graph.vertex(edge.fromVertex()).point() and vertices[i+1] == self.graph(edge.toVertex()).point():
                                return str(feature[name])
                               
            # if the shortest path network is used, the vLayer is set to the network 
            elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry and self.buildShortestPathNetwork: 
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()
                    if QgsWkbTypes.isMultiType(geom.wkbType()):  
                         for part in geom.asMultiPolyline():
                            for i in range(1,len(part)):                               
                                if part[i-1] == self.graph.vertex(edge.fromVertex()).point() and part[i] == self.graph.vertex(edge.toVertex()).point():                                                               
                                    return str(feature[name])
                                elif part[i-1] == self.graph.vertex(edge.toVertex()).point() and part[i] == self.graph.vertex(edge.fromVertex()).point():
                                    return str(feature[name])
                    else:           
                        vertices = geom.asPolyline()                       
                        for i in range(len(vertices)-1):    
                            if vertices[i] == self.graph.vertex(edge.fromVertex()).point() and vertices[i+1] == self.graph(edge.toVertex()).point():
                                return str(feature[name])
                            elif vertices[i] == self.graph.vertex(edge.toVertex()).point() and vertices[i+1] == self.graph(edge.FromVertex()).point():
                                return str(feature[name])
            
            # use information from points to set the edge weights
            # only incoming edges are considered         
            elif self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:               
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()
                    if self.graph.vertex(edge.toVertex()).point() == geom.asPoint():
                        return str(feature[name])                      
        
        # analysis of raster data
        elif "raster[" in part:
            rasterDataID = int(part.split("[")[1].split("]")[0])
            pointValuesForEdge = []       
            bandForRaster = self.rasterBands[rasterDataID]    
            stringForLookup = "SAMPLE_" + str(bandForRaster)
            #search for the right edgeID
            for feature in sampledPointsLayer[rasterDataID].getFeatures():
                if feature["line_id"] == edgeID:
                    pointValuesForEdge.append(feature[stringForLookup])
            
            # check which analysis should be used        
            if ":sum" in part:                
                return str(sum(pointValuesForEdge))
            elif ":mean" in part:
                return str(statistics.mean(pointValuesForEdge))
            elif ":median" in part:
                return str(statistics.median(pointValuesForEdge))
            elif ":min" in part:
                return str(min(pointValuesForEdge))
            elif ":max" in part:
                return str(max(pointValuesForEdge))
            elif ":variance" in part:
                return str(statistics.variance(pointValuesForEdge))
            elif ":standDev" in part:
                return str(statistics.stdev(pointValuesForEdge))
            elif ":gradientSum" in part:
                f = np.array(pointValuesForEdge, dtype=float)
                gradient = np.gradient(f)
                return str(np.sum(gradient))
            elif ":gradientMin" in part:
                f = np.array(pointValuesForEdge, dtype=float)
                gradient = np.gradient(f)
                return str(np.min(gradient))
            elif ":gradientMax" in part:
                f = np.array(pointValuesForEdge, dtype=float)
                gradient = np.gradient(f)
                return str(np.max(gradient))
            elif ":ascent" in part:
                ascent = 0
                for i in range(len(pointValuesForEdge)-1):
                    if pointValuesForEdge[i] < pointValuesForEdge[i+1]:
                        ascent = ascent + (pointValuesForEdge[i+1] - pointValuesForEdge[i])
                return str(ascent)                             
            elif ":descent" in part:
                descent = 0
                for i in range(len(pointValuesForEdge)-1):
                    if pointValuesForEdge[i] > pointValuesForEdge[i+1]:
                        descent = descent + (pointsValuesForEdge[i] - pointValuesForEdge[i+1])
                return str(descent)        
            elif ":totalClimb" in part:
                totalClimb = 0
                for i in range(len(pointValuesForEdge)-1):
                    totalClimb = totalClimb + abs(pointValuesForEdge[i] - pointValuesForEdge[i+1])
                return str(totalClimb) 
                        
        return str("0")
        
    def __evaluateIfs(self, part):
        """
        Evaluate if expression and return the correct value.
        If construct should look like: if(v1<op>v2,v3,v4) 
        
        :type part: String
        """      
        
        if "if" in part:                 
            expression = part.split(",")[0].split("[",1)[1]                    
            if eval(expression) == True:
                
                return part.split(",")[1]
            else:
                return part.split(",")[2].split("]")[0]
        
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
        
    def setEdgeCosts(self, costFunction):    
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
        
        costFunction = costFunction.replace(" ", "").replace('"', '')       
            
        formulaParts = re.split("\+|-|\*|/", costFunction)
        variables = []
        
        for i in range(len(formulaParts)):
            formulaParts[i] = formulaParts[i].replace("(","").replace(")","")
            variables.append(formulaParts[i])
                                                   
        # since the function value depends on the edge the function needs to be evaluated for every edge separately                                                          
        for i in range(self.graph.edgeCount()):   
            translatedParts = []                                                       
            # call function to translate the  parts            
            for j in range(len(formulaParts)):                                            
                translatedParts.append(self.__translate(formulaParts[j], i, sampledPointsLayers))                                                                         
            # after all variables are translated to numbers if conditions can be evaluated
            for j in range(len(formulaParts)):
                translatedParts[j] = self.__evaluateIfs(str(translatedParts[j]))
            
            counter = 0                       
            translatedFormula = costFunction
            for var in variables:               
                translatedFormula = translatedFormula.replace(var,str(translatedParts[counter]))
                counter+=1
            
            print(translatedFormula)           
            weights.append(eval(translatedFormula))                                             
        
        # append the list
        self.graph.edgeWeights.append(weights)
                        
        return self.graph    
    
    
    