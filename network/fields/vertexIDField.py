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


from ...views.widgets.graphVertexPickerWidget import GraphVertexPickerWidget

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class VertexIDField(BaseField):
    """Handler class for vertex id request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_ID

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        :raises ParseError: If data does not contain the required key
        :raises ParseError: If the field name is invalid
        :raises ParseError: If the field key is invalid
        """

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
        """
        Creates a widget for the request field

        :param parent: Parent of the created widget
        """

        vertexPickerWidget = GraphVertexPickerWidget(parent)
        vertexPickerWidget.toggleDialogVisibility.connect(parent.toggleDialogVisibility.emit)
        return vertexPickerWidget

    def getWidgetData(self, widget):
        """
        Returns the data of the specified widget

        :param widget: The widget containing the desired data
        :return: The widget data
        """

        return widget.getVertex()


class VertexIDResult(BaseResult):
    """Handler class for vertex id result fields"""

    type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_ID

    def parseProtoBuf(self, response, data):
        """
        Parses the result field from the specified response protobuf message into the specified data
        dictionairy

        :param response: Protobuf message containing the result field to be parsed
        :param data: Dictionairy the data will be placed into
        """

        if "." in self.key:
            protoField = self.getProtoMapField(response)
            data[self.key] = protoField.attributes[0]
        else:
            protoField = self.getProtoField(response)
            data[self.key] = protoField

    def getResultString(self, data):
        """
        Returns the result string of the specified data

        :param _data: The result data
        :return: The result string
        """

        result = data.get(self.key, None)
        if result:
            return f"{self.label}: {result}"
        return ""
