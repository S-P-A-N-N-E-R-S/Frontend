from PyQt5.QtWidgets import QSpinBox

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class IntField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.INT

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

    def createWidget(self, parent):
        widget = QSpinBox(parent)
        # highest minimum and maximum
        widget.setRange(-2147483648, 2147483647)
        if self.default and isinstance(self.default, int):
            widget.setValue(self.default)
        return widget

    def getWidgetData(self, widget):
        return widget.value()


class IntResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.INT

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

    def getResultString(self, data):
        result = data.get(self.key, None)
        if result:
            return f"{self.label}: {result}"
        return ""
