from ..protocol.build import abort_job_pb2, meta_pb2


class AbortJobRequest():

    def __init__(self, jobId):
        self.type = meta_pb2.RequestType.ABORT_JOB
        self.jobId = jobId

    def toProtoBuf(self):
        proto = abort_job_pb2.AbortJobRequest()
        proto.jobId = self.jobId
        return proto
