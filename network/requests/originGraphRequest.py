from ..protocol.build import origin_graph_pb2, meta_pb2


class OriginGraphRequest():

    def __init__(self, jobId):
        self.type = meta_pb2.RequestType.ORIGIN_GRAPH
        self.jobId = jobId

    def toProtoBuf(self):
        proto = origin_graph_pb2.OriginGraphRequest()
        proto.jobId = self.jobId
        return proto
