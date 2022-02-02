from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem

from ..protocol.build import meta_pb2, origin_graph_pb2

from ...models.ExtGraph import ExtGraph


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
