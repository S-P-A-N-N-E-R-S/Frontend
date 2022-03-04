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


from ...views.widgets.QgsGraphVertexPickerWidget import QgsGraphVertexPickerWidget

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class VertexIDField(BaseField):
    type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_ID

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
        vertexPickerWidget = QgsGraphVertexPickerWidget(parent)
        vertexPickerWidget.toggleDialogVisibility.connect(parent.toggleDialogVisibility.emit)
        return vertexPickerWidget

    def getWidgetData(self, widget):
        return widget.getVertex()


class VertexIDResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_ID

    def parseProtoBuf(self, response, data):
        if "." in self.key:
            protoField = self.getProtoMapField(response)
            data[self.key] = protoField.attributes[0]
        else:
            protoField = self.getProtoField(response)
            data[self.key] = protoField

    def getResultString(self, data):
        result = data.get(self.key, None)
        if result:
            return f"{self.label}: {result}"
        return ""
