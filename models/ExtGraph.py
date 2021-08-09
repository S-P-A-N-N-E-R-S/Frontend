from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

from qgis.PyQt.QtCore import QObject

import math
from random import *

"""
Class extends the QgsGraph by adding a function costOfEdge
which returns the distance between the two endpoint of an edge.
Different metrics for this distance can be defined by setting 
the distanceStrategy attribute of the class

Strategies are divided in cost functions and already set weights
"""
class ExtGraph(QObject):
    
    #==ExtVertex===================================================================
    class ExtVertex:
        """
        Inner class representing a vertex of the ExtGraph
        """
        def __init__(self, point):
            self.mCoordinates = point
            self.mIncomingEdges = []
            self.mOutgoingEdges = []

        def __del__(self):
            del self.mCoordinates
            del self.mIncomingEdges
            del self.mOutgoingEdges

        def incomingEdges(self):
            return self.mIncomingEdges

        def outgoingEdges(self):
            return self.mOutgoingEdges

        def point(self):
            return self.mCoordinates

    #==ExtEdge=======================================================================
    class ExtEdge:
        """
        Inner class representing an edge of the ExtGraph
        """
        def __init__(self, fromVertexIdx, toVertexIdx):
            # TODO: add costs list for an edge here?
            self.mFromIdx = fromVertexIdx
            self.mToIdx = toVertexIdx

        def __del__(self):
            pass

        def fromVertex(self):
            return self.mFromIdx

        def toVertex(self):
            return self.mToIdx

    #==ExtGraph Methods===============================================================
    def __init__(self):        
        super().__init__()
        self.distanceStrategy = "Euclidean"
        self.mConnectionType = "None"
        self.edgeWeights = []        
        self.vertexWeights = []

        self.mVertices = {}
        self.mEdges = {}

        self.mEdgeCount = 0
        self.mVertexCount = 0

        self.__availableVertexIndices =[]
        self.__availableEdgeIndices = []

        # holds the feature IDs if lines where used to create graph
        self.featureMatchings = []
     
    def __del__(self):
        del self.edgeWeights
        del self.vertexWeights
        del self.mVertices
        del self.mEdges
        
        del self.__availableVertexIndices
        del self.__availableEdgeIndices

    def setDistanceStrategy(self, strategy):
        """
        Function is called my the GraphBuilder every time the makeGraph 
        method is called.
        
        :type strategy: String
        """
        self.distanceStrategy = strategy
    
    def setConnectionType(self, connectionType):
        self.mConnectionType = connectionType

    def connectionType(self):
        return self.mConnectionType

    def setCostOfEdge(self, edgeID, functionIndex, cost):
        """
        Set cost of a specific edge.
        
        :type functionIndex: Integer
        :type edgeID: Integer
        :type cost: Integer
        """
        while len(self.edgeWeights) <= functionIndex:
            self.edgeWeights.append([])
        
        while len(self.edgeWeights[functionIndex]) <= edgeID:
            self.edgeWeights[functionIndex].append(-1)
        
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
        
        elif self.distanceStrategy == "None":
            return None
        
        else:
            raise NameError("Unknown distance strategy")
    
    
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
        return radius*c  
    
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
        :return Integer found edgeIdx, else -1
        """
        # TODO: maybe return edgeIdx
        for edgeIdx in self.mEdges:
            edge = self.mEdges[edgeIdx]            
            if edge.fromVertex() == vertex1 and edge.toVertex() == vertex2:
                return edgeIdx
               
        return -1
                   
    def addEdge(self, vertex1, vertex2, idx=-1):
        addIndex = self.mEdgeCount
        if idx >= 0:
            addIndex = idx
        elif len(self.__availableEdgeIndices) > 0:
            # check if other indices are available due to earlier delete
            print("Use earlier edge index")
            addIndex = self.__availableEdgeIndices.pop(0)

        self.mEdges[addIndex] = self.ExtEdge(vertex1, vertex2)
        self.mVertices[vertex1].mOutgoingEdges.append(addIndex)
        self.mVertices[vertex2].mIncomingEdges.append(addIndex)
        self.mEdgeCount += 1

        return addIndex

    def addVertex(self, point, idx=-1):
        addIndex = self.mVertexCount
        if idx >= 0:
            addIndex = idx
        elif len(self.__availableVertexIndices) > 0:
            # check if other indices are available due to earlier delete
            print("Use earlier vertex index")
            addIndex = self.__availableVertexIndices.pop(0)

        self.mVertices[addIndex] = self.ExtVertex(point)
        self.mVertexCount += 1
        
        return addIndex

    def edge(self, idx):
        if idx in self.mEdges:
            return self.mEdges[idx]
        return None

    def edgeCount(self):
        return self.mEdgeCount

    def findVertex(self, vertex, tolerance=0):
        """
        Modified findVertex function to find a vertex within a tolerance square

        :type vertex: QgsPointXY
        :type tolerance: int
        :return vertexId: Integer
        """
        if tolerance > 0:
            toleranceRect = QgsRectangle.fromCenterAndSize(vertex, tolerance, tolerance)
        
        for idx in self.mVertices:
            checkVertex = self.vertex(idx)
            
            if tolerance == 0 and checkVertex.point() == vertex:
                return idx
            elif tolerance > 0 and toleranceRect.contains(checkVertex.point()):
                return idx

        return -1
    
    def vertex(self, idx):
        if idx in self.mVertices:
            return self.mVertices[idx]
        return None

    def vertexCount(self):
        return self.mVertexCount

    def vertices(self):
        return self.mVertices

    def edges(self):
        return self.mEdges

    def deleteEdge(self, idx):
        if idx in self.mEdges:
            edge = self.mEdges[idx]

            # remove edge from toVertex incomingEdges
            toVertex = self.vertex(edge.toVertex())
            for edgeIdx in range(len(toVertex.mIncomingEdges)):
                if toVertex.mIncomingEdges[edgeIdx] == idx:
                    toVertex.mIncomingEdges.pop(edgeIdx)
                    break
            # remove edge from fromVertex outgoingEdges
            fromVertex = self.vertex(edge.fromVertex())
            for edgeIdx in range(len(fromVertex.mOutgoingEdges)):
                if fromVertex.mOutgoingEdges[edgeIdx] == idx:
                    fromVertex.mOutgoingEdges.pop(edgeIdx)
                    break

            del self.mEdges[idx]
            self.__availableEdgeIndices.append(idx)
            self.mEdgeCount -= 1
            return True
        return False

    def deleteVertex(self, idx):
        """
        Deletes a vertex and all outgoing and incoming edges of this vertex

        :type idx: Integer, index of vertex to delete
        :return list with indices of all edges deleted (may be empty)

        """
        deletedEdges = []
        if idx in self.mVertices:
            vertex = self.mVertices[idx]
            # delete all incoming edges vertex is connected with
            for id in range(len(vertex.incomingEdges())):
                edgeIdx = vertex.incomingEdges().pop(0)
                self.deleteEdge(edgeIdx)
                deletedEdges.append(edgeIdx)
            vertex.mIncomingEdges = []
            # delete all outgoing edges vertex is connected with
            for id in range(len(vertex.outgoingEdges())):
                edgeIdx = vertex.outgoingEdges().pop(0)
                self.deleteEdge(edgeIdx)
                deletedEdges.append(edgeIdx)
            vertex.mOutgoingEdges = []
            
            del self.mVertices[idx]
            self.__availableVertexIndices.append(idx)
            self.mVertexCount -= 1
            
        return deletedEdges
            

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
        
        for i in self.mVertices:
            nodeLine = '\t\t<node id="' + str(i) + '"/>\n'
            file.write(nodeLine) 
            file.write('\t\t\t<data key="d1">\n')
            file.write('\t\t\t\t<y:ShapeNode>\n')
            coordinates = '\t\t\t\t\t<y:Geometry height="30.0" width="30.0" x="' + str(self.vertex(i).point().x()) + '" y="' + str(self.vertex(i).point().y()) + '"/>\n'
            file.write(coordinates)
            file.write('\t\t\t\t</y:ShapeNode>\n')
            file.write('\t\t\t</data>\n')
        
        for i in self.mEdges:
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
