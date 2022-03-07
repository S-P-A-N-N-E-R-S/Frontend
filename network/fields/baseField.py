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

from PyQt5.QtWidgets import QLabel

from ..exceptions import ParseError

class BaseField:
    type = None

    def __init__(self, key="", label="", default=None, required=False):
        self.key = key
        self.label = label
        self.default = default
        self.required = required

    def getInfo(self):
        return {
            "type": self.type,
            "label": self.label,
            "default": self.default,
            "required": self.required,
        }

    def createLabel(self):
        return QLabel(self.label)

    def createWidget(self, parent):
        raise AttributeError("Not implemented!")

    def getWidgetData(self, _widget):
        return self.default


class BaseResult:
    type = None

    def __init__(self, key="", label=""):
        self.key = key
        self.label = label

    def getInfo(self):
        return {
            "type": self.type,
            "label": self.label,
        }

    def getProtoField(self, response):   
        try:
            if not self.key in dir(response):
                return response.graphAttributes[self.key]
            return getattr(response, self.key)
        except AttributeError as error:
            raise ParseError(f"Invalid key: {self.key}") from error

    def getProtoMapField(self, response):
        fieldName, mapKey = self.key.split(".")
        try:
            return getattr(response, fieldName)[mapKey]
        except AttributeError as error:
            raise ParseError(f"Invalid field name: {fieldName}") from error

    def getResultString(self, _data):
        return ""


class GraphDependencyMixin():
    graphKey = ""
