from PyQt5.QtWidgets import QComboBox

from .baseField import BaseField, BaseResult, GraphDependencyMixin
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2, generic_container_pb2


class EdgeCostsField(BaseField, GraphDependencyMixin):
    type = available_handlers_pb2.FieldInformation.FieldType.EDGE_COSTS

    def toProtoBuf(self, request, data):
        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        if not data[self.graphKey].costOfEdge(0, data[self.key]):
            raise ParseError("Algortihm requires a weighted graph")

        if "." in self.key:
            fieldName, mapKey = self.key.split(".")
            try:
                protoField = getattr(request, fieldName).get_or_create(mapKey)
                protoField.type = generic_container_pb2.AttributeType.EDGE
                for edgeIdx, _edge in enumerate(data[self.graphKey].edges()):
                    edgeCost = data[self.graphKey].costOfEdge(edgeIdx, data[self.key])
                    protoField.attributes.append(edgeCost)
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                protoField = getattr(request, self.key)
                for edgeIdx, _edge in enumerate(data[self.graphKey].edges()):
                    edgeCost = data[self.graphKey].costOfEdge(edgeIdx, data[self.key])
                    protoField.append(edgeCost)
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error

    def createWidget(self, parent):
        widget = QComboBox(parent)
        return widget

    def getWidgetData(self, widget):
        return widget.currentData()


class EdgeCostsResult(BaseResult, GraphDependencyMixin):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS

    def parseProtoBuf(self, response, data):
        if "." in self.key:
            protoField = self.getProtoMapField(response)
            for edgeIdx, edgeCost in enumerate(protoField.attributes):
                data[self.graphKey].setCostOfEdge(edgeIdx, data[self.key], edgeCost)
        else:
            protoField = self.getProtoField(response)
            for edgeIdx, edgeCost in enumerate(protoField):
                data[self.graphKey].setCostOfEdge(edgeIdx, data[self.key], edgeCost)
