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


from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class EdgeIdArrayField(BaseField):
    """Handler class for edge id array request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.EDGE_ID_ARRAY

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data; Not implemented yet

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        """

        raise ParseError("Not implemented")


class EdgeIdArrayResult(BaseResult):
    """Handler class for edge id array result fields"""

    type = available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_ID_ARRAY

    def parseProtoBuf(self, response, data):
        """
        Parses the result field from the specified response protobuf message into the specified data
        dictionairy; Not implemented yet

        :param response: Protobuf message containing the result field to be parsed
        :param data: Dictionairy the data will be placed into
        """

        raise ParseError("Not implemented")
