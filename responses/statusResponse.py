from ..protocol.build import meta_pb2, status_pb2


class StatusResponse():

    def __init__(self):
        self.type = meta_pb2.RequestType.STATUS

        self.jobStates = {}

    def parseProtoBuf(self, protoBuf):
        statusRes = status_pb2.StatusResponse()
        protoBuf.response.Unpack(statusRes)

        for state in statusRes.states:
            self.jobStates[state.job_id] = {
                'status': state.status
            }
