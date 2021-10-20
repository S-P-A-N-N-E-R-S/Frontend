from ..protocol.build import result_pb2, meta_pb2


class ResultRequest():

    def __init__(self, jobId):
        self.type = meta_pb2.RequestType.RESULT
        self.jobId = jobId

    def toProtoBuf(self):
        proto = result_pb2.ResultRequest()
        proto.jobId = self.jobId
        return proto
