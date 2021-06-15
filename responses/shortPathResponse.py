from qgis.core import QgsPointXY

from ..exceptions import ParseError
from ..protocol.protos import GraphData_pb2


class ShortPathResponse():

    def __init__(self, graph=None):
        self.graph = graph

        self.type = GraphData_pb2.ResponseContainer.ResponseType.SHORTEST_PATH

    def parseProtoBuf(self, protoBuf):
        if protoBuf.type != self.type:
            raise ParseError("Invalid response type")

        response = GraphData_pb2.ShortPathResponse()
        protoBuf.response.Unpack(response)

        protoGraph = response.graph

        for vertex in protoGraph.vertexList:
            self.graph.addVertex(QgsPointXY(vertex.x, vertex.y))

        for edge in protoGraph.edgeList:
            self.graph.addEdge(edge.inVertexUid, edge.outVertexUid, [])
