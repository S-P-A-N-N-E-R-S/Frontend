#  This file is part of the S.P.A.N.N.E.R.S. plugin.
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
    """Base class for all request fields"""

    type = None

    def __init__(self, key="", label="", default=None, required=False):
        """
        Constructor

        :param key: Key of the request field, defaults to ""
        :param label: Label for the request field, defaults to ""
        :param default: Default value for the request field, defaults to None
        :param required: Sets of the request field is required, defaults to False
        """

        self.key = key
        self.label = label
        self.default = default
        self.required = required

    def getInfo(self):
        """
        Returns a dictionairy containing field information

        :return: The desired field information
        """

        return {
            "type": self.type,
            "label": self.label,
            "default": self.default,
            "required": self.required,
        }

    def createLabel(self):
        """
        Creates and returns a label for the request field

        :return: Label for the request field
        """

        return QLabel(self.label)

    def createWidget(self, parent):
        """
        Creates a widget for the request field; Has to be implemented by specific request field

        :param parent: Parent of the created widget
        """

        raise AttributeError("Not implemented!")

    def getWidgetData(self, _widget):
        """
        Returns the data of the specified widget

        :param _widget: The widget containing the desired data
        :return: The widget data
        """

        return self.default

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data; Has to be implemented by specific request field

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        """

        raise AttributeError("Not implemented!")


class BaseResult:
    """Base class for all result fields"""

    type = None

    def __init__(self, key="", label=""):
        """
        Constructor

        :param key: Key of the result field, defaults to ""
        :param label: Label for the result field, defaults to ""
        """

        self.key = key
        self.label = label

    def getInfo(self):
        """
        Returns a dictionairy containing field information

        :return: The desired field information
        """

        return {
            "type": self.type,
            "label": self.label,
        }

    def getProtoField(self, response):
        """
        Returns the result field protobuf message contained in the specified response protobuf message

        :param response: Response containing the result field
        :raises ParseError: If the field key is invalid
        :return: The result field protobuf message
        """

        try:
            if not self.key in dir(response):
                return response.graphAttributes[self.key]
            return getattr(response, self.key)
        except AttributeError as error:
            raise ParseError(f"Invalid key: {self.key}") from error

    def getProtoMapField(self, response):
        """
        Returns the result field protobuf message contained in a map in the specified response protobuf message

        :param response: Response containing the map with the result field
        :raises ParseError: If the field name is invalid
        :return: The result field protobuf message
        """

        fieldName, mapKey = self.key.split(".")
        try:
            return getattr(response, fieldName)[mapKey]
        except AttributeError as error:
            raise ParseError(f"Invalid field name: {fieldName}") from error

    def getResultString(self, _data):
        """
        Returns the result string of the specified data

        :param _data: The result data
        :return: An empty string
        """

        return ""

    def parseProtoBuf(self, response, data):
        """
        Parses the result field from the specified response protobuf message into the specified data
        dictionairy; Has to be implemented by specific request field

        :param response: Protobuf message containing the result field to be parsed
        :param data: Dictionairy the data will be placed into
        """

        raise AttributeError("Not implemented!")


class GraphDependencyMixin():
    """Mixin for fields that depend on a graph"""

    graphKey = ""
