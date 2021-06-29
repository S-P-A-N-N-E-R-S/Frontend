from .exceptions import ParseError
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
        raise ParseError("Server responded with error")

    else:
        raise ParseError("Server responded with unknown status code")
