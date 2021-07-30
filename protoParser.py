from .exceptions import ParseError, ServerError
from .protocol.build import container_pb2


def createProtoBuf(request):
    protoBuf = container_pb2.RequestContainer()

    try:
        requestMessage = request.toProtoBuf()
    except NameError as nameError:
        raise ParseError("Method not defined") from nameError
    protoBuf.request.Pack(requestMessage)
    protoBuf.type = request.type

    return protoBuf.SerializeToString()


def parseProtoBuf(protoBufString, response):
    protoBuf = container_pb2.ResponseContainer()
    protoBuf.ParseFromString(protoBufString)

    if protoBuf.status == container_pb2.ResponseContainer.StatusCode.OK:

        try:
            response.parseProtoBuf(protoBuf)
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
