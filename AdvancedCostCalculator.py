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


class AdvancedCostCalculator:
    def __init__(self, rLayer, vLayer, graph):
        self.rLayer = rLayer
        self.vLayerFields = []        
        self.vLayer = vLayer
        self.graph = graph
        for field in vLayer.fields():
            self.vLayerFields.append(field.name())                      
        
        self.operators = ["+","-","*","/","(",")"]
    
    def translate(self, part, edgeID):
        edge = self.graph.edge(edgeID)
        
        # operator or bracket do not need to be translated
        if part in self.operators or part.isnumeric():                       
            return str(part)          
        
        if "euclidean" == part:
            return self.graph.euclideanDist(edgeID)
        
        elif "manhattan" == part:
            return self.graph.manhattanDist(edgeID)
        
        elif "geodesic" == part:
            return self.graph.geodesicDist(edgeID)
        
        # TODO: Add all other variable types and translate them
                 
        # translate if parts if needed if(v1<op>v2;v3;v4)
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
            v1 = self.translate(expression.split(comparator)[0], edgeID)           
            v2 = self.translate(expression.split(comparator)[1].split(";")[0], edgeID)            
            v3 = self.translate(part.split(";")[1], edgeID)
            v4 = self.translate(part.split(";")[2].split(")")[0], edgeID)
           
            return "if" + "(" + str(v1) + comparator + str(v2)+ ";" + str(v3) + ";" + str(v4) + ")"
        
        # python math method
        elif "math." in part:           
            mathOperation = part.split(".")[1].split("(")[0]
            if "," in part:          
                # recursive calls               
                var1 = self.translate(part.split("(")[1].split(",")[0], edgeID)
                var2 = self.translate(part.split(")")[0].split(",")[1], edgeID)
                return "math." + mathOperation + "(" + var1 + "," + var2 + ")" 
            else:
                # recursive call             
                var = self.translate(part.split(")")[0].split(",")[1])
                return "math." + mathOperation + "(" + var + ")"    
        
        elif "field:" in part:
            
            name = part.split(":")[1]
            if self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:  
                count = 0
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()
                    # get end points of line
                    
                    # check if geom and edgeID match
                    if QgsWkbTypes.isMultiType(geom.wkbType()):                 
                        for part in geom.asMultiPolyline():
                            for i in range(len(part)):
                                if i!=0:                                                                                                                                
                                    if count == edgeID:                                                                                                     
                                        return str(feature[name])
                                    count+=1                                            
                    else:                        
                        vertices = geom.asPolyline()                       
                        for i in range(len(vertices)-1):
                            startVertex = vertices[i]
                            endVertex = vertices[i+1]                                                                          
                            if count == edgeID:
                                return str(feature[name])
                            count+=1
            
            # should be point geometry    
            else:                
                for feature in self.vLayer.getFeatures():
                    geom = feature.geometry()
                    if self.graph.vertex(edge.toVertex()).point() == geom.asPoint():
                        return str(feature[name])
                
                
        
        return str("0")
    
    
    def evaluateIfs(self, part):
        # evaluate if expression and return the correct value
        # if construct should look like: if(v1<op>v2;v3;v4)       
        if "if" in part:           
            expression = part.split(";")[0].split("(")[1]
            if eval(expression) == True:
                return part.split(";")[1]
            else:
                return part.split(";")[2].split(")")[0]
        
        return part
        
    def setEdgeCosts(self, costFunction):                                 
        for i in range(self.graph.edgeCount()):
            formulaParts = costFunction.split() 
            for j in range(len(formulaParts)):
                formulaParts[j] = self.translate(formulaParts[j], i)                             
            # after all variables are translated to numbers if conditions can be evaluated
            for j in range(len(formulaParts)):
                formulaParts[j] = self.evaluateIfs(formulaParts[j])
               
            
            # there should only be numbers, brackets and operators inside the translated formula
            translatedFormula = " ".join(formulaParts)
            
            self.graph.edgeWeights.append(eval(translatedFormula))
                
        
        return self.graph    
    
    
    