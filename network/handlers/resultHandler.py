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


from ..protocol.build import result_pb2, meta_pb2


class ResultRequest():
    """Request handler for the job result request"""

    def __init__(self, jobId):
        """
        Constructor

        :param jobId: ID of the desired job result
        """

        self.type = meta_pb2.RequestType.RESULT
        self.jobId = jobId

    def toProtoBuf(self):
        """
        Creates and returns the protobuf message of the job result request

        :return: The created job result request
        """

        proto = result_pb2.ResultRequest()
        proto.jobId = self.jobId
        return proto
