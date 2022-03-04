#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Timo Glane, Leon Nienhüser
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


from qgis.core import QgsSettings, QgsApplication, QgsAuthMethodConfig

from . import parserManager, statusManager
from .exceptions import ParseError, ServerError
from .protocol.build import container_pb2, error_pb2, meta_pb2

from .responses.availableHandlersResponse import AvailableHandlersResponse
from .responses.emptyResponse import EmptyResponse
from .responses.genericResponse import GenericResponse
from .responses.newJobResponse import NewJobResponse
from .responses.originGraphResponse import OriginGraphResponse
from .responses.shortestPathResponse import ShortestPathResponse
from .responses.statusResponse import StatusResponse


ERROR_TYPES = {
    error_pb2.ErrorType.UNKNOWN_ERROR: "an unknown error",
    error_pb2.ErrorType.UNAUTHORIZED: "an authorization error",
}


def createProtoBuf(request):
    protoBuf = container_pb2.RequestContainer()

    try:
        requestMessage = request.toProtoBuf()
    except AttributeError as attributeError:
        raise ParseError("Method not defined") from attributeError
    protoBuf.request.Pack(requestMessage)

    return protoBuf.SerializeToString()


def getMetaStringFromType(requestType):
    metaData = meta_pb2.MetaData()
    getAuthenticationData(metaData)
    metaData.containerSize = 0
    metaData.type = requestType
    return metaData.SerializeToString()


def getMetaStringFromRequest(request, requestStringLen):
    metaData = meta_pb2.MetaData()
    getAuthenticationData(metaData)
    metaData.containerSize = requestStringLen
    metaData.type = request.type

    if getattr(request, "key", None):
        metaData.handlerType = request.key

    if getattr(request, "jobName", None):
        metaData.jobName = request.jobName

    metaString = metaData.SerializeToString()

    return metaString


def getAuthenticationData(metaData):
    settings = QgsSettings()
    authId = settings.value("ogdfplugin/authId")
    authMgr = QgsApplication.authManager()
    if not authId or not authId in authMgr.configIds():
        raise ParseError("Invalid authID")

    authCfg = QgsAuthMethodConfig()
    # load config from manager to the new config instance and decrypt sensitive data
    authMgr.loadAuthenticationConfig(authId, authCfg, True)
    authCfg.setName("ogdfplugin/serverAuth")

    username = authCfg.config("username", "")
    if not username:
        raise ParseError("Missing username")

    password = authCfg.config("password", "")
    if not password:
        raise ParseError("Missing password")

    metaData.user.name = username
    metaData.user.password = password


def parseMetaData(metaString):
    metaData = meta_pb2.MetaData()
    metaData.ParseFromString(metaString)
    if metaData.containerSize <= 0 and metaData.type != meta_pb2.RequestType.AUTH:
        raise ParseError("Empty Message")
    return metaData


def parseProtoBuf(protoBufString, responseType, handlerType=None):
    if responseType == meta_pb2.RequestType.ERROR:
        parseError(protoBufString)

    protoBuf = container_pb2.ResponseContainer()
    protoBuf.ParseFromString(protoBufString)

    if protoBuf.status == container_pb2.ResponseContainer.StatusCode.OK:

        if protoBuf.HasField("statusData"):
            statusManager.insertJobState(protoBuf.statusData)

        if responseType == meta_pb2.RequestType.GENERIC:
            if not handlerType:
                raise ParseError("Missing handler type")

            # Get specific generic response for request
            response = parserManager.getResponseParser(handlerType)
        else:
            response = getResponseByType(responseType)()
            if not response:
                raise ParseError("Unknown response key")

        try:
            response.parseProtoBuf(protoBuf)
            return response
        except AttributeError as attributeError:
            raise ParseError("Method not defined") from attributeError

    elif protoBuf.status == container_pb2.ResponseContainer.StatusCode.ERROR:
        raise ServerError("Server responded with unspecified error")
    elif protoBuf.status == container_pb2.ResponseContainer.StatusCode.READ_ERROR:
        raise ServerError("Server responded with error: READ_ERROR")
    elif protoBuf.status == container_pb2.ResponseContainer.StatusCode.PROTO_PARSING_ERROR:
        raise ServerError("Server responded with error: PROTO_PARSING_ERROR")
    elif protoBuf.status == container_pb2.ResponseContainer.StatusCode.INVALID_REQUEST_ERROR:
        raise ServerError("Server responded with error: INVALID_REQUEST_ERROR")
    else:
        raise ParseError("Server responded with unknown status code")


def parseError(protoBufString):
    errorMessage = error_pb2.ErrorMessage()
    errorMessage.ParseFromString(protoBufString)

    error = "Server responded with"

    errorType = ERROR_TYPES.get(errorMessage.type)
    if errorType:
        error = f"{error} {errorType}"
    else:
        error = f"{error} an unspecified error"
    if errorMessage.message:
        error = f"{error}: {errorMessage.message}"
    raise ServerError(error)


def getResponseByType(requestType):
    # Return the correct default constructed response type by the type field provied by meta data
    try:
        return {
            meta_pb2.RequestType.ABORT_JOB: EmptyResponse,
            meta_pb2.RequestType.AUTH: EmptyResponse,
            meta_pb2.RequestType.AVAILABLE_HANDLERS: AvailableHandlersResponse,
            meta_pb2.RequestType.CREATE_USER: EmptyResponse,
            meta_pb2.RequestType.DELETE_JOB: EmptyResponse,
            meta_pb2.RequestType.GENERIC: GenericResponse,
            meta_pb2.RequestType.NEW_JOB_RESPONSE: NewJobResponse,
            meta_pb2.RequestType.ORIGIN_GRAPH: OriginGraphResponse,
            meta_pb2.RequestType.SHORTEST_PATH: ShortestPathResponse,
            meta_pb2.RequestType.STATUS: StatusResponse,
        }[requestType]
    except KeyError as error:
        raise ParseError("Unknown response key") from error
