from qgis.core import QgsPointXY

from ..exceptions import ParseError
from ..protocol.build import container_pb2, shortest_path_pb2


class ShortPathResponse():

    def __init__(self, graph=None):
        self.graph = graph

        self.type = container_pb2.ResponseContainer.ResponseType.SHORTEST_PATH

    def parseProtoBuf(self, protoBuf):
        if protoBuf.type != self.type:
            raise ParseError("Invalid response type")

        response = shortest_path_pb2.ShortestPathResponse()
        protoBuf.response.Unpack(response)

        protoGraph = response.graph

        for vertex in protoGraph.vertexList:
            vertexX = response.vertexCoordinates[vertex.uid].x
            vertexY = response.vertexCoordinates[vertex.uid].y
            #TODO Parse possible z coordinates from protobuf
            self.graph.addVertex(QgsPointXY(vertexX, vertexY))

        for edge in protoGraph.edgeList:
            self.graph.addEdge(edge.inVertexUid, edge.outVertexUid, [])
