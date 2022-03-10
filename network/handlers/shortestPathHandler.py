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

    def __init__(self):
        super().__init__()

        self.type = meta_pb2.RequestType.SHORTEST_PATH
        self.protoRequest = shortest_path_pb2.ShortestPathRequest

        self.key = "shortest_path"


class OldShortestPathRequest():

    def __init__(self, graph=None, startUid=None, endUid=None):
        self.graph = graph
        self.startUid = startUid
        self.endUid = endUid

        self.type = meta_pb2.RequestContainer.RequestType.SHORTEST_PATH

    def toProtoBuf(self):
        request = shortest_path_pb2.ShortestPathRequest()
        request.startUid = self.startUid
        request.endUid = self.endUid

        request.graph.uid = 0

        for vertexIdx in range(self.graph.vertexCount()):
            point = self.graph.vertex(vertexIdx).point()

            protoVertex = request.graph.vertexList.add()
            protoVertex.uid = vertexIdx

            vertexCoordinates = request.vertexCoordinates.add()
            vertexCoordinates.x = point.x()
            vertexCoordinates.y = point.y()
            # TODO Include possible z coordinates in protobuf

        for edgeIdx in range(self.graph.edgeCount()):
            edge = self.graph.edge(edgeIdx)

            protoEdge = request.graph.edgeList.add()
            protoEdge.uid = edgeIdx
            protoEdge.inVertexIndex = edge.fromVertex()
            protoEdge.outVertexIndex = edge.toVertex()

            request.edgeCosts.append(self.graph.costOfEdge(edgeIdx))

        return request


class ShortestPathResponse(BaseGraphResponse):

    def __init__(self):
        super().__init__()

        self.type = meta_pb2.RequestType.SHORTEST_PATH
        self.protoResponse = shortest_path_pb2.ShortestPathResponse

        self.key = "shortest_path"


class OldShortestPathResponse():

    def __init__(self, graph=None):
        self.graph = graph

        self.type = meta_pb2.ResponseContainer.ResponseType.SHORTEST_PATH

    def parseProtoBuf(self, protoBuf):
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
            self.graph.addEdge(edge.inVertexIndex, edge.outVertexIndex, [])
