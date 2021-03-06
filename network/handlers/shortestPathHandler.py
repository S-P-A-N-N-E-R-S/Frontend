#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
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

from qgis.core import QgsPointXY

from .baseHandler import BaseGraphRequest, BaseGraphResponse
from ..exceptions import ParseError

from ..protocol.build import meta_pb2
from ..protocol.build.handlers import shortest_path_pb2


class ShortestPathRequest(BaseGraphRequest):
    """Request handler for the shortest path request; Unused"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.type = meta_pb2.RequestType.SHORTEST_PATH
        self.protoRequest = shortest_path_pb2.ShortestPathRequest

        self.key = "shortest_path"


class OldShortestPathRequest():
    """Old request handler for the shortest path request; Unused"""

    def __init__(self, graph=None, startUid=None, endUid=None):
        """
        Constructor

        :param graph: Graph instance, defaults to None
        :param startUid: UID of the start node, defaults to None
        :param endUid: UID of the end node, defaults to None
        """

        self.graph = graph
        self.startUid = startUid
        self.endUid = endUid

        self.type = meta_pb2.RequestContainer.RequestType.SHORTEST_PATH

    def toProtoBuf(self):
        """
        Creates and returns the protobuf message for the shortest path request

        :return: The created protobuf message
        """

        request = shortest_path_pb2.ShortestPathRequest()
        request.startUid = self.startUid
        request.endUid = self.endUid

        request.graph.uid = 0

        for vertexId, vertex in self.graph.vertices().items():
            point = vertex.point()

            protoVertex = request.graph.vertexList.add()
            protoVertex.uid = vertexId

            vertexCoordinates = request.vertexCoordinates.add()
            vertexCoordinates.x = point.x()
            vertexCoordinates.y = point.y()
            # TODO Include possible z coordinates in protobuf

        for edgeId, edge in self.graph.edges().items():
            protoEdge = request.graph.edgeList.add()
            protoEdge.uid = edgeId
            protoEdge.inVertexIndex = edge.fromVertex()
            protoEdge.outVertexIndex = edge.toVertex()

            request.edgeCosts.append(self.graph.costOfEdge(edgeId))

        return request


class ShortestPathResponse(BaseGraphResponse):
    """Response handler for the shortest path response; Unused"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.type = meta_pb2.RequestType.SHORTEST_PATH
        self.protoResponse = shortest_path_pb2.ShortestPathResponse

        self.key = "shortest_path"


class OldShortestPathResponse():
    """Old response handler for the shortest path response; Unused"""

    def __init__(self, graph=None):
        """
        Constructor

        :param graph: Graph instance, defaults to None
        """

        self.graph = graph

        self.type = meta_pb2.ResponseContainer.ResponseType.SHORTEST_PATH

    def parseProtoBuf(self, protoBuf):
        """
        Parses the specified protobuf message

        :param protoBuf: Protobuf message to be parsed
        :raises ParseError: If the response type is invalid
        """

        if protoBuf.type != self.type:
            raise ParseError("Invalid response type")

        response = shortest_path_pb2.ShortestPathResponse()
        protoBuf.response.Unpack(response)

        protoGraph = response.graph

        # TODO Set vertex_uid of new vertex
        for idx, _vertex in enumerate(protoGraph.vertexList):
            vertexX = response.vertexCoordinates[idx].x
            vertexY = response.vertexCoordinates[idx].y
            # TODO Parse possible z coordinates from protobuf
            self.graph.addVertex(QgsPointXY(vertexX, vertexY))

        for edge in protoGraph.edgeList:
            self.graph.addEdge(edge.inVertexIndex, edge.outVertexIndex)
