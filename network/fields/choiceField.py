#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.


from PyQt5.QtWidgets import QComboBox

from .baseField import BaseField
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class ChoiceField(BaseField):
    """Handler class for choice request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.CHOICE

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data; Not implemented yet

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        """

        raise ParseError("Not implemented")

    def createWidget(self, parent):
        """
        Creates a widget for the request field

        :param parent: Parent of the created widget
        """

        widget = QComboBox(parent)
        choices = self.choices
        for choice in choices:
            choiceData = choices[choice]
            widget.addItem(choice, choiceData)
        # select default item if exist
        widget.setCurrentIndex(widget.findText(str(self.default)))
        return widget

    def getWidgetData(self, widget):
        """
        Returns the data of the specified widget

        :param widget: The widget containing the desired data
        :return: The widget data
        """

        return widget.currentData()
