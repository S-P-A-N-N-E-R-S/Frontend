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
from ...models.extGraph import ExtGraph

from ..protocol.build import generic_container_pb2, available_handlers_pb2, meta_pb2


class BaseRequest():
    """Base class for job request handlers"""

    def __init__(self):
        """Constructor"""

        self.type = meta_pb2.RequestType.UNDEFINED_REQUEST
        self.protoRequest = generic_container_pb2.GenericRequest

        self.key = ""
        self.name = ""
        self.jobName = ""
        self.description = ""

        self.fields = {}
        self.data = {}

    def getFieldInfo(self):
        """
        Returns the information of all request fields as a dictionairy

        :return: Information of all request fields
        """

        fieldInfo = {}
        for fieldKey, field in self.fields.items():
            fieldInfo[fieldKey] = field.getInfo()
        return fieldInfo

    def setFieldData(self, key, data):
        """
        Sets the data of the request field with the specified field key

        :param key: Key of the request field
        :param data: Data for the request field
        :raises ParseError: If the field key is invalid
        """

        try:
            self.data[key] = data
        except KeyError as error:
            raise ParseError("Invalid field key") from error

    def resetData(self):
        """Resets all request field data"""

        self.data = {}

    def addField(self, field):
        """
        Adds the specified field to the saved request fields

        :param field: Field to be added
        """

        self.fields[field.key] = field

    def createWidget(self, fieldKey, parent):
        """
        Creates and returns the widget for the specified field

        :param fieldKey: Field key of the widget to be created
        :param parent: Parent set to be the parent of the widget
        :return: The created field widget
        """

        return self.fields[fieldKey].createWidget(parent)

    def getWidgetData(self, fieldKey, widget):
        """
        Returns the data of the specified field widget

        :param fieldKey: The field key of the widget
        :param widget: The widget containing the desired data
        :return: The widget data
        """

        return self.fields[fieldKey].getWidgetData(widget)

    def toProtoBuf(self):
        """
        Creates and returns the protobuf message of the request handler

        :return: The created protobuf message
        """

        request = self.protoRequest()

        for field in self.fields.values():
            field.toProtoBuf(request, self.data)

        return request


class BaseGraphRequest(BaseRequest):
    """Base class for job request handlers containing a graph"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.graphKey = ""

    def addField(self, field):
        """
        Adds the specified field to the saved request fields

        :param field: Field to be added
        """

        if isinstance(field, graphField.GraphField):
            self.graphKey = field.key
            for savedField in self.fields.values():
                if isinstance(savedField, baseField.GraphDependencyMixin):
                    savedField.graphKey = self.graphKey
        elif self.graphKey and isinstance(field, baseField.GraphDependencyMixin):
            field.graphKey = self.graphKey

        super().addField(field)

    def toProtoBuf(self):
        """
        Creates and returns the protobuf message of the request handler

        :return: The created protobuf message
        """

        request = self.protoRequest()

        if self.graphKey:
            self.fields[self.graphKey].toProtoBuf(request, self.data)

        for fieldKey, field in self.fields.items():
            if fieldKey != self.graphKey:
                field.toProtoBuf(request, self.data)

        return request


class BaseResponse():
    """Base class for job result handlers"""

    def __init__(self):
        """Constructor"""

        self.type = meta_pb2.RequestType.UNDEFINED_REQUEST
        self.protoResponse = generic_container_pb2.GenericResponse

        self.key = ""
        self.name = ""
        self.description = ""

        self.results = {}
        self.data = {}

    def getFieldInfo(self):
        """
        Returns the information of all response fields as a dictionairy

        :return: Information of all response fields
        """

        fieldInfo = {}
        for resultKey, result in self.results.items():
            fieldInfo[resultKey] = result.getInfo()
        return fieldInfo

    def getFieldData(self, key):
        """
        Returns the data of the response field with the specified field key

        :param key: Key of the response field
        :raises ParseError: If the field key is invalid
        """

        try:
            return self.data[key]
        except KeyError as error:
            raise ParseError("Invalid field key") from error

    def setFieldData(self, key, data):
        """
        Sets the data of the response field with the specified field key

        :param key: Key of the response field
        :param data: Data for the response field
        :raises ParseError: If the field key is invalid
        """

        try:
            self.data[key] = data
        except KeyError as error:
            raise ParseError("Invalid field key") from error

    def resetData(self):
        """Resets all response field data"""

        self.data = {}

    def addResult(self, result):
        """
        Adds the specified result field to the saved response fields

        :param field: Result field to be added
        """

        self.results[result.key] = result

    def getResultString(self):
        """
        Returns all field results as a string

        :return: Field results
        """

        resultString = ""
        for result in self.results.values():
            try:
                resultString += result.getResultString(self.data)
            except AttributeError:
                pass
            resultString += "\n"
        return resultString

    def parseProtoBuf(self, protoBuf):
        """
        Parses the specified protobuf message

        :param protoBuf: Protobuf message to be parsed
        """

        response = self.protoResponse()
        protoBuf.response.Unpack(response)

        for result in self.results.values():
            result.parseProtoBuf(response, self.data)


class BaseGraphResponse(BaseResponse):
    """Base class for job result handlers containing a graph"""

    def __init__(self):
        """Constructor"""

        super().__init__()

        self.graphKey = ""

    def getEdgeCostFields(self):
        """
        Returns list of all edge cost fields contained in the job result message

        :return: All edge cost fields
        """

        edgeCostFields = []
        for result in self.results.values():
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS:
                edgeCostFields.append(result)
        return edgeCostFields

    def getVertexCostFields(self):
        """
        Returns list of all vertex cost fields contained in the job result message

        :return: All vertex cost fields
        """

        vertexCostFields = []
        for result in self.results.values():
            if result.type == available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COSTS:
                vertexCostFields.append(result)
        return vertexCostFields

    def initGraphField(self):
        """Initializes the graph field by creating a new graph instance"""

        newGraph = ExtGraph()
        newGraph.setDistanceStrategy("None")
        self.data[self.graphKey] = newGraph

    def initCostFields(self):
        """Initializes all cost fields by resetting the cost index"""

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
        """
        Adds the specified result field to the saved response fields

        :param field: Result field to be added
        """

        if isinstance(result, graphField.GraphResult):
            self.graphKey = result.key
            for savedResult in self.results.values():
                if isinstance(savedResult, baseField.GraphDependencyMixin):
                    savedResult.graphKey = self.graphKey
        elif self.graphKey and isinstance(result, baseField.GraphDependencyMixin):
            result.graphKey = self.graphKey

        super().addResult(result)

    def resetData(self):
        """Resets all response field data"""

        super().resetData()
        self.initGraphField()
        self.initCostFields()

    def getGraph(self):
        """
        Returns the graph contained in the job result message

        :return: The graph contained in the job result message
        """

        return self.data[self.graphKey]

    def parseProtoBuf(self, protoBuf):
        """
        Parses the specified protobuf message

        :param protoBuf: Protobuf message to be parsed
        """

        response = self.protoResponse()
        protoBuf.response.Unpack(response)

        if self.graphKey:
            self.results[self.graphKey].parseProtoBuf(response, self.data)

        for resultKey, result in self.results.items():
            if resultKey != self.graphKey:
                result.parseProtoBuf(response, self.data)
