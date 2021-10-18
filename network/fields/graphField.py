from qgis.core import QgsPointXY

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class GraphField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.GRAPH

    def toProtoBuf(self, request, data):
        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        protoField = getattr(request, self.key)

        protoField.uid = 0
        for vertex in data[self.key].vertices():
            protoVertex = protoField.vertexList.add()
            protoVertex.uid = vertex.id()

        for edge in data[self.key].edges():
            protoEdge = protoField.edgeList.add()
            protoEdge.uid = edge.id()
            protoEdge.inVertexIndex = data[self.key].findVertexByID(edge.fromVertex())
            protoEdge.outVertexIndex = data[self.key].findVertexByID(edge.toVertex())


class GraphResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.GRAPH

    def parseProtoBuf(self, response, data):
        protoField = self.getProtoField(response)

        for vertex in protoField.vertexList:
            data[self.key].addVertex(QgsPointXY(0,0), -1, vertex.uid)

        for edge in protoField.edgeList:
            inVertexId = protoField.vertexList[edge.inVertexIndex].uid
            outVertexId = protoField.vertexList[edge.outVertexIndex].uid
            data[self.key].addEdge(inVertexId, outVertexId, -1, edge.uid)
