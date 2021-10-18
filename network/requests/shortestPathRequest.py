from .baseRequest import BaseGraphRequest

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
            #TODO Include possible z coordinates in protobuf

        for edgeIdx in range(self.graph.edgeCount()):
            edge = self.graph.edge(edgeIdx)

            protoEdge = request.graph.edgeList.add()
            protoEdge.uid = edgeIdx
            protoEdge.inVertexIndex = edge.fromVertex()
            protoEdge.outVertexIndex = edge.toVertex()

            request.edgeCosts.append(self.graph.costOfEdge(edgeIdx))

        return request
