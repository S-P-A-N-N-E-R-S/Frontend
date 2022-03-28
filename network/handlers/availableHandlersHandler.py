#  This file is part of the S.P.A.N.N.E.R.S. plugin.
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


from .. import handlerManager
from ..exceptions import ParseError
from ..fields import boolField, choiceField, doubleField, edgeCostsField, edgeIDField, edgeIdArrayField, graphField, intField, literalField, stringField, vertexCoordinatesField, vertexCostsField, vertexIdArrayField, vertexIDField
from .genericHandler import GenericRequest, GenericResponse
from .shortestPathHandler import ShortestPathRequest, ShortestPathResponse

from ..protocol.build import available_handlers_pb2, meta_pb2

REQUEST = 0
RESPONSE = 1

REQUEST_TYPES = {
    meta_pb2.RequestType.GENERIC: (GenericRequest, GenericResponse),
    meta_pb2.RequestType.SHORTEST_PATH: (ShortestPathRequest, ShortestPathResponse),
}

FIELD_TYPES = {
    available_handlers_pb2.FieldInformation.FieldType.BOOL: boolField.BoolField,
    available_handlers_pb2.FieldInformation.FieldType.CHOICE: choiceField.ChoiceField,
    available_handlers_pb2.FieldInformation.FieldType.DOUBLE: doubleField.DoubleField,
    available_handlers_pb2.FieldInformation.FieldType.EDGE_COSTS: edgeCostsField.EdgeCostsField,
    available_handlers_pb2.FieldInformation.FieldType.EDGE_ID: edgeIDField.EdgeIDField,
    available_handlers_pb2.FieldInformation.FieldType.EDGE_ID_ARRAY: edgeIdArrayField.EdgeIdArrayField,
    available_handlers_pb2.FieldInformation.FieldType.GRAPH: graphField.GraphField,
    available_handlers_pb2.FieldInformation.FieldType.INT: intField.IntField,
    available_handlers_pb2.FieldInformation.FieldType.LITERAL: literalField.LiteralField,
    available_handlers_pb2.FieldInformation.FieldType.STRING: stringField.StringField,
    available_handlers_pb2.FieldInformation.FieldType.VERTEX_COORDINATES: vertexCoordinatesField.VertexCoordinatesField,
    available_handlers_pb2.FieldInformation.FieldType.VERTEX_COSTS: vertexCostsField.VertexCostsField,
    available_handlers_pb2.FieldInformation.FieldType.VERTEX_ID: vertexIDField.VertexIDField,
    available_handlers_pb2.FieldInformation.FieldType.VERTEX_ID_ARRAY: vertexIdArrayField.VertexIdArrayField,
}

RESULT_TYPES = {
    available_handlers_pb2.ResultInformation.HandlerReturnType.DOUBLE: doubleField.DoubleResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS: edgeCostsField.EdgeCostsResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_ID: edgeIDField.EdgeIDResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_ID_ARRAY: edgeIdArrayField.EdgeIdArrayResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.GRAPH: graphField.GraphResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.INT: intField.IntResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.STRING: stringField.StringResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COORDINATES: vertexCoordinatesField.VertexCoordinatesResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COSTS: vertexCostsField.VertexCostsResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_ID: vertexIDField.VertexIDResult,
    available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_ID_ARRAY: vertexIdArrayField.VertexIdArrayResult,
}


class AvailableHandlersResponse:
    """Handler class for the available handlers response"""

    def __init__(self):
        """Constructor"""

        self.type = meta_pb2.RequestType.AVAILABLE_HANDLERS

    def parseProtoBuf(self, protoBuf):
        """
        Creates and saves the available handlers included in the specified protobuf message

        :param protoBuf: Protobuf message to be parsed
        :raises ParseError: If the type of a handler is unknown
        """

        # if protoBuf.type != self.type:
        #     raise ParseError(f"Invalid response type: {protoBuf.type}")

        response = available_handlers_pb2.AvailableHandlersResponse()
        protoBuf.response.Unpack(response)

        for handler in response.handlers:
            try:
                requestObj = REQUEST_TYPES[handler.request_type][REQUEST]()
                responseObj = REQUEST_TYPES[handler.request_type][RESPONSE]()
            except KeyError as error:
                raise ParseError(f"Unknown handler type: {handler.request_type}") from error

            requestObj.name = handler.name
            requestObj.description = handler.description

            for field in handler.fields:
                requestObj.addField(self.parseField(field))

            responseObj.name = handler.name
            responseObj.description = handler.description

            for result in handler.results:
                responseObj.addResult(self.parseResult(result))

            if not requestObj.key:
                # raise ParseError("Missing handlerType")
                requestObj.key = requestObj.name

            responseObj.key = requestObj.key

            handlerManager.insertHandlerPair(requestObj, responseObj)

    def parseField(self, field):
        """
        Creates a field object from the specified field message

        :param field: Field message to be parsed
        :raises ParseError: If the field type is unknown
        :raises ParseError: If the field type is missing
        :return: The resulting field object
        """

        try:
            fieldObj = FIELD_TYPES[field.type]()
        except KeyError as error:
            raise ParseError(f"Unknown field type: {field.type}") from error

        fieldObj.key = field.key
        fieldObj.label = field.label

        if isinstance(fieldObj, literalField.LiteralField) and not field.default:
            raise ParseError("Missing handlerType")

        fieldObj.default = field.default
        fieldObj.required = field.required

        if field.type == available_handlers_pb2.FieldInformation.FieldType.CHOICE:
            fieldObj.choices = field.choices

        return fieldObj

    def parseResult(self, result):
        """
        Creates a result object from the specified result message

        :param field: Result message to be parsed
        :raises ParseError: If the field type is unknown
        :return: The resulting result object
        """
        try:
            fieldObj = RESULT_TYPES[result.type]()
        except KeyError as error:
            raise ParseError(f"Unknown field type: {result.type}") from error

        fieldObj.key = result.key
        fieldObj.label = result.label

        return fieldObj
