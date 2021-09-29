from ..exceptions import ParseError
from ..fields import graphField, baseField

from ..protocol.build import generic_container_pb2, meta_pb2


class BaseRequest():

    def __init__(self):
        self.type = meta_pb2.RequestType.UNDEFINED_REQUEST
        self.protoRequest = generic_container_pb2.GenericRequest

        self.key = ""
        self.name = ""
        self.description = ""

        self.fields = {}
        self.data = {}

    def getFieldInfo(self):
        fieldInfo = {}
        for fieldKey, field in self.fields.items():
            fieldInfo[fieldKey] = field.getInfo()
        return fieldInfo

    def setFieldData(self, key, data):
        try:
            self.data[key] = data
        except KeyError as error:
            raise ParseError("Invalid data key") from error

    def resetData(self):
        self.data = {}

    def addField(self, field):
        self.fields[field.key] = field

    def toProtoBuf(self):
        request = self.protoRequest()

        for field in self.fields.values():
            field.toProtoBuf(request, self.data)

        return request


class BaseGraphRequest(BaseRequest):

    def __init__(self):
        super().__init__()

        self.graphKey = ""

    def addField(self, field):
        if isinstance(field, graphField.GraphField):
            self.graphKey = field.key
            for savedField in self.fields.values():
                if isinstance(savedField, baseField.GraphDependencyMixin):
                    savedField.graphKey = self.graphKey
        elif self.graphKey and isinstance(field, baseField.GraphDependencyMixin):
            field.graphKey = self.graphKey

        super().addField(field)

    def toProtoBuf(self):
        request = self.protoRequest()

        if self.graphKey:
            self.fields[self.graphKey].toProtoBuf(request, self.data)

        for fieldKey, field in self.fields.items():
            if fieldKey != self.graphKey:
                field.toProtoBuf(request, self.data)

        return request
