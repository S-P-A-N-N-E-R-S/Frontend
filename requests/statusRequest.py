from ..protocol.build import status_pb2, meta_pb2


class StatusRequest():

    def __init__(self):
        self.type = meta_pb2.RequestType.STATUS

    def toProtoBuf(self):
        return status_pb2.StatusRequest()
