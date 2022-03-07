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

from PyQt5.QtWidgets import QCheckBox

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

    def createLabel(self):
        return None

    def createWidget(self, parent):
        widget = QCheckBox(self.label, parent)
        widget.setChecked(self.default is True)
        return widget

    def getWidgetData(self, widget):
        return widget.isChecked()
