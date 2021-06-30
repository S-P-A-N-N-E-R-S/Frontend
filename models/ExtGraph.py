from qgis.core import *
from qgis.gui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
import math
from random import *


class ExtGraph(QgsGraph):
    """
    Class extends the QgsGraph by adding a function costOfEdge
    which returns the distance between the two endpoint of an edge.
    Different metrics for this distance can be defined by setting 
    the distanceStrategy attribute of the class
    
    Strategies are divided in cost functions and already set weights
    by an advanced strategy
    """   
    def __init__(self):        
        super().__init__()
        self.distanceStrategy = "Euclidean"
        # list of list to hold multiple weight function values
        self.edgeWeights = []
        self.vertexWeights = []
        # holds the feature IDs if lines where used to create graph
        self.featureMatchings = []
        
    
    def setDistanceStrategy(self, strategy):
        """
        Function is called my the GraphBuilder every time the makeGraph 
        method is called.
        
        :type strategy: String
        """
        self.distanceStrategy = strategy
     
    def setCostOfEdge(self, edgeID, functionIndex, cost):
        """
        Set cost of a specific edge.
        
        :type functionIndex: Integer
        :type edgeID: Integer
        :type cost: Integer
        """
        self.edgeWeights[functionIndex][edgeID] = cost
        
             
    def costOfEdge(self, edgeID, functionIndex = 0):  
        """
        Function to get the weight of an edge. The returned value
        depends on the set distance strategy and on the functionIndex.
        The functionIndex defines the cost function to use if multiple ones
        are given.
        
        :type edgeID: Integer
        :type functionIndex: Integer
        :return cost of Edge
        """                  
        # differentiate between edge weights from cost functions and set weights from graph builder        
        if self.distanceStrategy == "Euclidean":                                                                    
            return self.euclideanDist(edgeID)
        
        elif self.distanceStrategy == "Manhattan":
            return self.manhattanDist(edgeID)
        
        # calculate geodesic distance using the Haversine formula
        elif self.distanceStrategy == "Geodesic":
            return self.geodesicDist(edgeID)
        
        #if the type is advanced the distances are set by the GraphBuilder directly
        elif self.distanceStrategy == "Advanced":
            return self.edgeWeights[functionIndex][edgeID]
        
        else:
            return 0  
    
    def euclideanDist(self, edgeID):
        edgeFromID = self.edge(edgeID)
        fromPoint = self.vertex(edgeFromID.fromVertex()).point()
        toPoint = self.vertex(edgeFromID.toVertex()).point() 
        euclDist = math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2)) 
        return euclDist
        
    def manhattanDist(self, edgeID): 
        edgeFromID = self.edge(edgeID)
        fromPoint = self.vertex(edgeFromID.fromVertex()).point()
        toPoint = self.vertex(edgeFromID.toVertex()).point() 
        manhattenDist = abs(fromPoint.x()-toPoint.x()) + abs(fromPoint.y()-toPoint.y())
        return manhattenDist
    
    def geodesicDist(self, edgeID):
        edgeFromID = self.edge(edgeID)
        fromPoint = self.vertex(edgeFromID.fromVertex()).point()
        toPoint = self.vertex(edgeFromID.toVertex()).point() 
        radius = 6371000
        phi1 = math.radians(fromPoint.y())
        phi2 = math.radians(toPoint.y())        
        deltaPhi = math.radians(toPoint.y()-fromPoint.y())
        deltaLambda = math.radians(toPoint.x()-fromPoint.x())
        a = math.sin(deltaPhi/2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(deltaLambda / 2.0) ** 2    
        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))       
        return radius*c;
           
    def distanceP2P(self, vertex1, vertex2):
        """
        Method to get the euclidean distance between two vertices
        
        :type vertex1: Integer
        :type vertex2: Integer
        :return distance between vertices
        """
        fromPoint = self.vertex(vertex1).point()
        toPoint = self.vertex(vertex2).point()
        return math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))
           
    def hasEdge(self, vertex1, vertex2):
        """
        Method searches for the edge between to vertices
        
        :type vertex1: Integer
        :type vertex2: Integer
        :return Boolean
        """
        for i in range(self.edgeCount()):            
            if self.edge(i).fromVertex() == vertex1 and self.edge(i).toVertex() == vertex2:
                return True
               
        return False             
                          
    def addEdge(self, vertex1, vertex2):       
        # overload to not use distance strategy
        super().addEdge(vertex1, vertex2, [])               
        
    def writeGraphML(self, path):
        """
        Write the graph into a .graphml format
        
        :type path: String       
        """
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
        """
        Read a .graphml file into a ExtGraph
        
        :type path: String
        """     
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
         
        # maybe no coordinate are given in the .graphml file           
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
         
        # if no coordinates are given assign random                             
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
