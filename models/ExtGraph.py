#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Tim Hartmann, Julian Wittker
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

from qgis.core import (QgsUnitTypes, QgsDistanceArea, QgsRectangle, QgsPointXY, QgsCoordinateTransform, QgsProject,
                       QgsCoordinateReferenceSystem, QgsWkbTypes)

from qgis.PyQt.QtCore import QObject

import math, sys
from random import randrange

from ..lib.kdtree import kdtree

"""
Extended graph class

Different metrics for distance can be defined by setting
the distanceStrategy attribute of the class.

Strategies are divided in cost functions and already set weights.

Graphediting is supported by several functions.
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

        def calculateSize(self):
            """
            Returns the calculated memory size of a vertex
            """
            size = 0

            size += sys.getsizeof(self.mCoordinates)
            size += sys.getsizeof(self.mIncomingEdges)
            size += sys.getsizeof(self.mOutgoingEdges)

            return size

        def setClusterID(self, clusterID):
            self.mClusterID = clusterID

        def clusterID(self):
            if hasattr(self, "mClusterID"):
                return self.mClusterID
            return -1

        def incomingEdges(self):
            """
            Returns all incoming edge ids
            """
            return self.mIncomingEdges

        def outgoingEdges(self):
            """
            Returns all outgoing edge ids
            """
            return self.mOutgoingEdges

        def point(self):
            return self.mCoordinates

        def setNewPoint(self, point):
            self.mCoordinates = point

        def degree(self):
            return len(self.mIncomingEdges) + len(self.mOutgoingEdges)

    #==ExtEdge=======================================================================
    class ExtEdge:
        """
        Inner class representing an edge of the ExtGraph
        """
        def __init__(self, fromVertexID, toVertexID, highlighted=False):
            self.mFromID = fromVertexID
            self.mToID = toVertexID
            self.feature = None

            # highlights used for marked edges by a server response
            self.isHighlighted = highlighted

        def __del__(self):
            pass

        def calculateSize(self):
            """
            Returns the calculated memory space of an edge
            """
            size = 0

            size += sys.getsizeof(self.mFromID)
            size += sys.getsizeof(self.mToID)
            size += sys.getsizeof(self.isHighlighted)

            return size

        def fromVertex(self):
            return self.mFromID

        def toVertex(self):
            return self.mToID

        def highlighted(self):
            return self.isHighlighted

        def toggleHighlight(self):
            self.isHighlighted = not self.isHighlighted

        def opposite(self, vertexID):
            """
            Returns the opposite of the vertexID of the edge

            :type vertexID: Integer
            :return -1 if vertexID is not attached to the edge
            """
            if self.mFromID == vertexID:
                return self.mToID
            elif self.mToID == vertexID:
                return self.mFromID

            else:
                return -1

    #==ExtGraph Methods===============================================================
    def __init__(self):
        super().__init__()
        self.distanceStrategy = "Euclidean"
        self.mConnectionType = "None"
        self.edgeWeights = []
        self.vertexWeights = []
        self.crs = None

        # dictionaries for vertices and edges
        self.mVertices = {}
        self.mEdges = {}

        self.vLayer = None
        self.lineLayerForConnection = None

        # Set to true while building the graph to indicate that the arrays are
        # sorted by id, so binary search is possible
        self.verticesSorted = True
        self.edgesSorted = True

        self.mEdgeCount = 0
        self.mVertexCount = 0

        # next useable IDs for vertices and edges
        self.mMaxEdgeID = 0
        self.mMaxVertexID = 0

        # holds the feature IDs if lines where used to create graph
        self.featureMatchings = []
        self.pointsToFeatureHash = {}

        # default information from GraphBuilder
        self.numberNeighbours = 20
        self.edgeDirection = "Directed"
        self.clusterNumber = 5
        self.nnAllowDoubleEdges = True
        self.distance = (0, QgsUnitTypes.DistanceUnknownUnit)
        self.randomSeed = None

        self.kdTree = None

        self.mJobId = -1

    def __del__(self):
        del self.edgeWeights
        del self.vertexWeights

        vertexKeys = list(self.mVertices.keys())
        for idx in range(len(vertexKeys)):
            del self.mVertices[vertexKeys[idx]]
        del vertexKeys

        edgeKeys = list(self.mEdges.keys())
        for idx in range(len(edgeKeys)):
            del self.mEdges[edgeKeys[idx]]
        del edgeKeys

        del self.mVertices
        del self.mEdges

        if self.kdTree:
            del self.kdTree

    def calculateSize(self):
        """
        Calculates the memory space of the graph

        :return graph memory space in bytes
        """
        size = 0

        verticesSize = 0
        for id in self.mVertices:
            verticesSize += self.mVertices[id].calculateSize()
        size += verticesSize
        size += sys.getsizeof(self.mVertices)

        edgesSize = 0
        for id in self.mEdges:
            edgesSize += self.mEdges[id].calculateSize()
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

        size += sys.getsizeof(self.numberNeighbours)
        size += sys.getsizeof(self.edgeDirection)
        size += sys.getsizeof(self.clusterNumber)
        size += sys.getsizeof(self.nnAllowDoubleEdges)
        size += sys.getsizeof(self.distance)

        size += sys.getsizeof(self.kdTree)

        size += sys.getsizeof(self.mJobId)

        return size

    def setVectorLayer(self, layer):
        self.vLayer = layer

    def setLineLayerForConnection(self, layer):
        self.lineLayerForConnection = layer

    def setJobID(self, jobId):
        self.mJobId = jobId

    def setRandomSeed(self, seed):
        self.randomSeed = seed

    def setDistanceStrategy(self, strategy):
        """
        Function is called by the GraphBuilder every time the makeGraph
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

    def setCostOfEdge(self, edgeId, functionIndex, cost):
        """
        Set cost of a specific edge.

        :type edgeId: Integer
        :type functionIndex: Integer
        :type cost: Integer

        :raises RuntimeError if distanceStrategy is not 'Advanced'
        """
        if not self.distanceStrategy == "Advanced":
            # do not set costs if distanceStrategy is not advanced
            raise RuntimeError(f"Can't set cost of edges in not advanced graph.")

        while len(self.edgeWeights) <= functionIndex:
            self.edgeWeights.append([])

        while len(self.edgeWeights[functionIndex]) <= edgeId:
            self.edgeWeights[functionIndex].append(-1)

        self.edgeWeights[functionIndex][edgeId] = cost

    def costOfEdge(self, edgeId, functionIndex = 0):
        """
        Function to get the weight of an edge. The returned value
        depends on the set distance strategy and on the functionIndex.
        The functionIndex defines the cost function to use if multiple ones
        are given.

        :type edgeId: Integer
        :type functionIndex: Integer
        :return cost of Edge, None if edgeId does not exist
        """
        if not edgeId in self.mEdges:
            return None

        #if the type is advanced the distances are set by the GraphBuilder directly
        if self.distanceStrategy == "Advanced":
            if functionIndex == -1:
                functionIndex = 0
            if len(self.edgeWeights) <= functionIndex or len(self.edgeWeights[functionIndex]) <= edgeId:
                return 0
            return self.edgeWeights[functionIndex][edgeId]

        elif self.distanceStrategy == "None":
            return None

        # differentiate between edge weights from cost functions and set weights from graph builder
        if self.distanceStrategy == "Euclidean":
            return self.euclideanDist(edgeId)

        elif self.distanceStrategy == "Manhattan":
            return self.manhattanDist(edgeId)

        # calculate geodesic distance using the Haversine formula
        elif self.distanceStrategy == "Geodesic":
            return self.geodesicDist(edgeId)

        elif self.distanceStrategy == "Ellipsoidal":
            return self.ellipsoidalDist(edgeId)

        #if the type is advanced the distances are set by the GraphBuilder directly
        elif self.distanceStrategy == "Advanced":
            # here edgeID is actually only edgeIdx
            if len(self.edgeWeights) <= functionIndex or len(self.edgeWeights[functionIndex]) <= edgeId:
                return None
            return self.edgeWeights[functionIndex][edgeId]

        elif self.distanceStrategy == "None":
            return None
        else:
            print("DistanceStrategy: ", self.distanceStrategy)
            raise NameError("Unknown distance strategy")

    def setCostOfVertex(self, vertexId, functionIndex, cost):
        """
        Set cost of a specific vertex.

        :type vertexId: Integer
        :type functionIndex: Integer
        :type cost: Integer
        """
        while len(self.vertexWeights) <= functionIndex:
            self.vertexWeights.append([])

        while len(self.vertexWeights[functionIndex]) <= vertexId:
            self.vertexWeights[functionIndex].append(-1)

        # important for e.g. rendering and writeGraphML
        self.advancedVertexWeights = True
        self.vertexWeights[functionIndex][vertexId] = cost

    def costOfVertex(self, vertexId, functionIndex = 0):
        """
        Function to get the weight of an vertex. The returned value
        depends on the set distance strategy and on the functionIndex.
        The functionIndex defines the cost function to use if multiple ones
        are given.

        :type vertexId: Integer
        :type functionIndex: Integer
        :return cost of Vertex, None if vertexId does not exist
        """
        if not vertexId in self.mVertices:
                    return None

        if len(self.vertexWeights) <= functionIndex or len(self.vertexWeights[functionIndex]) <= vertexId:
            return None
        return self.vertexWeights[functionIndex][vertexId]

    def ellipsoidalDist(self, edgeId):
        edgeFromId = self.edge(edgeId)
        fromPoint = self.vertex(edgeFromId.fromVertex()).point()
        toPoint = self.vertex(edgeFromId.toVertex()).point()
        distArea = QgsDistanceArea()
        distArea.setEllipsoid(self.crs.ellipsoidAcronym())
        ellDist = distArea.measureLine(fromPoint, toPoint)
        if str(ellDist) == "nan":
            return -1
        else:
            return ellDist

    def euclideanDist(self, edgeId):
        edgeFromId = self.edge(edgeId)
        fromPoint = self.vertex(edgeFromId.fromVertex()).point()
        toPoint = self.vertex(edgeFromId.toVertex()).point()
        euclDist = math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))
        return euclDist

    def manhattanDist(self, edgeId):
        edgeFromId = self.edge(edgeId)
        fromPoint = self.vertex(edgeFromId.fromVertex()).point()
        toPoint = self.vertex(edgeFromId.toVertex()).point()
        manhattenDist = abs(fromPoint.x()-toPoint.x()) + abs(fromPoint.y()-toPoint.y())
        return manhattenDist

    def geodesicDist(self, edgeId):
        edgeFromId = self.edge(edgeId)
        fromPoint = self.vertex(edgeFromId.fromVertex()).point()
        toPoint = self.vertex(edgeFromId.toVertex()).point()
        radius = 6371000
        phi1 = math.radians(fromPoint.y())
        phi2 = math.radians(toPoint.y())
        deltaPhi = math.radians(toPoint.y()-fromPoint.y())
        deltaLambda = math.radians(toPoint.x()-fromPoint.x())
        a = math.sin(deltaPhi/2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(deltaLambda / 2.0) ** 2
        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        return radius*c

    def distanceP2P(self, vertex1Id, vertex2Id):
        """
        Method to get the euclidean distance between two vertices

        :type vertex1Id: Integer
        :type vertex2Id: Integer
        :return distance between vertices
        """
        fromPoint = self.vertex(vertex1Id).point()
        toPoint = self.vertex(vertex2Id).point()
        return math.sqrt(pow(fromPoint.x()-toPoint.x(),2) + pow(fromPoint.y()-toPoint.y(),2))

    def hasEdge(self, vertex1Id, vertex2Id):
        """
        Method searches for the edge between to vertices

        :type vertex1Id: Integer
        :type vertex2Id: Integer
        :return Integer found edgeId, else -1
        """
        for edgeID in self.vertex(vertex1Id).outgoingEdges():
            edge = self.mEdges[edgeID]

            if edge.fromVertex() == vertex1Id and edge.toVertex() == vertex2Id:
                return edgeID

        if self.edgeDirection == "Undirected":
            for edgeID in self.vertex(vertex1Id).incomingEdges():
                edge = self.mEdges[edgeID]

                if edge.fromVertex() == vertex2Id and edge.toVertex() == vertex1Id:
                    return edgeID
        return -1

    def findVertex(self, vertex):
        """
        Modified findVertex function to find a vertex closest to each other

        :type vertex: QgsPointXY
        :return vertexId: Integer
        """
        minDist = sys.maxsize
        minId = -1

        for id in self.mVertices:
            checkVertex = self.vertex(id)

            dist = checkVertex.point().distance(vertex)
            if dist < minDist:
                minDist = dist
                minId = id

            if checkVertex.point() == vertex:
                return id

        if not minId == -1:
            return minId

        return -1

    def findVertices(self, topLeftPoint, bottomRightPoint):
        """
        Select multiple vertices in a rectangle defined by topLeftPoint and bottomRightPoint

        :type topLeftPoint: QgsPointXY
        :type bottomRightPoint: QgsPointXY
        :return foundVertexIds: []
        """
        foundVertexIds = []
        rect = QgsRectangle(topLeftPoint, bottomRightPoint)

        # TODO: here kdtree useable instead of linear search?
        for vertexId in self.mVertices:
            vertex = self.mVertices[vertexId]
            vertexPoint = vertex.point()

            if rect.contains(vertexPoint):
                foundVertexIds.append(vertexId)

        return foundVertexIds

    def nextEdgeID(self):
        return self.mMaxEdgeID

    def addEdge(self, vertex1ID, vertex2ID, ID=-1, highlighted=False, feat=None):
        """
        Adds an edge with fromVertex vertex1 and toVertex2 to the ExtGraph

        :type vertex1ID: Integer
        :type vertex2ID: Integer
        :type id: Integer add Edge with ID id, default -1 to be used,
                  non-default only used by QUndoCommands and readGraphML
        :type highlightd: Bool
        :return Integer id of added edge
        """
        addedEdgeID = ID
        if ID < 0:
            addedEdgeID = self.mMaxEdgeID
            self.mMaxEdgeID += 1

        if addedEdgeID >= self.mMaxEdgeID:
            self.mMaxEdgeID = addedEdgeID + 1

        addedEdge = self.ExtEdge(vertex1ID, vertex2ID, highlighted)
        if feat != None:
            addedEdge.feature = feat

        self.mEdges[addedEdgeID] = addedEdge

        # add entries for edgeWeights at the correct id
        for functionIdx in range(len(self.edgeWeights)):
            # add default value 0
            self.setCostOfEdge(addedEdgeID, functionIdx, 0)

        # register edge on from- and toVertices
        self.mVertices[vertex1ID].mOutgoingEdges.append(addedEdgeID)
        self.mVertices[vertex2ID].mIncomingEdges.append(addedEdgeID)

        self.mEdgeCount += 1

        return addedEdgeID

    def nextVertexID(self):
        return self.mMaxVertexID

    def addVertex(self, point, ID=-1):
        """
        Adds a vertex with coordinates point to ExtGraph

        :type point: QgsPointXY
        :type id: Integer add Vertex with ID id, default -1 to be used,
                  non-default only used by QUndoCommands and readGraphML
        :return Integer id of added edge
        """
        addedVertexID = ID
        if ID < 0:
            addedVertexID = self.mMaxVertexID
            self.mMaxVertexID += 1

        if addedVertexID >= self.mMaxVertexID:
            self.mMaxVertexID = addedVertexID + 1

        self.mVertices[addedVertexID] = self.ExtVertex(point)

        if hasattr(self, "mNextClusterID"):
            self.mVertices[addedVertexID].setClusterID(self.mNextClusterID)
            self.mNextClusterID += 1

        if self.kdTree:
            self.kdTree.add([point.x(), point.y()])

        # NOTE: this is commented since the plugin is mainly used for spanners atm
        # so vertexWeights are not always used

        # add entries for vertexWeights at the correct idx
        # for functionIdx in range(len(self.vertexWeights)):
        #     # add default value 0
        #     self.setCostOfVertex(addedVertexID, functionIdx, 0)

        self.mVertexCount += 1

        return addedVertexID

    def addVertexWithEdges(self, vertexCoordinates, fromUndo=False):
        """
        Methods adds a vertex with edges according to the origin GraphBuilder settings.

        Complete, NearestNeighbor (NN), DistanceNN, ClusterNN, ClusterComplete

        Does not support graphs with advanced costs

        :type vertexCoordinates: list with x,y-Coordinates
        :type fromUndo: Bool, if the call comes from an UndoCommand
        :return list of edges
        """
        if self.distanceStrategy == "Advanced":
            return

        if not self.kdTree and not self.mConnectionType == "Complete":
            points = []
            for id in self.mVertices:
                point = self.vertex(id).point()
                points.append([point.x(),point.y()])

            self.kdTree = kdtree.create(points)

        listOfEdges = []
        numberOfEdgesOriginal = self.edgeCount()
        addedVertexID = self.addVertex(QgsPointXY(vertexCoordinates[0], vertexCoordinates[1]))
        point = self.vertex(addedVertexID).point()

        #== COMPLETE ==============================================================================
        if self.mConnectionType == "Complete":
            addedEdgesCount = 1
            for vertexId in self.mVertices:
                if vertexId == addedVertexID:
                    continue

                if not fromUndo:
                    edgeId = self.addEdge(vertexId, addedVertexID)
                else:
                    edgeId = self.mMaxEdgeID + addedEdgesCount
                    addedEdgesCount += 1
                listOfEdges.append([edgeId, vertexId, addedVertexID])

        #== NEAREST NEIGHBOR & DISTANCENN =========================================================
        elif self.mConnectionType == "Nearest neighbor" or self.mConnectionType == "DistanceNN":
            # if this is True the nodes got deleted
            # TODO: why not self.nnAllowDoubleEdges?
            if not self.nnAllowDoubleEdges and not self.kdTree:
                points = []
                for id in self.mVertices:
                    if id == addedVertexID:
                        continue

                    p = self.vertex(id).point()
                    points.append([p.x(),p.y()])
                self.kdTree = kdtree.create(points)

            # else:
            #     # this should already happen in addVertex
            #     self.kdTree.add([point.x(),point.y()])

            if self.mConnectionType == "Nearest neighbor":
                listOfNeighbors = self.kdTree.search_knn([point.x(),point.y()], self.numberNeighbours+1)
                rangeStart = 1
                rangeEnd = len(listOfNeighbors)
            elif self.mConnectionType == "DistanceNN":
                transDistValue = self.distance[0] * QgsUnitTypes.fromUnitToUnitFactor(self.distance[1],
                                                                                      self.crs.mapUnits())
                listOfNeighbors = self.kdTree.search_nn_dist([point.x(),point.y()], pow(transDistValue,2))
                rangeStart = 0
                rangeEnd = len(listOfNeighbors)-1

            addedEdgesCount = 1
            for j in range(rangeStart,rangeEnd):
                if self.mConnectionType == "Nearest neighbor":
                    neighborPoint = listOfNeighbors[j][0].data
                elif self.mConnectionType == "DistanceNN":
                    neighborPoint = listOfNeighbors[j]

                neighborID = self.findVertex(QgsPointXY(neighborPoint[0], neighborPoint[1]))
                if not fromUndo:
                    edgeId = self.addEdge(addedVertexID, neighborID)
                else:
                    edgeId = self.mMaxEdgeID + addedEdgesCount
                    addedEdgesCount += 1
                listOfEdges.append([edgeId, addedVertexID, neighborID])
                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        edgeId = self.addEdge(addedVertexID, neighborID)
                    else:
                        edgeId = self.mMaxEdgeID + addedEdgesCount
                        addedEdgesCount += 1
                    listOfEdges.append([edgeId, neighborID, addedVertexID])

        #== CLUSTER COMPLETE ======================================================================
        elif self.mConnectionType == "ClusterComplete":

            # search nearest point
            neighborPoint = self.kdTree.search_knn([point.x(),point.y()], 2)
            neighborPointId = self.findVertex(QgsPointXY(neighborPoint[1][0].data[0], neighborPoint[1][0].data[1]))
            neighborVertex = self.vertex(neighborPointId)
            neighborClusterID = neighborVertex.clusterID()

            self.vertex(addedVertexID).setClusterID(neighborClusterID)

            # add an edge to all the neighbors of the found nearest point
            addedEdgesCount = 1
            for edgeID in neighborVertex.incomingEdges():
                edge = self.edge(edgeID)

                if not fromUndo:
                    addedEdgeId = self.addEdge(edge.fromVertex(), addedVertexID)
                else:
                    addedEdgeId = self.mMaxEdgeID + addedEdgesCount
                    addedEdgesCount += 1
                listOfEdges.append([addedEdgeId, edge.fromVertex(), addedVertexID])

                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        addedEdgeId = self.addEdge(addedVertexID, edge.fromVertex())
                    else:
                        addedEdgeId = self.mMaxEdgeID + addedEdgesCount
                        addedEdgesCount += 1
                    listOfEdges.append([addedEdgeId, addedVertexID, edge.fromVertex()])

            for edgeID in neighborVertex.outgoingEdges():
                edge = self.edge(edgeID)

                if not fromUndo:
                    addedEdgeId = self.addEdge(addedVertexID, edge.toVertex())
                else:
                    addedEdgeId = self.mMaxEdgeID + addedEdgesCount
                    addedEdgesCount += 1
                listOfEdges.append([addedEdgeId, addedVertexID, edge.toVertex()])

                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        addedEdgeId = self.addEdge(edge.toVertex(), addedVertexID)
                    else:
                        addedEdgeId = self.mMaxEdgeID + addedEdgesCount
                        addedEdgesCount += 1
                    listOfEdges.append([addedEdgeId, edge.toVertex(), addedVertexID])

            if not fromUndo:
                addedEdgeId = self.addEdge(neighborPointId, addedVertexID)
            else:
                addedEdgeId = self.mMaxEdgeID + addedEdgesCount
                addedEdgesCount += 1
            listOfEdges.append([addedEdgeId, neighborPointId, addedVertexID])

            if self.nnAllowDoubleEdges:
                if not fromUndo:
                    addedEdgeId = self.addEdge(addedVertexID, neighborPointId)
                else:
                    addedEdgeId = self.mMaxEdgeID + addedEdgesCount
                listOfEdges.append([addedEdgeId, addedVertexID, neighborPointId])

        #== CLUSTERNN =============================================================================
        elif self.mConnectionType == "ClusterNN":

            # search nearest point
            neighborPoint = self.kdTree.search_knn([point.x(),point.y()], 2)
            neighborPointId = self.findVertex(QgsPointXY(neighborPoint[1][0].data[0], neighborPoint[1][0].data[1]))
            neighborVertex = self.vertex(neighborPointId)
            neighborClusterID = neighborVertex.clusterID()

            # create kdtree with all the nodes from the same cluster
            points = []
            for vertexId in self.mVertices:
                vertex = self.vertex(vertexId)
                if vertex.clusterID() == neighborClusterID:
                    points.append([vertex.point().x(), vertex.point().y(), vertexId])

            clusterKDTree = kdtree.create(points)

            self.vertex(addedVertexID).setClusterID(neighborClusterID)

            listOfNeighbors = clusterKDTree.search_knn([point.x(),point.y(), addedVertexID], self.numberNeighbours)
            addedEdgesCount = 1
            for j in range(len(listOfNeighbors)):
                neighborVertexID = self.findVertex(QgsPointXY(listOfNeighbors[j][0].data[0],
                                                   listOfNeighbors[j][0].data[1]))

                if not fromUndo:
                    edgeId = self.addEdge(addedVertexID, neighborVertexID)
                else:
                    edgeId = self.mMaxEdgeID + addedEdgesCount
                    addedEdgesCount += 1
                listOfEdges.append([edgeId, addedVertexID, neighborVertexID])

                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        edgeId = self.addEdge(addedVertexID, neighborVertexID)
                    else:
                        edgeId = self.mMaxEdgeID + addedEdgesCount
                        addedEdgesCount += 1
                    listOfEdges.append([edgeId, neighborVertexID, addedVertexID])

            del clusterKDTree

        #== RANDOM =============================================================================
        elif self.mConnectionType == "Random":
            amountEdgesToBeAdded = math.ceil(self.mEdgeCount / self.mVertexCount)

            # bound amountEdgesToBeAdded by vertex count
            if amountEdgesToBeAdded > self.mVertexCount - 1:
                amountEdgesToBeAdded = self.mVertexCount - 1

            vertexKeys = list(self.mVertices.keys())
            pastRandomVertices = []
            addedEdgesCount = 1
            for j in range(amountEdgesToBeAdded):
                # choose random vertex
                randomVertexID = vertexKeys[randrange(self.mVertexCount)]
                while randomVertexID == addedVertexID or randomVertexID in pastRandomVertices:
                    randomVertexID = vertexKeys[randrange(self.mVertexCount)]
                pastRandomVertices.append(randomVertexID)

                if not fromUndo:
                    edgeId = self.addEdge(randomVertexID, addedVertexID)
                else:
                    edgeId = self.mMaxEdgeID + addedEdgesCount
                    addedEdgesCount += 1
                listOfEdges.append([edgeId, randomVertexID, addedVertexID])

                if self.nnAllowDoubleEdges:
                    if not fromUndo:
                        edgeId = self.addEdge(addedVertexID, randomVertexID)
                    else:
                        edgeId = self.mMaxEdgeID + addedEdgesCount
                        addedEdgesCount += 1
                    listOfEdges.append([edgeId, randomVertexID, addedVertexID])

        return listOfEdges

    def edge(self, id):
        if not id in self.mEdges:
            raise IndexError(f"Edge id {id} is out of bounds")
        return self.mEdges[id]

    def edgeCount(self):
        return self.mEdgeCount

    def vertex(self, id):
        if not id in self.mVertices:
            raise IndexError(f"Vertex id {id} is out of bounds")
        return self.mVertices[id]

    def vertexCount(self):
        return self.mVertexCount

    def vertices(self):
        return self.mVertices

    def edges(self):
        return self.mEdges

    def deleteEdge(self, id):
        """
        Deletes an edge

        :type id: Integer, id of edge to delete
        :return Bool
        """
        if id in self.mEdges:
            edge = self.mEdges[id]
            edgeID = id

            # remove edge from toVertex incomingEdges
            toVertexId = edge.toVertex()
            if not toVertexId == -1:
                toVertex = self.vertex(toVertexId)
                for incomingIdx in range(len(toVertex.mIncomingEdges)):
                    if toVertex.mIncomingEdges[incomingIdx] == edgeID:
                        toVertex.mIncomingEdges.pop(incomingIdx)
                        break

            # remove edge from fromVertex outgoingEdges
            fromVertexId = edge.fromVertex()
            if not fromVertexId == -1:
                fromVertex = self.vertex(fromVertexId)
                for outgoingIdx in range(len(fromVertex.mOutgoingEdges)):
                    if fromVertex.mOutgoingEdges[outgoingIdx] == edgeID:
                        fromVertex.mOutgoingEdges.pop(outgoingIdx)
                        break

            del self.mEdges[id]

            # also remove entries from edgeWeights
            for functionIdx in range(len(self.edgeWeights)):
                self.edgeWeights[functionIdx][id] = -1

            self.mEdgeCount -= 1
            return True
        return False

    def deleteVertex(self, id, fromUndo=False):
        """
        Deletes a vertex and all outgoing and incoming edges of this vertex

        :type id: Integer, index of vertex to delete
        :type fromUndo: Bool non-default only used by QUndoCommand
        :return list with ids of all edges deleted (may be empty)

        """
        deletedEdgeIDs = []
        if id in self.mVertices:
            vertex = self.mVertices[id]

            # delete all incoming edges vertex is connected with
            for incomingIdx in range(len(vertex.incomingEdges())):
                edgeID = vertex.incomingEdges().pop(0)
                self.edge(edgeID).mToID = -1
                deletedEdgeIDs.append(edgeID)
            vertex.mIncomingEdges = []

            # delete all outgoing edges vertex is connected with
            for outgoingIdx in range(len(vertex.outgoingEdges())):
                edgeID = vertex.outgoingEdges().pop(0)
                self.edge(edgeID).mFromID = -1
                deletedEdgeIDs.append(edgeID)
            vertex.mOutgoingEdges = []

            if self.kdTree:
                self.kdTree.remove([vertex.point().x(), vertex.point().y()])

            del self.mVertices[id]

            # also remove entries from vertexWeights
            for functionIdx in range(len(self.vertexWeights)):
                self.vertexWeights[functionIdx][id] = -1

            self.mVertexCount -= 1

            if not fromUndo:
                # undoCommand creates deleteEdgeCommands on its own and append it to the deleteVertexCommand
                for id in deletedEdgeIDs:
                    self.deleteEdge(id)

        return deletedEdgeIDs

    def updateCrs(self, crs=QgsCoordinateReferenceSystem("EPSG:4326")):
        """
        Update the graphs coordinate reference system.
        The containing coordinates will be updated if the given crs is a different one.
        """
        # update crs and coordinates if new crs is different and old crs is not None
        if not self.crs or not crs.authid() == self.crs.authid():
            newCrs = crs

            if self.crs:
                transform = QgsCoordinateTransform(self.crs, newCrs, QgsProject.instance())

                for id in self.mVertices:
                    vertex = self.mVertices[id]
                    coords = vertex.point()
                    newCoords = transform.transform(coords)

                    vertex.setNewPoint(newCoords)

            self.crs = newCrs


    def writeGraphML(self, path):
        """
        Write the graph into a .graphml format

        :type path: String
        """
        with open(path, "w") as file:
            header = ['<?xml version="1.0" encoding="UTF-8"?>\n',
                '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n',
                '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
                '\txmlns:y="http://www.yworks.com/xml/graphml"\n',
                '\txsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n',
                '\t http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n',
                '\t<key for="node" attr.name="label" attr.type="string" id="label" />\n',
                '\t<key for="node" attr.name="x" attr.type="double" id="x" />\n',
                '\t<key for="node" attr.name="y" attr.type="double" id="y" />\n',
                '\t<key for="node" attr.name="size" attr.type="double" id="size" />\n',
                '\t<key for="node" attr.name="r" attr.type="int" id="r" />\n',
                '\t<key for="node" attr.name="g" attr.type="int" id="g" />\n',
                '\t<key for="node" attr.name="b" attr.type="int" id="b" />\n',
                '\t<key for="node" attr.name="width" attr.type="double" id="width" />\n',
                '\t<key for="node" attr.name="height" attr.type="double" id="height" />\n',
                '\t<key for="node" attr.name="shape" attr.type="string" id="shape" />\n',
                '\t<key for="node" attr.name="nodestroke" attr.type="string" id="nodestroke" />\n',
                '\t<key for="node" attr.name="nodestroketype" attr.type="int" id="nodestroketype" />\n',
                '\t<key for="node" attr.name="nodestrokewidth" attr.type="double" id="nodestrokewidth" />\n',
                '\t<key for="node" attr.name="nodefill" attr.type="int" id="nodefill" />\n',
                '\t<key for="node" attr.name="nodefillbg" attr.type="string" id="nodefillbg" />\n',
                '\t<key for="node" attr.name="nodetype" attr.type="int" id="nodetype" />\n']

            # add keys for fields in pointLayer
            if self.vLayer != None and self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                for field in self.vLayer.fields():
                    type = field.typeName()
                    typeNameConv = ""
                    if type == "String":
                        typeNameConv = "string"
                    elif type == "Real":
                        typeNameConv = "double"
                    elif type == "Integer":
                        typeNameConv = "int"
                    else:
                        typeNameConv = "string"
                    string = '\t<key for="node" attr.name="' + 'field_' + field.name() + '" attr.type="' +\
                             typeNameConv + '" id = "' + field.name() + '" />\n'
                    header.append(string)

            eStroke = ['\t<key for="edge" attr.name="edgetype" attr.type="string" id="edgetype" />\n',
                       '\t<key for="edge" attr.name="edgestroke" attr.type="string" id="edgestroke" />\n',
                       '\t<key for="edge" attr.name="edgestroketype" attr.type="int" id="edgestroketype" />\n',
                       '\t<key for="edge" attr.name="edgestrokewidth" attr.type="double" id="edgestrokewidth" />\n']
            header.extend(eStroke)

            # add keys for fields in lineLayer
            if self.vLayer != None and self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:
                for field in self.vLayer.fields():
                    type = field.typeName()
                    typeNameConv = ""
                    if type == "String":
                        typeNameConv = "string"
                    elif type == "Real":
                        typeNameConv = "double"
                    elif type == "Integer":
                        typeNameConv = "int"
                    else:
                        typeNameConv = "string"
                    string = '\t<key for="edge" attr.name="' + 'field_' + field.name() + '" attr.type="' +\
                             typeNameConv + '" id = "' + field.name() + '" />\n'
                    header.append(string)

            # add keys for fields in lineLayer (and pointLayer)
            if self.vLayer != None and self.vLayer.geometryType() == QgsWkbTypes.PointGeometry and\
               self.connectionType() == "LineLayerBased":
                # in this case the edge feature contains a dictionary
                for field in self.lineLayerForConnection.fields():
                    type = field.typeName()
                    typeNameConv = ""
                    if type == "String":
                        typeNameConv = "string"
                    elif type == "Real":
                        typeNameConv = "double"
                    elif type == "Integer":
                        typeNameConv = "int"
                    else:
                        typeNameConv = "string"
                    string = '\t<key for="edge" attr.name="' + 'field_' + field.name() + '" attr.type="' +\
                             typeNameConv + '" id = "' + field.name() + '" />\n'
                    header.append(string)

            file.writelines(header)

            if self.mConnectionType == "ClusterComplete" or self.mConnectionType == "ClusterNN":
                clusterKey = '\t<key for="node" attr.name="clusterid" attr.type="int" id="clusterid" />\n'
                file.write(clusterKey)

            if self.distanceStrategy == "Advanced" and self.amountOfEdgeCostFunctions() > 1:
                advancedEdgeKeys = ''
                for costIdx in range(self.amountOfEdgeCostFunctions()):
                    advancedEdgeKeys += '\t<key for="edge" attr.name="weight_' + str(costIdx) +\
                                        '" attr.type="double" id="weight_' + str(costIdx) + '" />\n'
                file.write(advancedEdgeKeys)
            else:
                weightKey = '\t<key for="edge" attr.name="weight" attr.type="double" id="weight" />\n'
                file.write(weightKey)

            # if setCostOfVertex was used to add specific cost to a vertex
            if hasattr(self, "advancedVertexWeights") and self.advancedVertexWeights:
                advancedVertexKeys = ''
                for costIdx in range(len(self.vertexWeights)):
                    advancedVertexKeys += '\t<key for="node" attr.name="weight_' + str(costIdx) +\
                                          ' attr.type="double id="c_' + str(costIdx) + '" />\n'
                file.write(advancedVertexKeys)

            edgeDefault = self.edgeDirection.lower()

            graphString = '\t<graph id="G" ' +\
                          'edgedefault="' + edgeDefault + '" distancestrategy="' + self.distanceStrategy +\
                          '" connectiontype="' + self.mConnectionType +\
                          '" numberneighbors="' + str(self.numberNeighbours) +\
                          '" nnallowdoubleedges="' + str(self.nnAllowDoubleEdges) +\
                          '" distance="' + str(self.distance[0]) +\
                          '" distanceunit="' + str(self.distance[1]) + '"' +\
                          ((' seed="' + str(self.randomSeed)) + '"' if self.randomSeed else '') +\
                          ((' crs="' + self.crs.authid() + '"') if self.crs else '') + '>\n'
            file.write(graphString)

            vertexKeyAttributes = ['\t\t\t<data key="width">20</data>\n',
                                  '\t\t\t<data key="height">20</data>\n',
                                  '\t\t\t<data key="size">20</data>\n',
                                  '\t\t\t<data key="shape">rect</data>\n',
                                  '\t\t\t<data key="r">255</data>\n',
                                  '\t\t\t<data key="g">255</data>\n',
                                  '\t\t\t<data key="b">255</data>\n',
                                  '\t\t\t<data key="nodefill">1</data>\n',
                                  '\t\t\t<data key="nodefillbg">#000000</data>\n',
                                  '\t\t\t<data key="nodestroke">#000000</data>\n',
                                  '\t\t\t<data key="nodestroketype">1</data>\n',
                                  '\t\t\t<data key="nodestrokewidth">1</data>\n',
                                  '\t\t\t<data key="nodetype">0</data>\n']

            for id in self.mVertices:
                vertex = self.vertex(id)
                nodeLine = '\t\t<node id="' + str(id) + '">\n'
                file.write(nodeLine)
                file.write('\t\t\t<data key="x">' + str(vertex.point().x()) + '</data>\n')
                file.write('\t\t\t<data key="y">' + str(vertex.point().y()) + '</data>\n')
                file.writelines(vertexKeyAttributes)
                if self.mConnectionType == "ClusterComplete" or self.mConnectionType == "ClusterNN":
                    file.write('\t\t\t<data key="clusterid">' + str(vertex.clusterID()) + '</data>\n')
                if self.vLayer != None and self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                    feat = self.vLayer.getFeature(id)
                    if feat != None:
                        for field in feat.fields():
                            file.write('\t\t\t<data key="field_' + str(field.name()) + '">' +\
                                       str(feat[field.name()]) + '</data>\n')

                # if setCostOfVertex was used to add specific cost to a vertex
                if hasattr(self, "advancedVertexWeights") and self.advancedVertexWeights:
                    vertexData = ''
                    for costIdx in range(len(self.vertexWeights)):
                        vertexData += '\t\t\t<data key="c_' + str(costIdx) + '">' +\
                                      str(self.costOfVertex(id, costIdx)) + '</data>\n'
                    file.write(vertexData)

                file.write('\t\t</node>\n')

            # TODO: 'bends'
            edgeKeyAttributes = ['\t\t\t<data key="edgetype">association</data>\n',
                                '\t\t\t<data key="edgestroke">#000000</data>\n',
                                '\t\t\t<data key="edgestroketype">1</data>\n',
                                '\t\t\t<data key="edgestrokewidth">1</data>\n']

            for id in self.mEdges:
                edge = self.edge(id)
                edgeLine = '\t\t<edge id="' + str(id) + '" source="' + str(edge.fromVertex()) + '" target="' +\
                           str(edge.toVertex()) + '">\n'
                file.write(edgeLine)
                file.writelines(edgeKeyAttributes)

                edgeData = ''
                if self.distanceStrategy == "Advanced" and self.amountOfEdgeCostFunctions() > 1:
                    for costIdx in range(self.amountOfEdgeCostFunctions()):
                        edgeData += '\t\t\t<data key="weight_' + str(costIdx) + '">' +\
                                    str(self.costOfEdge(id, costIdx)) + '</data>\n'
                else:
                    edgeData += '\t\t\t<data key="weight">' + str(self.costOfEdge(id)) + '</data>\n'
                file.write(edgeData)

                if self.vLayer != None and self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:
                    for field in self.vLayer.fields():
                        if edge.feature != None:
                            file.write('\t\t\t<data key="field_' + str(field.name()) + '">' +\
                                       str(edge.feature[field.name()]) + '</data>\n')

                if self.vLayer != None and self.vLayer.geometryType() == QgsWkbTypes.PointGeometry and\
                   self.connectionType() == "LineLayerBased":
                    # in this case the edge feature contains a dictionary
                    if edge.feature != None:
                        for dict in edge.feature:
                            for key in dict.keys():
                                file.write('\t\t\t<data key="field_' + str(key) + '">' + str(dict[key]) + '</data>\n')

                file.write('\t\t</edge>\n')

            file.write("\t</graph>\n")
            file.write("</graphml>")

    def readGraphML(self, path):
        """
        Read a .graphml file into a ExtGraph

        :type path: String
        """
        with open(path, "r") as file:
            lines = file.readlines()

        nodeCoordinatesGiven = False
        edgeTypeDirection = "Directed"
        currNodeID = 0
        parseNode = True

        for line in lines:
            if 'edgedefault="undirected"' in line:
                edgeTypeDirection = "Undirected"

            if 'distancestrategy' in line:
                self.distanceStrategy = line.split('distancestrategy="')[1].split('"')[0]

            if 'connectiontype' in line:
                self.mConnectionType = line.split('connectiontype="')[1].split('"')[0]

            if 'numberneighbors' in line:
                self.numberNeighbours = int(line.split('numberneighbors="')[1].split('"')[0])

            if 'nnallowdoubleedges' in line:
                self.nnAllowDoubleEdges = line.split('nnallowdoubleedges="')[1].split('"')[0] == "True"

            if 'distance=' in line:
                self.distance = [float(line.split('distance="')[1].split('"')[0])]

            if 'distanceunit=' in line:
                self.distance.append(int(line.split('distanceunit="')[1].split('"')[0]))

            if 'seed' in line:
                self.randomSeed = int(line.split('seed="')[1].split('"')[0])

            if 'crs' in line:
                self.crs = QgsCoordinateReferenceSystem(line.split('crs="')[1].split('"')[0])

            if 'key="x"' in line:
                nodeCoordinatesGiven = True
                break

        self.edgeDirection = edgeTypeDirection

        for line in lines:
            if '<node' in line:
                currNodeID = int(line.split('id="')[1].split('"')[0])
                parseNode = True

                if not nodeCoordinatesGiven:
                    # add vertex with random coordinates and correct ID
                    currNodeID = self.addVertex(QgsPointXY(randrange(742723,1534455), randrange(6030995,7314884)),
                                                currNodeID)

            elif '<edge' in line:
                currEdgeID = int(line.split('id="')[1].split('"')[0])
                fromVertex = int(line.split('source="')[1].split('"')[0])
                toVertex = int(line.split('target="')[1].split('"')[0])

                # add edge (no need to give ID here)
                currEdgeID = self.addEdge(fromVertex, toVertex, currEdgeID)
                parseNode = False

            elif '<data' in line:
                if 'key="x"' in line:
                    xValue = float(line.split('<data key="x">')[1].split('<')[0])

                elif 'key="y"' in line:
                    yValue = float(line.split('<data key="y">')[1].split('<')[0])

                    # add vertex with correct coordinates and ID
                    self.addVertex(QgsPointXY(xValue, yValue), currNodeID)

                elif 'key="cluster"' in line:
                    self.vertex(currNodeID).setClusterID(int(line.split('<data key="cluster">')[1].split('<')[0]))

                elif 'key="weight' in line and self.distanceStrategy == "Advanced":
                    if "weight_" in line:
                        costIdx = int(line.split('key="weight_')[1].split('"')[0])
                        cost = float(line.split('<data key="weight_' + str(costIdx) + '">')[1].split('<')[0])
                    elif "weight" in line:
                        costIdx = 0
                        cost = float(line.split('<data key="weight">')[1].split('<')[0])

                    if parseNode:
                        self.setCostOfVertex(currNodeID, costIdx, cost)
                    else:
                        self.setCostOfEdge(currEdgeID, costIdx, cost)
