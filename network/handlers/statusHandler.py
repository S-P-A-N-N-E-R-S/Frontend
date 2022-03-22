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

from .. import statusManager

from ..protocol.build import status_pb2, meta_pb2


class StatusRequest():
    """Request handler for the status request"""

    def __init__(self):
        """Constructor"""

        self.type = meta_pb2.RequestType.STATUS

    def toProtoBuf(self):
        """
        Creates and returns the protobuf message of the status request

        :return: The created protobuf message
        """

        return status_pb2.StatusRequest()


class StatusResponse():
    """Response handler for the status response"""

    def __init__(self):
        """Constructor"""

        self.type = meta_pb2.RequestType.STATUS

        self.jobStates = {}

    def parseProtoBuf(self, protoBuf):
        """
        Parses the specified protobuf message

        :param protoBuf: The protobuf message to be parsed
        """

        statusResponse = status_pb2.StatusResponse()
        protoBuf.response.Unpack(statusResponse)

        statusManager.insertJobStates(statusResponse.states)
