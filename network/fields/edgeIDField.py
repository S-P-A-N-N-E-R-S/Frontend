from ...views.widgets.QgsGraphEdgePickerWidget import QgsGraphEdgePickerWidget

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class EdgeIDField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.EDGE_ID

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
                protoField.attributes.append(data[self.key])
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                setattr(request, self.key, data[self.key])
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error

    def createWidget(self, parent):
        edgePickerWidget = QgsGraphEdgePickerWidget(parent)
        edgePickerWidget.toggleDialogVisibility.connect(lambda visible: parent.toggleDialogVisibility.emit(visible))
        return edgePickerWidget

    def getWidgetData(self, widget):
        return widget.getEdge()


class EdgeIDResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_ID

    def parseProtoBuf(self, response, data):
        if "." in self.key:
            protoField = self.getProtoMapField(response)
            data[self.key] = protoField.attributes[0]
        else:
            protoField = self.getProtoField(response)
            data[self.key] = protoField
