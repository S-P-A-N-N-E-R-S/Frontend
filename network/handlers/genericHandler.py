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


from .baseHandler import BaseGraphRequest, BaseGraphResponse
from ..fields import literalField

from ..protocol.build import generic_container_pb2, meta_pb2


class GenericRequest(BaseGraphRequest):
    """Request handler for the generic job request"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.type = meta_pb2.RequestType.GENERIC
        self.protoRequest = generic_container_pb2.GenericRequest

    def addField(self, field):
        """
        Adds the specified field to the saved request fields

        :param field: Field to be added
        """

        if isinstance(field, literalField.LiteralField):
            self.key = field.default

        super().addField(field)


class GenericResponse(BaseGraphResponse):
    """Response handler for the generic job result response"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.type = meta_pb2.RequestType.GENERIC
        self.protoResponse = generic_container_pb2.GenericResponse
