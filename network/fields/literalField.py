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


from .baseField import BaseField
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class LiteralField(BaseField):
    """Handler class for literal request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.LITERAL

    def toProtoBuf(self, request, _data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data

        :param request: Request the protobuf message will be placed in
        :param _data: Unused
        :raises ParseError: If the field name is invalid
        :raises ParseError: If the field key is invalid
        """

        if "." in self.key:
            fieldName, mapKey = self.key.split(".")
            try:
                protoField = getattr(request, fieldName).get_or_create(mapKey)
                protoField[0] = self.default
            except AttributeError as error:
                raise ParseError(f"Invalid field name: {fieldName}") from error
        else:
            try:
                setattr(request, self.key, self.default)
            except AttributeError as error:
                raise ParseError(f"Invalid key: {self.key}") from error
