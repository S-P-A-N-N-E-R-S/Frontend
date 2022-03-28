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


from ..protocol.build import meta_pb2


class EmptyResponse:
    """Helper class for an empty response handler"""

    def __init__(self):
        """Constructor"""

        self.types = [
            meta_pb2.RequestType.AUTH,
            meta_pb2.RequestType.CREATE_USER,
        ]

    def parseProtoBuf(self, _protoBuf):
        """
        Helper function

        :param _protoBuf: Unused
        """

        return
