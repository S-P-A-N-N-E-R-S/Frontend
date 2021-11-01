from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class VertexIdArrayField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_ID_ARRAY

    def toProtoBuf(self, request, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")


class VertexIdArrayResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_ID_ARRAY

    def parseProtoBuf(self, response, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")
