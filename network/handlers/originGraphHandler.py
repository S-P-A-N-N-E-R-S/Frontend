#  This file is part of the S.P.A.N.N.E.R.S. plugin.
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
    """Request handler for the origin graph request"""

    def __init__(self, jobId):
        """
        Constructor

        :param jobId: ID of the job with the desired origin graph
        """

        self.type = meta_pb2.RequestType.ORIGIN_GRAPH
        self.jobId = jobId

    def toProtoBuf(self):
        """
        Creates and returns the protobuf message for the origin graph request

        :return: The created origin graph request
        """

        proto = origin_graph_pb2.OriginGraphRequest()
        proto.jobId = self.jobId
        return proto


class OriginGraphResponse():
    """Response handler for the origin graph response"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.type = meta_pb2.RequestType.ORIGIN_GRAPH
        self.protoResponse = origin_graph_pb2.OriginGraphResponse

        self.graph = None

    def getGraph(self):
        """Returns the origin graph"""

        return self.graph

    def parseProtoBuf(self, protoBuf):
        """
        Parses the specified protobuf message object

        :param protoBuf: The protobuf message to be parsed
        """

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
            self.graph.addVertex(QgsPointXY(0, 0), vertex.uid)

        # create edges
        for edge in protoGraph.edgeList:
            inVertexId = protoGraph.vertexList[edge.inVertexIndex].uid
            outVertexId = protoGraph.vertexList[edge.outVertexIndex].uid
            self.graph.addEdge(inVertexId, outVertexId, edge.uid)

        # set vertex positions
        for id, vertexCoordinates in enumerate(response.vertexCoordinates):
            vertex = self.graph.vertex(id)
            vertex.point().setX(vertexCoordinates.x)
            vertex.point().setY(vertexCoordinates.y)
            # TODO Parse possible z coordinates from protobuf

        # set edge costs
        self.graph.setDistanceStrategy(response.staticAttributes.get("distanceStrategy", "None"))
        if self.graph.distanceStrategy == "Advanced":
            for edgeId, edgeCost in enumerate(response.edgeCosts):
                self.graph.setCostOfEdge(edgeId, 0, edgeCost)
