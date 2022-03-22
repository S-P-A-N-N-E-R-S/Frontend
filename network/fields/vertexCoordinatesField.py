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


from .baseField import BaseField, BaseResult, GraphDependencyMixin
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class VertexCoordinatesField(BaseField, GraphDependencyMixin):
    """Handler class for vertex coordinates request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_COORDINATES

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        :raises ParseError: If data does not contain the required key
        """

        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        protoField = getattr(request, self.key)
        for vertex in data[self.graphKey].vertices():
            point = vertex.point()
            vertexCoordinates = protoField.add()
            vertexCoordinates.x = point.x()
            vertexCoordinates.y = point.y()
            #TODO Include possible z coordinates in protobuf


class VertexCoordinatesResult(BaseResult, GraphDependencyMixin):
    """Handler class for vertex coordinates result fields"""

    type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COORDINATES

    def parseProtoBuf(self, response, data):
        """
        Parses the result field from the specified response protobuf message into the specified data
        dictionairy

        :param response: Protobuf message containing the result field to be parsed
        :param data: Dictionairy the data will be placed into
        """

        protoField = self.getProtoField(response)
        for idx, vertexCoordinates in enumerate(protoField):
            vertex = data[self.graphKey].vertex(idx)
            vertex.point().setX(vertexCoordinates.x)
            vertex.point().setY(vertexCoordinates.y)
            #TODO Parse possible z coordinates from protobuf
