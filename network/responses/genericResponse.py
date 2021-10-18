from .baseResponse import BaseGraphResponse
from ..protocol.build import generic_container_pb2, meta_pb2


class GenericResponse(BaseGraphResponse):

    def __init__(self):
        super().__init__()

        self.type = meta_pb2.RequestType.GENERIC
        self.protoResponse = generic_container_pb2.GenericResponse
