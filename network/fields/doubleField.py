from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class DoubleField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.DOUBLE

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
                if fieldName == 'graphAttributes':
                    getattr(request, fieldName)[mapKey] = str(data[self.key])
                else:
                    protoField = getattr(request, fieldName).get_or_create(mapKey)
                    protoField.attributes.append(data[self.key])
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                setattr(request, self.key, data[self.key])
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error


class DoubleResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.DOUBLE

    def parseProtoBuf(self, response, data):
        if "." in self.key:
            protoField = self.getProtoMapField(response)
            if 'graphAttributes' in self.key:
                data[self.key] = float(protoField.attributes[0])
            else:
                data[self.key] = protoField.attributes[0]
        else:
            protoField = self.getProtoField(response)
            data[self.key] = protoField
