from .baseField import BaseField
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class BoolField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.BOOL

    def toProtoBuf(self, request, data):
        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        if "." in self.key:
            fieldName, mapKey = self.key.split(".")
            try:
                protoField = getattr(request, fieldName).get_or_create(mapKey)
                protoField[0] = str(int(data[self.key]))
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
            except ValueError as error:
                raise ParseError(f"Invalid value: {data[self.key]}") from error
        else:
            try:
                setattr(request, self.key, str(int(data[self.key])))
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error
            except ValueError as error:
                raise ParseError(f"Invalid value: {data[self.key]}") from error
