#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz
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

from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem

from ...models.ExtGraph import ExtGraph

from ..protocol.build import origin_graph_pb2, meta_pb2


class OriginGraphRequest():

    def __init__(self, jobId):
        self.type = meta_pb2.RequestType.ORIGIN_GRAPH
        self.jobId = jobId

    def toProtoBuf(self):
        proto = origin_graph_pb2.OriginGraphRequest()
        proto.jobId = self.jobId
        return proto


class OriginGraphResponse():

    def __init__(self):
        super().__init__()

        self.type = meta_pb2.RequestType.ORIGIN_GRAPH
        self.protoResponse = origin_graph_pb2.OriginGraphResponse

        self.graph = None

    def getGraph(self):
        return self.graph

    def parseProtoBuf(self, protoBuf):
        response = self.protoResponse()
        protoBuf.response.Unpack(response)

        protoGraph = response.graph
        self.graph = ExtGraph()

        # parse static attributes from response
        crs = QgsCoordinateReferenceSystem(response.staticAttributes.get("crs"))
        if crs.isValid():
            self.graph.updateCrs(crs)
        self.graph.edgeDirection = response.staticAttributes.get("edgeDirection", "Directed")

        # create vertices
        for vertex in protoGraph.vertexList:
            self.graph.addVertex(QgsPointXY(0, 0), -1, vertex.uid)

        # create edges
        for edge in protoGraph.edgeList:
            inVertexId = protoGraph.vertexList[edge.inVertexIndex].uid
            outVertexId = protoGraph.vertexList[edge.outVertexIndex].uid
            self.graph.addEdge(inVertexId, outVertexId, -1, edge.uid)

        # set vertex positions
        for idx, vertexCoordinates in enumerate(response.vertexCoordinates):
            vertex = self.graph.vertex(idx)
            vertex.point().setX(vertexCoordinates.x)
            vertex.point().setY(vertexCoordinates.y)
            # TODO Parse possible z coordinates from protobuf

        # set edge costs
        self.graph.setDistanceStrategy(response.staticAttributes.get("distanceStrategy", "None"))
        if self.graph.distanceStrategy == "Advanced":
            for edgeIdx, edgeCost in enumerate(response.edgeCosts):
                self.graph.setCostOfEdge(edgeIdx, 0, edgeCost)
