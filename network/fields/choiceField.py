from .baseField import BaseField
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class ChoiceField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.CHOICE

    def toProtoBuf(self, request, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")
