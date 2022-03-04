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
    type = available_handlers_pb2.FieldInformation.FieldType.EDGE_ID_ARRAY

    def toProtoBuf(self, request, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")


class EdgeIdArrayResult(BaseResult):
    type = available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_ID_ARRAY

    def parseProtoBuf(self, response, data):
        # ExtGraph does not implement a function to get vertex costs yet
        raise ParseError("Not implemented")
