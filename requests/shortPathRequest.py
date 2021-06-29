from ..protocol.build import container_pb2, shortest_path_pb2


class ShortPathRequest():

    def __init__(self, graph=None, startIndex=None, endIndex=None):
        self.graph = graph
        self.startIndex = startIndex
        self.endIndex = endIndex

        self.type = container_pb2.RequestContainer.RequestType.SHORTEST_PATH

    def toProtoBuf(self):
        request = shortest_path_pb2.ShortestPathRequest()
        request.startIndex = self.startIndex
        request.endIndex = self.endIndex

        request.graph.uid = 0

        for vertexIdx in range(self.graph.vertexCount()):
            point = self.graph.vertex(vertexIdx).point()

            protoVertex = request.graph.vertexList.add()
            protoVertex.uid = vertexIdx

            vertexCoordinates = request.vertexCoordinates
            vertexCoordinates[vertexIdx].x = point.x()
            vertexCoordinates[vertexIdx].y = point.y()
            #TODO Include possible z coordinates in protobuf

        for edgeIdx in range(self.graph.edgeCount()):
            edge = self.graph.edge(edgeIdx)

            protoEdge = request.graph.edgeList.add()
            protoEdge.uid = edgeIdx
            protoEdge.inVertexUid = edge.fromVertex()
            protoEdge.outVertexUid = edge.toVertex()

            request.edgeCost[edgeIdx] = self.graph.costOfEdge(edgeIdx)

        return request
