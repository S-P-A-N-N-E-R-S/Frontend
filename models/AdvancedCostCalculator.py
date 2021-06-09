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


class AdvancedCostCalculator:
    """
    Class to calculate the edge costs of a graph by analysis of a cost function. The cost function
    can use different variables and operators.    
    """
    def __init__(self, rLayers, vLayer, graph, buildShortestPathNetwork, usePolygons):
        """
        Constructor
        
        :type rLayer: QgsRasterLayer
        :type vLayer: QgsVectorLayer
        :type graph: PGGraph
        :type buildShortestPathNetwork: Boolean
        :type usePolygons: Boolean
        """
        self.rLayers = rLayers
        self.vLayerFields = []        
        self.vLayer = vLayer
        self.graph = graph
        self.buildShortestPathNetwork = buildShortestPathNetwork
        self.usePolygons = usePolygons        
        self.operators = ["+","-","*","/","(",")"]
        self.numberOfWeightFunctions = 0
    
    def __translate(self, part, edgeID):
        edge = self.graph.edge(edgeID)
        
        # operator or bracket do not need to be translated
        if part in self.operators or part.isnumeric():                       
            return str(part)          
        
        # normal distance metrics
        if "euclidean" == part:
            return str(self.graph.euclideanDist(edgeID))
        
        elif "manhattan" == part:
            return str(self.graph.manhattanDist(edgeID))
        
        elif "geodesic" == part:
            return str(self.graph.geodesicDist(edgeID))
                        
        # translate if part
        elif "if" in part:            
            expression = part.split(",")[0].split("(")[1]
            if "<" in expression:
                comparator = "<"
            elif ">" in expression:
                comparator = ">"
            elif "!=" in expression:
                comparator = "!="
            elif "==" in expression:
                comparator = "=="
            elif ">=" in expression:
                comparator = ">="
            elif "<=" in expression:
                comparator = "<="       
            
            # recursive calls
            v1 = self.__translate(expression.split(comparator)[0], edgeID)           
            v2 = self.__translate(expression.split(comparator)[1].split(",")[0], edgeID)            
            v3 = self.__translate(part.split(",")[1], edgeID)
            v4 = self.__translate(part.split(",")[2].split(")")[0], edgeID)
           
            return "if" + "(" + str(v1) + comparator + str(v2)+ "," + str(v3) + "," + str(v4) + ")"
        
        # python math method
        elif "math." in part:           
            mathOperation = part.split(".")[1].split("(")[0]
            if "," in part:          
                # recursive calls               
                var1 = self.__translate(part.split("(")[1].split(",")[0], edgeID)
                var2 = self.__translate(part.split(")")[0].split(",")[1], edgeID)
                return "math." + mathOperation + "(" + var1 + "," + var2 + ")" 
            else:
                # recursive call             
                var = self.__translate(part.split(")")[0].split(",")[1])
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
        elif "raster:" in part:
            print("TODO")
        
        return str("0")
        
    def __evaluateIfs(self, part):
        """
        Evaluate if expression and return the correct value.
        If construct should look like: if(v1<op>v2,v3,v4) 
        
        :type part: String
        """      
        if "if" in part:           
            expression = part.split(",")[0].split("(")[1]
            if eval(expression) == True:
                return part.split(",")[1]
            else:
                return part.split(",")[2].split(")")[0]
        
        return part
        
    def setEdgeCosts(self, costFunction):    
        """
        Set the cost function for the edge cost calculation.
        
        :type costFunction: String
        :return graph with set edge costs
        """           
        self.numberOfWeightFunctions += 1   
        result = []                   
        for i in range(self.graph.edgeCount()):
            costFunction = costFunction.replace(" ", "").replace('"', '')
            
            formulaParts = re.split("\+|-|\*|/", costFunction)
            operators = []
            
            for symbol in costFunction:
                if symbol == "+" or symbol == "-" or symbol == "*" or symbol == "/":
                    operators.append(symbol)                        
            
            for j in range(len(formulaParts)):
                formulaParts[j] = self.__translate(formulaParts[j], i)                             
            
            # after all variables are translated to numbers if conditions can be evaluated
            for j in range(len(formulaParts)):
                formulaParts[j] = self.__evaluateIfs(str(formulaParts[j]))
            
            translatedFormula = formulaParts[0]   
            for p in range(len(operators)):
                translatedFormula = translatedFormula + operators[p] + formulaParts[p+1] 
            
            result.append(eval(translatedFormula))
            # there are only be numbers, brackets and operators inside the translated formula                                   
        
        self.graph.edgeWeights.append(result)
                        
        return self.graph    
    
    
    