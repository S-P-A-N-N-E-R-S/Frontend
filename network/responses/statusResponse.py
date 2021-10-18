from .. import statusManager
from ..protocol.build import meta_pb2, status_pb2


class StatusResponse():

    def __init__(self):
        self.type = meta_pb2.RequestType.STATUS

        self.jobStates = {}

    def parseProtoBuf(self, protoBuf):
        statusResponse = status_pb2.StatusResponse()
        protoBuf.response.Unpack(statusResponse)

        statusManager.insertJobStates(statusResponse.states)
