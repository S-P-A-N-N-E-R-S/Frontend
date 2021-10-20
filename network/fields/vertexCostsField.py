from .baseField import BaseField, BaseResult, GraphDependencyMixin
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2, generic_container_pb2


class VertexCostsField(BaseField, GraphDependencyMixin):
    type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_COSTS

    def toProtoBuf(self, request, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")


class VertexCostsResult(BaseResult, GraphDependencyMixin):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COSTS

    def parseProtoBuf(self, response, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")
