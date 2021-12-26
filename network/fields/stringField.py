from PyQt5.QtWidgets import QLineEdit

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class StringField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.STRING

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
                protoField[0] = data[self.key]
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                setattr(request, self.key, data[self.key])
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error

    def createWidget(self, parent):
        widget = QLineEdit(str(self.default), parent)
        return widget

    def getWidgetData(self, widget):
        return widget.text() if len(widget.text()) > 0 else None


class StringResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.STRING

    def parseProtoBuf(self, response, data):
        if "." in self.key:
            protoMapField = self.getProtoMapField(response)
            data[self.key] = protoMapField[0]
        else:
            protoField = self.getProtoField(response)
            data[self.key] = protoField

    def getResultString(self, data):
        result = data.get(self.key, None)
        if result:
            return f"{self.label}: {result}"
        return ""
