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


from PyQt5.QtWidgets import QComboBox

from .baseField import BaseField, BaseResult, GraphDependencyMixin
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2, generic_container_pb2


class EdgeCostsField(BaseField, GraphDependencyMixin):
    """Handler class for edge costs request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.EDGE_COSTS

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        :raises ParseError: If data does not contain the required key
        :raises ParseError: If the graph is unweighted
        :raises ParseError: If field name is invalid
        :raises ParseError: If the field key is invalid
        """

        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        for edgeId in data[self.graphKey].edges():
            if not data[self.graphKey].costOfEdge(edgeId, data[self.key]):
                raise ParseError("Algorithm requires a weighted graph")
            break

        if "." in self.key:
            fieldName, mapKey = self.key.split(".")
            try:
                protoField = getattr(request, fieldName).get_or_create(mapKey)
                protoField.type = generic_container_pb2.AttributeType.EDGE
                for edgeId in data[self.graphKey].edges():
                    edgeCost = data[self.graphKey].costOfEdge(edgeId, data[self.key])
                    protoField.attributes.append(edgeCost)
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                protoField = getattr(request, self.key)
                for edgeId in data[self.graphKey].edges():
                    edgeCost = data[self.graphKey].costOfEdge(edgeId, data[self.key])
                    protoField.append(edgeCost)
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error

    def createWidget(self, parent):
        """
        Creates a widget for the request field

        :param parent: Parent of the created widget
        """

        widget = QComboBox(parent)
        return widget

    def getWidgetData(self, widget):
        """
        Returns the data of the specified widget

        :param widget: The widget containing the desired data
        :return: The widget data
        """

        return widget.currentData()


class EdgeCostsResult(BaseResult, GraphDependencyMixin):
    """Handler class for edge costs result fields"""

    type = available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS

    def parseProtoBuf(self, response, data):
        """
        Parses the result field from the specified response protobuf message into the specified data
        dictionairy

        :param response: Protobuf message containing the result field to be parsed
        :param data: Dictionairy the data will be placed into
        """
        data[self.graphKey].setDistanceStrategy("Advanced")
        if "." in self.key:
            protoField = self.getProtoMapField(response)
            edgeIds = list(data[self.graphKey].edges().keys())
            for edgeIdx, edgeCost in enumerate(protoField.attributes):
                data[self.graphKey].setCostOfEdge(edgeIds[edgeIdx], data[self.key], edgeCost)
        else:
            protoField = self.getProtoField(response)
            edgeIds = list(data[self.graphKey].edges().keys())
            for edgeIdx, edgeCost in enumerate(protoField):
                data[self.graphKey].setCostOfEdge(edgeIds[edgeIdx], data[self.key], edgeCost)
