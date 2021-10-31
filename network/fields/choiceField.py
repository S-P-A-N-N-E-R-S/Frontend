from PyQt5.QtWidgets import QComboBox

from .baseField import BaseField
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class ChoiceField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.CHOICE

    def toProtoBuf(self, request, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")

    def createWidget(self, parent):
        widget = QComboBox(parent)
        choices = self.choices
        for choice in choices:
            choiceData = choices[choice]
            widget.addItem(choice, choiceData)
        # select default item if exist
        widget.setCurrentIndex(widget.findText(str(self.default)))
        return widget

    def getWidgetData(self, widget):
        return widget.currentData()
