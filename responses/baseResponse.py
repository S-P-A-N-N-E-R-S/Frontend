from ..exceptions import ParseError
from ..fields import graphField, baseField

from ..protocol.build import generic_container_pb2, available_handlers_pb2, meta_pb2

from ...models.ExtGraph import ExtGraph


class BaseResponse():

    def __init__(self):
        self.type = meta_pb2.RequestType.UNDEFINED_REQUEST
        self.protoResponse = generic_container_pb2.GenericResponse

        self.key = ""
        self.name = ""
        self.description = ""

        self.results = {}
        self.data = {}

    def getFieldInfo(self):
        fieldInfo = {}
        for resultKey, result in self.results.items():
            fieldInfo[resultKey] = result.getInfo()
        return fieldInfo

    def getFieldData(self, key):
        try:
            return self.data[key]
        except KeyError as error:
            raise ParseError("Invalid data key") from error

    def setFieldData(self, key, data):
        try:
            self.data[key] = data
        except KeyError as error:
            raise ParseError("Invalid data key") from error

    def resetData(self):
        self.data = {}

    def addResult(self, result):
        self.results[result.key] = result

    def parseProtoBuf(self, protoBuf):
        response = self.protoResponse()
        protoBuf.response.Unpack(response)

        for result in self.results.values():
            result.parseProtoBuf(response, self.data)


class BaseGraphResponse(BaseResponse):

    def __init__(self):
        super().__init__()

        self.graphKey = ""

    def getEdgeCostFields(self):
        edgeCostFields = []
        for result in self.results.values():
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS:
                edgeCostFields.append(result)
        return edgeCostFields

    def getVertexCostFields(self):
        vertexCostFields = []
        for result in self.results.values():
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COSTS:
                vertexCostFields.append(result)
        return vertexCostFields

    def initEdgeCostFields(self):
        for index, result in enumerate(self.results.values()):
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS:
                self.data[result.key] = index

    def initVertexCostFields(self):
        for index, result in enumerate(self.results.values()):
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COSTS:
                self.data[result.key] = index

    def addResult(self, result):
        if isinstance(result, graphField.GraphResult):
            self.graphKey = result.key
            self.data[self.graphKey] = ExtGraph()
            for savedResult in self.results.values():
                if isinstance(savedResult, baseField.GraphDependencyMixin):
                    savedResult.graphKey = self.graphKey
        elif self.graphKey and isinstance(result, baseField.GraphDependencyMixin):
            result.graphKey = self.graphKey

        super().addResult(result)

    def resetData(self):
        super().resetData()
        self.data[self.graphKey] = ExtGraph()
        self.initEdgeCostFields()
        self.initVertexCostFields()

    def getGraph(self):
        return self.data[self.graphKey]

    def parseProtoBuf(self, protoBuf):
        response = self.protoResponse()
        protoBuf.response.Unpack(response)

        if self.graphKey:
            self.results[self.graphKey].parseProtoBuf(response, self.data)

        for resultKey, result in self.results.items():
            if resultKey != self.graphKey:
                result.parseProtoBuf(response, self.data)
