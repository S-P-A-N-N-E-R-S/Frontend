from ..protocol.protos import GraphData_pb2


class ShortPathRequest():

    def __init__(self, graph=None, startIndex=None, endIndex=None):
        self.graph = graph
        self.startIndex = startIndex
        self.endIndex = endIndex

        self.type = GraphData_pb2.RequestContainer.RequestType.SHORTEST_PATH

    def toProtoBuf(self):
        request = GraphData_pb2.ShortPathRequest()
        request.startIndex = self.startIndex
        request.endIndex = self.endIndex

        request.graph.uid = 0

        for vertexIdx in range(self.graph.vertexCount()):
            point = self.graph.vertex(vertexIdx).point()

            protoVertex = request.graph.vertexList.add()
            protoVertex.uid = vertexIdx
            protoVertex.x = point.x()
            protoVertex.y = point.y()

        for edgeIdx in range(self.graph.edgeCount()):
            edge = self.graph.edge(edgeIdx)

            protoEdge = request.graph.edgeList.add()
            protoEdge.uid = edgeIdx
            protoEdge.inVertexUid = edge.fromVertex()
            protoEdge.outVertexUid = edge.toVertex()
            protoEdge.attributes["cost"] = str(edge.cost(0))

        return request
