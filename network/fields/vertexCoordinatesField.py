from .baseField import BaseField, BaseResult, GraphDependencyMixin
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class VertexCoordinatesField(BaseField, GraphDependencyMixin):
    type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_COORDINATES

    def toProtoBuf(self, request, data):
        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        protoField = getattr(request, self.key)
        for vertex in data[self.graphKey].vertices():
            point = vertex.point()
            vertexCoordinates = protoField.add()
            vertexCoordinates.x = point.x()
            vertexCoordinates.y = point.y()
            #TODO Include possible z coordinates in protobuf


class VertexCoordinatesResult(BaseResult, GraphDependencyMixin):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COORDINATES

    def parseProtoBuf(self, response, data):
        protoField = self.getProtoField(response)
        for idx, vertexCoordinates in enumerate(protoField):
            vertex = data[self.graphKey].vertex(idx)
            vertex.point().setX(vertexCoordinates.x)
            vertex.point().setY(vertexCoordinates.y)
            #TODO Parse possible z coordinates from protobuf
