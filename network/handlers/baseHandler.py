#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.


from ..exceptions import ParseError
from ..fields import graphField, baseField
from ...models.ExtGraph import ExtGraph

from ..protocol.build import generic_container_pb2, available_handlers_pb2, meta_pb2


class BaseRequest():

    def __init__(self):
        self.type = meta_pb2.RequestType.UNDEFINED_REQUEST
        self.protoRequest = generic_container_pb2.GenericRequest

        self.key = ""
        self.name = ""
        self.jobName = ""
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

    def createWidget(self, fieldKey, parent):
        return self.fields[fieldKey].createWidget(parent)

    def getWidgetData(self, fieldKey, widget):
        return self.fields[fieldKey].getWidgetData(widget)

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

    def getResultString(self):
        resultString = ""
        for result in self.results.values():
            try:
                resultString += result.getResultString(self.data)
            except AttributeError:
                pass
            resultString += "\n"
        return resultString

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

    def initGraphField(self):
        newGraph = ExtGraph()
        newGraph.setDistanceStrategy("None")
        self.data[self.graphKey] = newGraph

    def initCostFields(self):
        edgeCostIndex = 0
        vertexCostIndex = 0
        for result in self.results.values():
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS:
                self.data[result.key] = edgeCostIndex
                edgeCostIndex += 1
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COSTS:
                self.data[result.key] = vertexCostIndex
                vertexCostIndex += 1

    def addResult(self, result):
        if isinstance(result, graphField.GraphResult):
            self.graphKey = result.key
            for savedResult in self.results.values():
                if isinstance(savedResult, baseField.GraphDependencyMixin):
                    savedResult.graphKey = self.graphKey
        elif self.graphKey and isinstance(result, baseField.GraphDependencyMixin):
            result.graphKey = self.graphKey

        super().addResult(result)

    def resetData(self):
        super().resetData()
        self.initGraphField()
        self.initCostFields()

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
