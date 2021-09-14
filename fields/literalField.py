from .baseField import BaseField
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class LiteralField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.LITERAL

    def toProtoBuf(self, request, _data):
        if "." in self.key:
            fieldName, mapKey = self.key.split(".")
            try:
                protoField = getattr(request, fieldName).get_or_create(mapKey)
                protoField[0] = self.default
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                setattr(request, self.key, self.default)
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error
