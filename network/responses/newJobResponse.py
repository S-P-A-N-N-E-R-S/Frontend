from ..protocol.build import meta_pb2, new_job_response_pb2


class NewJobResponse():

    def __init__(self):
        self.type = meta_pb2.RequestType.NEW_JOB_RESPONSE

    def parseProtoBuf(self, protoBuf):
        newJobResponse = new_job_response_pb2.NewJobResponse()
        protoBuf.response.Unpack(newJobResponse)

        self.jobId = newJobResponse.jobId
