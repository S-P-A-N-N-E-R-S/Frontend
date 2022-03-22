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


from ..protocol.build import meta_pb2, new_job_response_pb2


class NewJobResponse():
    """Response handler for the new job response"""

    def __init__(self):
        """Constructor"""

        self.type = meta_pb2.RequestType.NEW_JOB_RESPONSE

    def parseProtoBuf(self, protoBuf):
        """
        Parses the specified protobuf message

        :param protoBuf: The protobuf message to be parsed
        """

        newJobResponse = new_job_response_pb2.NewJobResponse()
        protoBuf.response.Unpack(newJobResponse)

        self.jobId = newJobResponse.jobId
