from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

from qgis.PyQt.QtCore import QObject

import math, sys
from random import *

from ..lib.kdtree import kdtree

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
        def __init__(self, point, id):
            self.mCoordinates = point
            self.mIncomingEdges = []
            self.mOutgoingEdges = []
            self.mID = id

        def __del__(self):
            del self.mCoordinates
            del self.mIncomingEdges
            del self.mOutgoingEdges

        def calculateSize(self):
            size = 0

            size += sys.getsizeof(self.mCoordinates)
            size += sys.getsizeof(self.mIncomingEdges)
            size += sys.getsizeof(self.mOutgoingEdges)
            size += sys.getsizeof(self.mID)

            return size

        def id(self):
            return self.mID

        def setClusterID(self, clusterID):
            self.mClusterID = clusterID

        def clusterID(self):
            if hasattr(self, "mClusterID"):
                return self.mClusterID
            return -1

        def incomingEdges(self):
            return self.mIncomingEdges

        def outgoingEdges(self):
            return self.mOutgoingEdges

        def point(self):
            return self.mCoordinates

        def setNewPoint(self, point):
            self.mCoordinates = point

    #==ExtEdge=======================================================================
    class ExtEdge:
        """
        Inner class representing an edge of the ExtGraph
        """
        def __init__(self, fromVertexID, toVertexID, id, highlighted=False):
            self.mFromID = fromVertexID
            self.mToID = toVertexID
            self.mID = id

            # highlights used for marked edges by a server response
            self.isHighlighted = highlighted

        def __del__(self):
            pass

        def calculateSize(self):
            size = 0

            size += sys.getsizeof(self.mFromID)
            size += sys.getsizeof(self.mToID)
            size += sys.getsizeof(self.mID)
            size += sys.getsizeof(self.isHighlighted)

            return size
        
        def id(self):
            return self.mID

        def fromVertex(self):
            return self.mFromID

        def toVertex(self):
            return self.mToID

        def highlighted(self):
            return self.isHighlighted

        def toggleHighlight(self):
            self.isHighlighted = not self.isHighlighted

    #==ExtGraph Methods===============================================================
    def __init__(self):
        super().__init__()
        self.distanceStrategy = "Euclidean"
        self.mConnectionType = "None"
        self.edgeWeights = []
        self.vertexWeights = []
        self.crs = None

        self.mVertices = []
        self.mEdges = []

        # Set to true while building the graph to indicate that the arrays are
        # sorted by uid, so binary search is possible
        # TODO default value
        self.verticesSorted = True
        self.edgesSorted = True

        self.mEdgeCount = 0
        self.mVertexCount = 0

        # next useable IDs for vertices and edges
        self.mMaxEdgeID = 0
        self.mMaxVertexID = 0

        # holds the feature IDs if lines where used to create graph
        self.featureMatchings = []

        # default information from GraphBuilder
        self.numberNeighbours = 20
        self.edgeDirection = "Directed"
        self.clusterNumber = 5
        self.nnAllowDoubleEdges = True
        self.distance = 0

        self.kdTree = None

        self.mJobId = -1

    def __del__(self):
        del self.edgeWeights
        del self.vertexWeights

        for idx in range(self.mVertexCount - 1, -1, -1):
            del self.mVertices[idx]

        for idx in range(self.mEdgeCount - 1, -1, -1):
            del self.mEdges[idx]

        del self.mVertices
        del self.mEdges

        if self.kdTree:
            del self.kdTree

        del self.featureMatchings

    def calculateSize(self):
        size = 0

        verticesSize = 0
        for idx in range(self.mVertexCount):
            verticesSize += self.mVertices[idx].calculateSize()
        size += verticesSize
        size += sys.getsizeof(self.mVertices)

        edgesSize = 0
        for idx in range(self.mEdgeCount):
            edgesSize += self.mEdges[idx].calculateSize()
        size += edgesSize
        size += sys.getsizeof(self.mEdges)

        size += sys.getsizeof(self.distanceStrategy)
        size += sys.getsizeof(self.mConnectionType)
        size += sys.getsizeof(self.edgeWeights)
        size += sys.getsizeof(self.vertexWeights)

        size += sys.getsizeof(self.verticesSorted)
        size += sys.getsizeof(self.edgesSorted)
        size += sys.getsizeof(self.mEdgeCount)
        size += sys.getsizeof(self.mVertexCount)

        size += sys.getsizeof(self.mMaxEdgeID)
        size += sys.getsizeof(self.mMaxVertexID)

        size += sys.getsizeof(self.featureMatchings)

        size += sys.getsizeof(self.numberNeighbours)
        size += sys.getsizeof(self.edgeDirection)
        size += sys.getsizeof(self.clusterNumber)
        size += sys.getsizeof(self.nnAllowDoubleEdges)
        size += sys.getsizeof(self.distance)

        size += sys.getsizeof(self.kdTree)

        size += sys.getsizeof(self.mJobId)

        file = open("ArraySize.txt", "a")
        sizeString = str(self.mVertexCount) + ";" + str(size/1000000) + "\n"
        file.write(sizeString)

        file.close()

        # print("VC: ", self.mVertexCount, ", EC: ", self.mEdgeCount, "\nComplete: ", size/1000000, ", Vertices: ", verticesSize/1000000, ", Edges: ", edgesSize/1000000)

    def setJobID(self, jobId):
        self.mJobId = jobId

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

    def setGraphBuilderInformation(self, numberNeighbours, edgeDirection, clusterNumber, nnAllowDoubleEdges, distance):
        self.numberNeighbours = numberNeighbours
        self.edgeDirection = edgeDirection
        self.clusterNumber = clusterNumber
        self.nnAllowDoubleEdges = nnAllowDoubleEdges
        self.distance = distance

    def setNextClusterID(self, nextClusterID):
        self.mNextClusterID = nextClusterID

    def nextClusterID(self):
        if hasattr(self, "mNextClusterID"):
            return self.mNextClusterID
        return -1

    def amountOfEdgeCostFunctions(self):
        return len(self.edgeWeights)

    def setCostOfEdge(self, edgeIdx, functionIndex, cost):
        """
        Set cost of a specific edge.

        :type functionIndex: Integer
        :type edgeIdx: Integer
        :type cost: Integer
        """
        while len(self.edgeWeights) <= functionIndex:
            self.edgeWeights.append([])

        while len(self.edgeWeights[functionIndex]) <= edgeIdx:
            self.edgeWeights[functionIndex].append(-1)

        self.edgeWeights[functionIndex][edgeIdx] = cost

    def costOfEdge(self, edgeIdx, functionIndex = 0):
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
            return self.euclideanDist(edgeIdx)

        elif self.distanceStrategy == "Manhattan":
            return self.manhattanDist(edgeIdx)

        # calculate geodesic distance using the Haversine formula
        elif self.distanceStrategy == "Geodesic":
            return self.geodesicDist(edgeIdx)

        elif self.distanceStrategy == "Ellipsoidal":
            return self.ellipsoidalDist(edgeIdx)

        #if the type is advanced the distances are set by the GraphBuilder directly
        elif self.distanceStrategy == "Advanced":
            # here edgeID is actually only edgeIdx
            if len(self.edgeWeights) <= functionIndex or len(self.edgeWeights[functionIndex]) <= edgeIdx:
                return 0
            return self.edgeWeights[functionIndex][edgeIdx]

        elif self.distanceStrategy == "None":
            return None
        else:
            print("DistanceStrategy: ", self.distanceStrategy)
            raise NameError("Unknown distance strategy")


    def ellipsoidalDist(self, edgeIdx):
        edgeFromIdx = self.edge(edgeIdx)
        fromPoint = self.vertex(self.findVertexByID(edgeFromIdx.fromVertex())).point()
        toPoint = self.vertex(self.findVertexByID(edgeFromIdx.toVertex())).point()
        distArea = QgsDistanceArea()
        distArea.setEllipsoid(self.crs.ellipsoidAcronym())
        return distArea.measureLine(fromPoint, toPoint)

    def euclideanDist(self, edgeIdx):
        edgeFromIdx = self.edge(edgeIdx)
        fromPoint = self.vertex(self.findVertexByID(edgeFromIdx.fromVertex())).point()
        toPoint = self.vertex(self.findVertexByID(edgeFromIdx.toVertex())).point()
        euclDist = math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))
        return euclDist

    def manhattanDist(self, edgeIdx):
        edgeFromIdx = self.edge(edgeIdx)
        fromPoint = self.vertex(self.findVertexByID(edgeFromIdx.fromVertex())).point()
        toPoint = self.vertex(self.findVertexByID(edgeFromIdx.toVertex())).point()
        manhattenDist = abs(fromPoint.x()-toPoint.x()) + abs(fromPoint.y()-toPoint.y())
        return manhattenDist

    def geodesicDist(self, edgeIdx):
        edgeFromIdx = self.edge(edgeIdx)
        fromPoint = self.vertex(self.findVertexByID(edgeFromIdx.fromVertex())).point()
        toPoint = self.vertex(self.findVertexByID(edgeFromIdx.toVertex())).point()
        radius = 6371000
        phi1 = math.radians(fromPoint.y())
        phi2 = math.radians(toPoint.y())
        deltaPhi = math.radians(toPoint.y()-fromPoint.y())
        deltaLambda = math.radians(toPoint.x()-fromPoint.x())
        a = math.sin(deltaPhi/2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(deltaLambda / 2.0) ** 2
        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        return radius*c

    def distanceP2P(self, vertex1Idx, vertex2Idx):
        """
        Method to get the euclidean distance between two vertices

        :type vertex1Idx: Integer
        :type vertex2Idx: Integer
        :return distance between vertices
        """
        fromPoint = self.vertex(vertex1Idx).point()
        toPoint = self.vertex(vertex2Idx).point()
        return math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))


    def hasEdge(self, vertex1Idx, vertex2Idx):
        """
        Method searches for the edge between to vertices

        :type vertex1Idx: Integer
        :type vertex2Idx: Integer
        :return Integer found edgeIdx, else -1
        """
        vertex1ID = self.vertex(vertex1Idx).id()
        vertex2ID = self.vertex(vertex2Idx).id()

        for edgeIdx in self.vertex(vertex1Idx).outgoingEdges():
            edge = self.mEdges[edgeIdx]

            if edge.fromVertex() == vertex1ID and edge.toVertex() == vertex2ID:
                return edgeIdx

        if self.edgeDirection == "Undirected":
            for edgeIdx in self.vertex(vertex1Idx).incomingEdges():
                edge = self.mEdges[edgeIdx]

                if edge.fromVertex() == vertex2ID and edge.toVertex() == vertex1ID:
                    return edgeIdx
        return -1

    def findVertexByID(self, id, output=False):
        """
        Start search for vertex with id

        :type id: Integer
        :return Integer idx for found vertex with id
        """
        if id < self.mVertexCount and self.mVertices[id].id() == id:
            # without much editing, this should be the case
            return id
        
        if self.verticesSorted:
            return self.__binaryVertexByID(id, 0, self.mVertexCount - 1)
        else:
            return self.__linearVertexByID(id)
    
    def __linearVertexByID(self, id):
        for idx, vertex in enumerate(self.mVertices):
            if vertex.id() == id:
                return idx
        return -1

    def __binaryVertexByID(self, id, left, right):
        if left > right:
            return -1
        
        mid = math.floor((left + right) / 2)

        midID = self.mVertices[mid].id()
        if id == midID:
            return mid
        elif id > midID:
            return self.__binaryVertexByID(id, mid + 1, right)
        else:
            return self.__binaryVertexByID(id, left, mid - 1)

    def findEdgeByID(self, id):
        """
        Start search for edge with id

        :type id: Integer
        :return Integer idx for found edge with id
        """
        if id < self.mEdgeCount and self.mEdges[id].id() == id:
            # without much editing, this should be the case
            return id

        if self.edgesSorted:
            return self.__binaryEdgeByID(id, 0, self.mEdgeCount - 1)
        else:
            return self.__linearEdgeByID(id)
    
    def __linearEdgeByID(self, id):
        for idx, edge in enumerate(self.mEdges):
            if edge.id() == id:
                return idx
        return -1

    def __binaryEdgeByID(self, id, left, right):
        if left > right:
            return -1
        
        mid = math.floor((left + right) / 2)

        midID = self.mEdges[mid].id()
        if id == midID:
            return mid
        elif id > midID:
            return self.__binaryEdgeByID(id, mid + 1, right)
        else:
            return self.__binaryEdgeByID(id, left, mid - 1)

    def findVertex(self, vertex, tolerance=0):
        """
        Modified findVertex function to find a vertex within a tolerance square

        :type vertex: QgsPointXY
        :type tolerance: int
        :return vertexId: Integer
        """
        if tolerance > 0:
            toleranceRect = QgsRectangle.fromCenterAndSize(vertex, tolerance, tolerance)

        for idx in range(self.mVertexCount):
            checkVertex = self.vertex(idx)

            if tolerance == 0 and checkVertex.point() == vertex:
                return idx
            elif tolerance > 0 and toleranceRect.contains(checkVertex.point()):
                return idx

        return -1
    
    def nextEdgeID(self):
        return self.mMaxEdgeID

    def addEdge(self, vertex1ID, vertex2ID, idx=-1, ID=-1, highlighted=False):
        """
        Adds an edge with fromVertex vertex1 and toVertex2 to the ExtGraph

        :type vertex1ID: Integer
        :type vertex2ID: Integer
        :type idx: Integer add Edge with index idx, default -1 to be used, non-default only used by QUndoCommands
        :type ID: Integer EdgeID
        :type highlightd: Bool
        :return Integer index of added edge
        """
        addIndex = self.mEdgeCount
        if idx >= 0:
            # mostly used by UndoCommands to maintain correct order of edges, enables binary search for ID
            addIndex = idx

        addedEdgeID = ID
        if ID < 0:
            addedEdgeID = self.mMaxEdgeID
            self.mMaxEdgeID += 1

        if addedEdgeID >= self.mMaxEdgeID:
            self.mMaxEdgeID = addedEdgeID + 1
        
        addedEdge = self.ExtEdge(vertex1ID, vertex2ID, addedEdgeID, highlighted)

        self.mEdges.insert(addIndex, addedEdge)

        # add entries for edgeWeights at the correct idx
        for functionIdx in range(len(self.edgeWeights)):
            # add default value 0
            self.edgeWeights[functionIdx].insert(addIndex, 0)
        
        # register edge on from- and toVertices
        self.mVertices[self.findVertexByID(vertex1ID)].mOutgoingEdges.append(addedEdge.id())
        self.mVertices[self.findVertexByID(vertex2ID)].mIncomingEdges.append(addedEdge.id())
        
        self.mEdgeCount += 1

        return addIndex

    def nextVertexID(self):
        return self.mMaxVertexID

    def addVertex(self, point, idx=-1, ID=-1):
        """
        Adds a vertex with coordinates point to ExtGraph

        :type point: QgsPointXY
        :type idx: Integer add Vertex with index idx, default -1 to be used, non-default only used by QUndoCommands
        :type ID: Integer VertexID
        :return Integer index of added edge
        """
        addIndex = self.mVertexCount
        if idx >= 0:
            addIndex = idx

        addedVertexID = ID
        if ID < 0:
            addedVertexID = self.mMaxVertexID
            self.mMaxVertexID += 1

        if addedVertexID >= self.mMaxVertexID:
            self.mMaxVertexID = addedVertexID + 1

        self.mVertices.insert(addIndex, self.ExtVertex(point, addedVertexID))

        if hasattr(self, "mNextClusterID"):
            self.mVertices[addIndex].setClusterID(self.mNextClusterID)
            self.mNextClusterID += 1

        # TODO: add entry in vertexWeights if used later

        self.mVertexCount += 1

        return addIndex

    def addVertexWithEdges(self, vertexCoordinates, fromUndo=False):
        """
        Methods adds the point given by its coordinates to the
        graph attribute of the Graphbuilder. Get the modified
        ExtGraph object by using the getGraph() method.

        :type vertexCoordinates: list with x,y-Coordinates
        :return list of edges
        """
        if not self.kdTree:
            points = []
            for idx in range(self.mVertexCount):
                point = self.vertex(idx).point()
                points.append([point.x(),point.y()])

            self.kdTree = kdtree.create(points)

        listOfEdges = []
        numberOfEdgesOriginal = self.edgeCount()
        index = self.addVertex(QgsPointXY(vertexCoordinates[0], vertexCoordinates[1]))
        addedVertexID = self.vertex(index).id()
        point = self.vertex(index).point()
        if self.mConnectionType == "Complete":
            for vertexIdx in range(self.mVertexCount):
                vertexID = self.vertex(vertexIdx).id()
                if not fromUndo:
                    edgeIdx = self.addEdge(vertexID, addedVertexID)
                else:
                    edgeIdx = self.edgeCount() + len(listOfEdges)
                listOfEdges.append([edgeIdx, vertexID, addedVertexID])

        #== NEAREST NEIGHBOR & DISTANCENN =========================================================
        elif self.mConnectionType == "Nearest neighbor" or self.mConnectionType == "DistanceNN":
            # if this is True the nodes got deleted
            if not self.nnAllowDoubleEdges:
                points = []
                for idx in range(self.mVertexCount):
                    p = self.vertex(idx).point()
                    points.append([p.x(),p.y()])
                self.kdTree = kdtree.create(points)

            else:
                self.kdTree.add([point.x(),point.y()])

            if self.mConnectionType == "Nearest neighbor":
                listOfNeighbors = self.kdTree.search_knn([point.x(),point.y()], self.numberNeighbours+1)
                rangeStart = 1
                rangeEnd = len(listOfNeighbors)
            elif self.mConnectionType == "DistanceNN":
                listOfNeighbors = self.kdTree.search_nn_dist([point.x(),point.y()], pow(self.distance,2))
                rangeStart = 0
                rangeEnd = len(listOfNeighbors)-1

            for j in range(rangeStart,rangeEnd):
                if self.mConnectionType == "Nearest neighbor":
                    neighborPoint = listOfNeighbors[j][0].data
                elif self.mConnectionType == "DistanceNN":
                    neighborPoint = listOfNeighbors[j]

                neighborID = self.vertex(self.findVertex(QgsPointXY(neighborPoint[0], neighborPoint[1]))).id()
                if not fromUndo:
                    edgeIdx = self.addEdge(addedVertexID, neighborID)
                else:
                    edgeIdx = self.edgeCount() + len(listOfEdges)
                listOfEdges.append([edgeIdx, addedVertexID, neighborID])
                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        edgeIdx = self.addEdge(addedVertexID, neighborID)
                    else:
                        edgeIdx = self.edgeCount() + len(listOfEdges)
                    listOfEdges.append([edgeIdx, neighborID, addedVertexID])

        #== CLUSTER COMPLETE ======================================================================
        elif self.mConnectionType == "ClusterComplete":

            # search nearest point
            neighborPoint = self.kdTree.search_knn([point.x(),point.y()], 1)
            neighborPointIdx = self.findVertex(QgsPointXY(neighborPoint[0][0].data[0], neighborPoint[0][0].data[1]))
            neighborVertex = self.vertex(neighborPointIdx)

            # add an edge to all the neighbors of the found nearest point
            for edgeID in neighborVertex.incomingEdges():
                edge = self.edge(self.findEdgeByID(edgeID))
                
                if not fromUndo:
                    addedEdgeIdx = self.addEdge(edge.fromVertex(), addedVertexID)
                else:
                    addedEdgeIdx = self.edgeCount() + len(listOfEdges)
                listOfEdges.append([addedEdgeIdx, edge.fromVertex(), addedVertexID])

                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        addedEdgeIdx = self.addEdge(addedVertexID, edge.fromVertex())
                    else:
                        addedEdgeIdx = self.edgeCount() + len(listOfEdges)
                    listOfEdges.append([addedEdgeIdx, addedVertexID, edge.fromVertex()])
            
            for edgeID in neighborVertex.outgoingEdges():
                edge = self.edge(self.findEdgeByID(edgeID))

                if not fromUndo:
                    addedEdgeIdx = self.addEdge(addedVertexID, edge.toVertex())
                else:
                    addedEdgeIdx = self.edgeCount() + len(listOfEdges)
                listOfEdges.append([addedEdgeIdx, addedVertexID, edge.toVertex()])

                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        addedEdgeIdx = self.addEdge(edge.toVertex(), addedVertexID)
                    else:
                        addedEdgeIdx = self.edgeCount() + len(listOfEdges)
                    listOfEdges.append([addedEdgeIdx, edge.toVertex(), addedVertexID])

            if not fromUndo:
                addedEdgeIdx = self.addEdge(neighborVertex.id(), addedVertexID)
            else:
                addedEdgeIdx = self.edgeCount() + len(listOfEdges)
            listOfEdges.append([addedEdgeIdx, neighborVertex.id(), addedVertexID])

            if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        addedEdgeIdx = self.addEdge(addedVertexID, neighborVertex.id())
                    else:
                        addedEdgeIdx = self.edgeCount() + len(listOfEdges)
                    listOfEdges.append([addedEdgeIdx, addedVertexID, neighborVertex.id()])

        #== CLUSTERNN =============================================================================
        elif self.mConnectionType == "ClusterNN":

            # search nearest point
            neighborPoint = self.kdTree.search_knn([point.x(),point.y()], 1)
            neighborPointIdx = self.findVertex(QgsPointXY(neighborPoint[0][0].data[0], neighborPoint[0][0].data[1]))
            neighborVertex = self.vertex(neighborPointIdx)
            neighborClusterID = neighborVertex.clusterID()

            self.vertex(index).setClusterID(neighborClusterID)

            #create kdtree with all the nodes from the same cluster
            points = []
            for vertexIdx in range(self.vertexCount()):
                vertex = self.vertex(vertexIdx)
                if vertex.clusterID() == neighborClusterID:
                    points.append([vertex.point().x(), vertex.point().y(), vertexIdx])

            clusterKDTree = kdtree.create(points)

            listOfNeighbors = clusterKDTree.search_knn([point.x(),point.y(), index], self.numberNeighbours + 1)
            for j in range(len(listOfNeighbors)):
                neighborPointIdx = self.findVertex(QgsPointXY(listOfNeighbors[j][0].data[0], listOfNeighbors[j][0].data[1]))
                neighborVertexID = self.vertex(neighborPointIdx).id()

                if not fromUndo:
                    edgeIdx = self.addEdge(addedVertexID, neighborVertexID)
                else:
                    edgeIdx = self.edgeCount() + len(listOfEdges)
                listOfEdges.append([edgeIdx, addedVertexID, neighborVertexID])
                
                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        edgeIdx = self.addEdge(addedVertexID, neighborVertexID)
                    else:
                        edgeIdx = self.edgeCount() + len(listOfEdges)
                    listOfEdges.append([edgeIdx, neighborVertexID, addedVertexID])

        return listOfEdges

    def edge(self, idx):
        if idx < 0 or idx >= self.mEdgeCount:
            raise IndexError(f"Edge index {idx} is out of bounds")
        return self.mEdges[idx]

    def edgeCount(self):
        return self.mEdgeCount

    def vertex(self, idx):
        if idx < 0 or idx >= self.mVertexCount:
            raise IndexError(f"Vertex index {idx} is out of bounds")
        return self.mVertices[idx]

    def vertexCount(self):
        return self.mVertexCount

    def vertices(self):
        return self.mVertices

    def edges(self):
        return self.mEdges

    def deleteEdge(self, idx):
        """
        Deletes an edge

        :type idx: Integer, index of edge to delete
        :return Bool
        """
        if idx < self.mEdgeCount:
            edge = self.mEdges[idx]
            edgeID = edge.id()

            # remove edge from toVertex incomingEdges
            toVertexIdx = self.findVertexByID(edge.toVertex())
            if not toVertexIdx == -1:
                toVertex = self.vertex(toVertexIdx)
                for edgeIdx in range(len(toVertex.mIncomingEdges)):
                    if toVertex.mIncomingEdges[edgeIdx] == edgeID:
                        toVertex.mIncomingEdges.pop(edgeIdx)
                        break
            
            # remove edge from fromVertex outgoingEdges
            fromVertexIdx = self.findVertexByID(edge.fromVertex())
            if not fromVertexIdx == -1:
                fromVertex = self.vertex(fromVertexIdx)
                for edgeIdx in range(len(fromVertex.mOutgoingEdges)):
                    if fromVertex.mOutgoingEdges[edgeIdx] == edgeID:
                        fromVertex.mOutgoingEdges.pop(edgeIdx)
                        break

            del self.mEdges[idx]
            
            # also remove entries from edgeWeights
            for functionIdx in range(len(self.edgeWeights)):
                del self.edgeWeights[functionIdx][idx]

            self.mEdgeCount -= 1
            return True
        return False

    def deleteVertex(self, idx, fromUndo=False):
        """
        Deletes a vertex and all outgoing and incoming edges of this vertex

        :type idx: Integer, index of vertex to delete
        :type fromUndo: Bool non-default only used by QUndoCommand
        :return list with ids of all edges deleted (may be empty)

        """
        deletedEdgeIDs = []
        if idx < self.mVertexCount:
            vertex = self.mVertices[idx]

            # delete all incoming edges vertex is connected with
            for incomingIdx in range(len(vertex.incomingEdges())):
                edgeID = vertex.incomingEdges().pop(0)
                deletedEdgeIDs.append(edgeID)
            vertex.mIncomingEdges = []
            
            # delete all outgoing edges vertex is connected with
            for outgoingIdx in range(len(vertex.outgoingEdges())):
                edgeID = vertex.outgoingEdges().pop(0)
                deletedEdgeIDs.append(edgeID)
            vertex.mOutgoingEdges = []

            del self.mVertices[idx]
            self.mVertexCount -= 1

            # TODO: remove entries from vertexWeights if used later

            if not fromUndo:
                # undoCommand creates deleteEdgeCommands on its own and append it to the deleteVertexCommand
                for id in deletedEdgeIDs:
                    self.deleteEdge(self.findEdgeByID(id))

        return deletedEdgeIDs


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

        for idx in range(self.mVertexCount):
            vertex = self.vertex(idx)
            nodeLine = '\t\t<node id="' + str(vertex.id()) + '"/>\n'
            file.write(nodeLine)
            file.write('\t\t\t<data key="d1">\n')
            file.write('\t\t\t\t<y:ShapeNode>\n')
            coordinates = '\t\t\t\t\t<y:Geometry height="30.0" width="30.0" x="' + str(vertex.point().x()) + '" y="' + str(vertex.point().y()) + '"/>\n'
            file.write(coordinates)
            file.write('\t\t\t\t</y:ShapeNode>\n')
            file.write('\t\t\t</data>\n')

        for idx in range(self.mEdgeCount):
            edge = self.edge(idx)
            edgeLine = '\t\t<edge source="' + str(edge.fromVertex()) + '" target="' + str(edge.toVertex()) + '"/>\n'
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
            vertexIDCount = 0
            for line in lines:
                if '<node' in line:
                    nodeIDs.append(line.split('id="')[1].split('"')[0])

                elif 'x="' in line:
                    xValue = float(line.split('x="')[1].split(' ')[0].split('"')[0])
                    yValue = float(line.split('y="')[1].split(' ')[0].split('"')[0])
                    
                    # add vertex with correct coordinates and ID
                    self.addVertex(QgsPointXY(xValue, yValue), -1, nodeIDs[vertexIDCount])
                    vertexIDCount += 1

                elif '<edge' in line:
                    fromVertex = line.split('source="')[1].split('"')[0]
                    toVertex = line.split('target="')[1].split('"')[0]
                    # fromVertexID = 0
                    # toVertexID = 0

                    # for i in range(len(nodeIDs)):
                    #     if nodeIDs[i] == fromVertex:
                    #         fromVertexID = i
                    #     elif nodeIDs[i] == toVertex:
                    #         toVertexID = i

                    # self.addEdge(fromVertexID, toVertexID)
                    # if edgeTypeDirection == "Undirected":
                    #     self.addEdge(toVertexID, fromVertexID)

                    self.addEdge(fromVertex, toVertex)
                    if edgeTypeDirection == "Undirected":
                        # TODO: direction in graph and hasEdge
                        self.addEdge(toVertex, fromVertex)

        # if no coordinates are given assign random
        else:
            vertexIDCount = 0
            for line in lines:
                if '<node' in line:
                    nodeIDs.append(line.split('id="')[1].split('"')[0])
                    
                    # add vertex with random coordinates and correct ID
                    self.addVertex(QgsPointXY(randrange(742723,1534455), randrange(6030995,7314884), -1, nodeIDs[vertexIDCount]))
                    vertexIDCount += 1

                elif '<edge' in line:
                    fromVertex = line.split('source="')[1].split('"')[0]
                    toVertex = line.split('target="')[1].split('"')[0]
                    # fromVertexID = 0
                    # toVertexID = 0

                    # for i in range(len(nodeIDs)):
                    #     if nodeIDs[i] == fromVertex:
                    #         fromVertexID = i
                    #     elif nodeIDs[i] == toVertex:
                    #         toVertexID = i
                    # self.addEdge(fromVertexID, toVertexID)
                    
                    self.addEdge(fromVertex, toVertex)
                    if edgeTypeDirection == "Undirected":
                        # TODO: direction in graph and hasEdge
                        self.addEdge(toVertex, fromVertex)
