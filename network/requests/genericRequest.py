from .baseRequest import BaseGraphRequest
from ..fields import literalField
from ..protocol.build import generic_container_pb2, meta_pb2


class GenericRequest(BaseGraphRequest):

    def __init__(self):
        super().__init__()

        self.type = meta_pb2.RequestType.GENERIC
        self.protoRequest = generic_container_pb2.GenericRequest

    def addField(self, field):
        if isinstance(field, literalField.LiteralField):
            self.key = field.default

        super().addField(field)
