from .exceptions import ParseError, ServerError
from .protocol.build import container_pb2, generic_container_pb2, meta_pb2

from .responses.statusResponse import StatusResponse
from .responses.availableHandlersResponse import AvailableHandlersResponse
from .responses.genericResponse import GenericResponse
from .responses.shortestPathResponse import ShortestPathResponse

from .. import mainPlugin


def createProtoBuf(request):
    protoBuf = container_pb2.RequestContainer()

    try:
        requestMessage = request.toProtoBuf()
    except NameError as nameError:
        raise ParseError("Method not defined") from nameError
    protoBuf.request.Pack(requestMessage)

    return protoBuf.SerializeToString()


def parseProtoBuf(protoBufString, responseType):
    protoBuf = container_pb2.ResponseContainer()
    protoBuf.ParseFromString(protoBufString)

    if protoBuf.status == container_pb2.ResponseContainer.StatusCode.OK:

        response = getResponseByType(responseType)

        if isinstance(response, GenericResponse):
            # Get specific generic response for request
            tmp = generic_container_pb2.GenericResponse()
            protoBuf.response.Unpack(tmp)
            response = mainPlugin.OGDFPlugin.responses[tmp.handlerType]
            response.resetData()

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


def getResponseByType(handlerType):
    # Return the correct default constructed response type by the type field provied by meta data
    try:
        return {
            meta_pb2.RequestType.AVAILABLE_HANDLERS: AvailableHandlersResponse(),
            meta_pb2.RequestType.STATUS: StatusResponse(),
            meta_pb2.RequestType.SHORTEST_PATH: ShortestPathResponse(),
            meta_pb2.RequestType.GENERIC: GenericResponse()
        }.get(handlerType)
    except KeyError as error:
        raise ParseError("Unknown response key") from error
