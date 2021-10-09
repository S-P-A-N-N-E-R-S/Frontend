from . import parserManager
from .exceptions import ParseError, ServerError
from .protocol.build import container_pb2, meta_pb2

from .responses.statusResponse import StatusResponse
from .responses.availableHandlersResponse import AvailableHandlersResponse
from .responses.genericResponse import GenericResponse
from .responses.newJobResponse import NewJobResponse
from .responses.shortestPathResponse import ShortestPathResponse


def createProtoBuf(request):
    protoBuf = container_pb2.RequestContainer()

    try:
        requestMessage = request.toProtoBuf()
    except NameError as nameError:
        raise ParseError("Method not defined") from nameError
    protoBuf.request.Pack(requestMessage)

    return protoBuf.SerializeToString()


def getMetaStringFromType(requestType):
    metaData = meta_pb2.MetaData()
    metaData.containerSize = 0
    metaData.type = requestType
    return metaData.SerializeToString()


def getMetaStringFromRequest(request, requestStringLen):
    metaData = meta_pb2.MetaData()
    metaData.containerSize = requestStringLen
    metaData.type = request.type

    if getattr(request, "key", None):
        metaData.handlerType = request.key

    if getattr(request, "jobName", None):
        metaData.jobName = request.jobName

    metaString = metaData.SerializeToString()

    return metaString


def parseProtoBuf(protoBufString, responseType, handlerType=None):
    protoBuf = container_pb2.ResponseContainer()
    protoBuf.ParseFromString(protoBufString)

    if protoBuf.status == container_pb2.ResponseContainer.StatusCode.OK:

        if responseType == meta_pb2.RequestType.GENERIC:
            if not handlerType:
                raise ParseError("Missing handler type")

            # Get specific generic response for request
            response = parserManager.getResponseParser(handlerType)
        else:
            response = getResponseByType(responseType)

        try:
            response.parseProtoBuf(protoBuf)
            return response
        except NameError as nameError:
            raise ParseError("Method not defined") from nameError

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


def getResponseByType(requestType):
    # Return the correct default constructed response type by the type field provied by meta data
    try:
        return {
            meta_pb2.RequestType.AVAILABLE_HANDLERS: AvailableHandlersResponse(),
            meta_pb2.RequestType.GENERIC: GenericResponse(),
            meta_pb2.RequestType.NEW_JOB_RESPONSE: NewJobResponse(),
            meta_pb2.RequestType.SHORTEST_PATH: ShortestPathResponse(),
            meta_pb2.RequestType.STATUS: StatusResponse(),
        }.get(requestType)
    except KeyError as error:
        raise ParseError("Unknown response key") from error
