from ..protocol.build import meta_pb2

class EmptyResponse:

    def __init__(self):
        self.types = [
            meta_pb2.RequestType.AUTH,
            meta_pb2.RequestType.CREATE_USER,
        ]

    def parseProtoBuf(self, _protoBuf):
        return
