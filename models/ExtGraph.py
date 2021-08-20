from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

from qgis.PyQt.QtCore import QObject

import math
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
        def __init__(self, point):
            self.mCoordinates = point
            self.mIncomingEdges = []
            self.mOutgoingEdges = []

        def __del__(self):
            # print("Delete Vertex")
            del self.mCoordinates
            del self.mIncomingEdges
            del self.mOutgoingEdges

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
        def __init__(self, fromVertexIdx, toVertexIdx, highlighted=False):
            # TODO: add costs list for an edge here?
            self.mFromIdx = fromVertexIdx
            self.mToIdx = toVertexIdx

            # highlights used for marked edges by a server response
            self.isHighlighted = highlighted

        def __del__(self):
            # print("Delete Edge")
            pass

        def fromVertex(self):
            return self.mFromIdx

        def toVertex(self):
            return self.mToIdx

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

        self.mVertices = {}
        self.mEdges = {}

        self.mEdgeCount = 0
        self.mVertexCount = 0

        self.availableVertexIndices =[]
        self.availableEdgeIndices = []

        # holds the feature IDs if lines where used to create graph
        self.featureMatchings = []

        # information from GraphBuilder
        self.numberNeighbours = 20
        self.edgeDirection = "Directed"
        self.clusterNumber = 5
        self.nnAllowDoubleEdges = True
        self.distance = 0

        self.kdTree = None

        self.mJobId = -1

    def __del__(self):
        # print("Delete Graph", self.mVertexCount, self.mEdgeCount)
        del self.edgeWeights
        del self.vertexWeights

        for idx in list(self.mVertices):
            del self.mVertices[idx]

        for idx in list(self.mEdges):
            del self.mEdges[idx]

        del self.mVertices
        del self.mEdges

        del self.availableVertexIndices
        del self.availableEdgeIndices

        if self.kdTree:
            del self.kdTree

        del self.featureMatchings

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

    def setGraphBuilderInformation(self, numberNeighbours, edgeDirection, clusterNumber, nnAllowDoubleEgdes, distance):
        self.numberNeighbours = numberNeighbours
        self.edgeDirection = edgeDirection
        self.clusterNumber = clusterNumber
        self.nnAllowDoubleEdges = nnAllowDoubleEgdes
        self.distance = distance

    def amountOfEdgeCostFunctions(self):
        return len(self.edgeWeights)

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

        elif self.distanceStrategy == "Ellipsoidal":
            return self.ellipsoidalDist(edgeID)

        #if the type is advanced the distances are set by the GraphBuilder directly
        elif self.distanceStrategy == "Advanced":
            if len(self.edgeWeights) <= functionIndex or len(self.edgeWeights[functionIndex]) <= edgeID:
                return 0
            return self.edgeWeights[functionIndex][edgeID]

        elif self.distanceStrategy == "None":
            return None
        else:
            print("DistanceStrategy: ", self.distanceStrategy)
            raise NameError("Unknown distance strategy")


    def ellipsoidalDist(self, edgeID):
        edgeFromID = self.edge(edgeID)
        fromPoint = self.vertex(edgeFromID.fromVertex()).point()
        toPoint = self.vertex(edgeFromID.toVertex()).point()
        distArea = QgsDistanceArea()
        distArea.setEllipsoid(self.crs.ellipsoidAcronym())
        return distArea.measureLine(fromPoint, toPoint)

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
        for edgeIdx in self.vertex(vertex1).outgoingEdges():
            edge = self.mEdges[edgeIdx]
            if edge.fromVertex() == vertex1 and edge.toVertex() == vertex2:
                return edgeIdx

        return -1

    def addEdge(self, vertex1, vertex2, idx=-1, highlighted=False):
        """
        Adds an edge with fromVertex vertex1 and toVertex2 to the ExtGraph

        :type vertex1: Integer
        :type vertex2: Integer
        :type idx: Integer add Edge with index idx, -1 if no custom index should be set
        :type highlighted: Bool if the edge should be highlighted in the rendering process
        :return Integer index of added edge
        """
        addIndex = self.mEdgeCount
        if idx >= 0:
            addIndex = idx
        elif len(self.availableEdgeIndices) > 0:
            # check if other indices are available due to earlier delete
            addIndex = self.availableEdgeIndices.pop(0)

        self.mEdges[addIndex] = self.ExtEdge(vertex1, vertex2, highlighted)
        self.mVertices[vertex1].mOutgoingEdges.append(addIndex)
        self.mVertices[vertex2].mIncomingEdges.append(addIndex)
        self.mEdgeCount += 1

        return addIndex

    def addVertex(self, point, idx=-1):
        addIndex = self.mVertexCount
        if idx >= 0:
            addIndex = idx
        elif len(self.availableVertexIndices) > 0:
            # check if other indices are available due to earlier delete
            addIndex = self.availableVertexIndices.pop(0)

        self.mVertices[addIndex] = self.ExtVertex(point)
        self.mVertexCount += 1

        return addIndex

    def addVertexWithEdges(self, vertexCoordinates):
        """
        Methods adds the point given by its coordinates to the
        graph attribute of the Graphbuilder. Get the modified
        ExtGraph object by using the getGraph() method.

        :type vertexCoordinates: list with x,y-Coordinates
        :return list of edges
        """
        if not self.kdTree:
            points = []
            for i in self.vertices():
                point = self.vertex(i).point()
                points.append([point.x(),point.y()])

            self.kdTree = kdtree.create(points)

        listOfEdges = []
        addedEdgeIndices = []
        numberOfEdgesOriginal = self.edgeCount()
        index = self.addVertex(QgsPointXY(vertexCoordinates[0], vertexCoordinates[1]))
        point = self.vertex(index).point()
        if self.mConnectionType == "Complete":
            for i in self.vertices():
                edgeId = self.addEdge(i, index)
                addedEdgeIndices.append(edgeId)
                listOfEdges.append([edgeId, i,index])
                if self.edgeDirection == "Undirected":
                    edgeId = self.addEdge(i, index)
                    addedEdgeIndices.append(edgeId)
                    listOfEdges.append([edgeId, i,index])

        elif self.mConnectionType == "Nearest neighbor" or self.mConnectionType == "DistanceNN":
            # if this is True the nodes got deleted
            if self.nnAllowDoubleEdges == False:
                points = []
                for i in self.vertices():
                    p = self.vertex(i).point()
                    points.append([p.x(),p.y()])
                self.kdTree = kdtree.create(points)

            else:
                self.kdTree.add([point.x(),point.y()])

            if self.mConnectionType == "Nearest neighbor":
                listOfNeighbors = self.kdTree.search_knn([point.x(),point.y()],self.numberNeighbours+1)
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

                edgeId = self.addEdge(index,neighborPoint[2])
                addedEdgeIndices.append(edgeId)
                listOfEdges.append([edgeId, index,neighborPoint[2]])
                if self.edgeDirection == "Undirected" or self.nnAllowDoubleEdges == True:
                    edgeId = self.addEdge(neighborPoint[2], index)
                    addedEdgeIndices.append(edgeId)
                    listOfEdges.append([edgeId, neighborPoint[2],index])

        elif self.mConnectionType == "ClusterComplete":
            print("addVertexWithEdges not yet supported for ClusterComplete")
            return

            # # search nearest point
            # neighborPoint = self.getNearestVertex(index)

            # # add an edge to all the neighbors of the found nearest point
            # for i in self.edges():
            #     edge = self.edge(i)
            #     if edge.toVertex() == neighborPoint:
            #         edgeId = self.addEdge(edge.fromVertex(), index)
            #         addedEdgeIndices.append(edgeId)
            #         listOfEdges.append([edgeId, edge.fromVertex(),index])
            #     elif edge.fromVertex() == neighborPoint:
            #         edgeId = self.addEdge(edge.toVertex(), index)
            #         addedEdgeIndices.append(edgeId)
            #         listOfEdges.append([edgeId, edge.toVertex(), index])

            # edgeId = self.addEdge(neighborPoint, index)
            # addedEdgeIndices.append(edgeId)
            # listOfEdges.append([edgeId, neighborPoint, index])

        elif self.mConnectionType == "ClusterNN":
            print("addVertexWithEdges not yet supported for ClusterNN")
            return

            # # search nearest point
            # neighborPoint = self.getNearestVertex(index)
            # self.layerWithClusterIDS.selectByIds([neighborPoint])
            # for feature in self.layerWithClusterIDS.selectedFeatures():
            #     idOfNearestCluster = feature["CLUSTER_ID"]

            # self.layerWithClusterIDS.selectAll()
            # #create kdtree with all the nodes from the same cluster
            # points = []
            # counter = 0
            # for feature in self.layerWithClusterIDS.getFeatures():
            #     geom = feature.geometry()
            #     if feature["CLUSTER_ID"] == idOfNearestCluster:
            #         points.append([geom.asPoint().x(),geom.asPoint().y(),counter])
            #     counter+=1
            # clusterKDTree = kdtree.create(points)

            # listOfNeighbors = clusterKDTree.search_knn([point.x(),point.y(),index],self.numberNeighbours)
            # for j in range(len(listOfNeighbors)):
            #     neighborPoint = listOfNeighbors[j][0].data
            #     edgeId = self.addEdge(index, neighborPoint[2])
            #     addedEdgeIndices.append(edgeId)
            #     listOfEdges.append([edgeId, index, neighborPoint[2]])
            #     if self.edgeDirection == "Undirected" or self.nnAllowDoubleEdges == True:
            #         edgeId = self.addEdge(neighborPoint[2], index)
            #         addedEdgeIndices.append(edgeId)
            #         listOfEdges.append([edgeId, neighborPoint[2], index])

        # # create AdvancedCostCalculator object with the necessary parameters
        # costCalculator = AdvancedCostCalculator(self.rLayers, self.vLayer, self, self.polygonsForCostFunction, self.__options["usePolygonsAsForbidden"], self.rasterBands)

        # # call for every new edge
        # for i in range(len(addedEdgeIndices)):
        #     # call the setEdgeCosts method of the AdvancedCostCalculator for every defined cost function
        #     # the costCalculator returns a ExtGraph where costs are assigned multiple weights if more then one cost function is defined
        #     functionCounter = 0
        #     for func in self.costFunctions:
        #         self = costCalculator.setEdgeCosts(func,addedEdgeIndices[i],functionCounter)
        #         functionCounter+=1

        print(listOfEdges)
        return listOfEdges

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
            if toVertex:
                for edgeIdx in range(len(toVertex.mIncomingEdges)):
                    if toVertex.mIncomingEdges[edgeIdx] == idx:
                        toVertex.mIncomingEdges.pop(edgeIdx)
                        break
            # remove edge from fromVertex outgoingEdges
            fromVertex = self.vertex(edge.fromVertex())
            if fromVertex:
                for edgeIdx in range(len(fromVertex.mOutgoingEdges)):
                    if fromVertex.mOutgoingEdges[edgeIdx] == idx:
                        fromVertex.mOutgoingEdges.pop(edgeIdx)
                        break

            del self.mEdges[idx]
            self.availableEdgeIndices.append(idx)
            self.mEdgeCount -= 1
            return True
        return False

    def deleteVertex(self, idx, fromUndo=False):
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
                deletedEdges.append(edgeIdx)
            vertex.mIncomingEdges = []
            # delete all outgoing edges vertex is connected with
            for id in range(len(vertex.outgoingEdges())):
                edgeIdx = vertex.outgoingEdges().pop(0)
                deletedEdges.append(edgeIdx)
            vertex.mOutgoingEdges = []

            del self.mVertices[idx]
            self.availableVertexIndices.append(idx)
            self.mVertexCount -= 1

            if not fromUndo:
                # undoCommand creates deleteEdgeCommands on its own and append it to the deleteVertexCommand
                for i in deletedEdges:
                    self.deleteEdge(i)

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
