from qgis.core import *
from qgis.gui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
import math


"""
Class extends the QgsGraph by adding a function costOfEdge
which returns the distance between the two endpoint of an edge.
Different metrics for this distance can be defined by setting 
the distanceMetric attribute of the class
"""
class PGGraph(QgsGraph):

    def __init__(self):        
        super().__init__()
        self.distanceMetric = "Euclidean"
        
    def costOfEdge(self, edge):               
        if self.distanceMetric == "Euclidean":            
            fromPoint = self.vertex(edge.fromVertex()).point()
            toPoint = self.vertex(edge.toVertex()).point()        
            euclDist = math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))           
            return euclDist
        else:
            return 0   

    def costOfEdgeID(self, edgeID):        
        edgeFromID = self.edge(edgeID)
        if self.distanceMetric == "Euclidean":            
            fromPoint = self.vertex(edgeFromID.fromVertex()).point()
            toPoint = self.vertex(edgeFromID.toVertex()).point()        
            euclDist = math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))           
            return euclDist
        else:
            return 0  
    


    def addEdge(self, vertex1, vertex2):
        super().addEdge(vertex1, vertex2, [])
