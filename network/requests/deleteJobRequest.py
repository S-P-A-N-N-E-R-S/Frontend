from ..protocol.build import delete_job_pb2, meta_pb2


class DeleteJobRequest():

    def __init__(self, jobId):
        self.type = meta_pb2.RequestType.DELETE_JOB
        self.jobId = jobId

    def toProtoBuf(self):
        proto = delete_job_pb2.DeleteJobRequest()
        proto.jobId = self.jobId
        return proto
