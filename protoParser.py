from qgis.core import QgsPointXY

from qgis.analysis import QgsGraph

from .exceptions import ParseError
from .protocol.protos import GraphData_pb2


def createProtoBuf(request):
    protoBuf = GraphData_pb2.RequestContainer()

    try:
        requestMessage = request.toProtoBuf()
    except NameError as nameError:
        raise ParseError("Method not defined") from nameError
    protoBuf.request.Pack(requestMessage)
    protoBuf.type = request.type

    return protoBuf.SerializeToString()


def parseProtoBuf(protoBufString):
    protoBuf = GraphData_pb2.ResponseContainer()
    protoBuf.ParseFromString(protoBufString)

    if protoBuf.status == GraphData_pb2.ResponseContainer.StatusCode.OK:

        try:
            responseParser = _responseParsers[protoBuf.type]
        except KeyError as undefinedResponseError:
            raise ParseError("Unknown response type") from undefinedResponseError

        return responseParser(protoBuf)

    elif protoBuf.status == GraphData_pb2.ResponseContainer.StatusCode.ERROR:
        raise ParseError("Server responded with error")

    else:
        raise ParseError("Server responded with unknown status code")


def _parseShortPathResponse(protoBuf):

    response = GraphData_pb2.ShortPathResponse()
    protoBuf.response.Unpack(response)

    graph = _createGraphFromProtoBuf(response.graph)

    return graph


def _createGraphFromProtoBuf(protoGraph):
    graph = QgsGraph()

    for vertex in protoGraph.vertexList:
        graph.addVertex(QgsPointXY(vertex.x, vertex.y))

    for edge in protoGraph.edgeList:
        graph.addEdge(edge.inVertexUid, edge.outVertexUid, [])

    return graph


_responseParsers = {
    GraphData_pb2.ResponseContainer.ResponseType.SHORTEST_PATH: _parseShortPathResponse,
}
