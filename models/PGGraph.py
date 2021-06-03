from qgis.core import *
from qgis.gui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
import math
from random import *



"""
Class extends the QgsGraph by adding a function costOfEdge
which returns the distance between the two endpoint of an edge.
Different metrics for this distance can be defined by setting 
the distanceStrategy attribute of the class

Strategies are divided in cost functions and already set weights
"""
class PGGraph(QgsGraph):
    
    def __init__(self):        
        super().__init__()
        self.distanceStrategy = "Euclidean"
        self.edgeWeights = []        
        self.vertexWeights = []
     
    
    def setDistanceStrategy(self, strategy):
        self.distanceStrategy = strategy
     
          
    def costOfEdge(self, edgeID):        
        edgeFromID = self.edge(edgeID)
        
        #differentiate between edge weights from cost functions and set weights from graph builder        
        if self.distanceStrategy == "Euclidean":                       
            fromPoint = self.vertex(edgeFromID.fromVertex()).point()
            toPoint = self.vertex(edgeFromID.toVertex()).point()        
            euclDist = math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))                     
            return euclDist
        else:
            return 0  
    
    def distanceP2P(self, vertex1, vertex2):
        fromPoint = self.vertex(vertex1).point()
        toPoint = self.vertex(vertex2).point()
        return math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))
        
    
    def hasEdge(self, vertex1, vertex2):
        for i in range(self.edgeCount()):            
            if self.edge(i).fromVertex() == vertex1 and self.edge(i).toVertex() == vertex2:
                return True
               
        return False
              
    
    def findEdgeWithID(self, startVertex, endVertex):
        for i in range(self.edgeCount()):
            if self.edge(i).fromVertex() == startVertex and self.edge(i).toVertex == endVertex:
                return True
        return False
    
    def findEdgeWithPoints(self, startVertex, endVertex):
        idStart = self.findVertex(startVertex)
        idEnd = self.findVertex(endVertex)
        
        if idStart != -1 and idEnd != -1:
            for i in range(self.edgeCount()):
                if self.edge(i).fromVertex() == idStart and self.edge(i).toVertex == idEnd:
                    return True
        
        return False
        
                   
    def addEdge(self, vertex1, vertex2):
        super().addEdge(vertex1, vertex2, [])
        
        
        
    def writeGraphML(self, path):
        file = open(path, "w")
        header = ['<?xml version="1.0" encoding="UTF-8"?>\n',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n',  
            '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
            '\txmlns:y="http://www.yworks.com/xml/graphml"\n',
            '\txsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n',
            '\t http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n',
            '\t<key for="node" id="d1" yfiles.type="nodegraphics"/>\n']
        
        file.writelines(header)
        file.write('\t<graph id="G" edgedefault="directed">\n')
        
        for i in range(self.vertexCount()):
            nodeLine = '\t\t<node id="' + str(i) + '"/>\n'
            file.write(nodeLine) 
            file.write('\t\t\t<data key="d1">\n')
            file.write('\t\t\t\t<y:ShapeNode>\n')
            coordinates = '\t\t\t\t\t<y:Geometry height="30.0" width="30.0" x="' + str(self.vertex(i).point().x()) + '" y="' + str(self.vertex(i).point().y()) + '"/>\n'
            file.write(coordinates)
            file.write('\t\t\t\t</y:ShapeNode>\n')
            file.write('\t\t\t</data>\n')
        
        for i in range(self.edgeCount()):
            edgeLine = '\t\t<edge source="' + str(self.edge(i).fromVertex()) + '" target="' + str(self.edge(i).toVertex()) + '"/>\n'
            file.write(edgeLine)
        
        file.write("\t</graph>\n")
        file.write("</graphml>")
        file.close()
        
    def readGraphML(self, path):        
        file = open(path, "r")
        lines = file.readlines()
        nodeCoordinatesGiven = False
        edgeTypeDirection = "Directed"
        nodeIDs = []
        
        for line in lines:
            if 'edgedefault="undirected"' in line:
                edgeTypeDirection = "Undirected"                       
            elif 'x="' in line and 'y="' in line:
                nodeCoordinatesGiven = True
                break
                   
        if nodeCoordinatesGiven == True:
            for line in lines:
                if '<node' in line:
                    nodeIDs.append(line.split('id="')[1].split('"')[0])
                
                elif 'x="' in line:
                    xValue = float(line.split('x="')[1].split(' ')[0].split('"')[0])
                    yValue = float(line.split('y="')[1].split(' ')[0].split('"')[0])
                    self.addVertex(QgsPointXY(xValue, yValue))                      
                    
                elif '<edge' in line:
                    fromVertex = line.split('source="')[1].split('"')[0]
                    toVertex = line.split('target="')[1].split('"')[0]
                    fromVertexID = 0
                    toVertexID = 0
                    
                    for i in range(len(nodeIDs)):
                        if nodeIDs[i] == fromVertex:
                            fromVertexID = i
                        elif nodeIDs[i] == toVertex:
                            toVertexID = i    
                    
                    self.addEdge(fromVertexID, toVertexID)                     
                    if edgeTypeDirection == "Undirected":   
                        self.addEdge(toVertexID, fromVertexID)      
                                         
        else:
            for line in lines:
                if '<node' in line:
                    self.addVertex(QgsPointXY(randrange(742723,1534455), randrange(6030995,7314884))) 
                    nodeIDs.append(line.split('id="')[1].split('"')[0])
        
                elif '<edge' in line:
                    fromVertex = line.split('source="')[1].split('"')[0]
                    toVertex = line.split('target="')[1].split('"')[0]
                    fromVertexID = 0
                    toVertexID = 0
                    
                    for i in range(len(nodeIDs)):
                        if nodeIDs[i] == fromVertex:
                            fromVertexID = i
                        elif nodeIDs[i] == toVertex:
                            toVertexID = i    
                    self.addEdge(fromVertexID, toVertexID)