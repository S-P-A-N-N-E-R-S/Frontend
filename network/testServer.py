#!/usr/bin/env python

import gzip
import sys
import struct
import socket
import logging

from protocol.build import container_pb2, generic_container_pb2, available_handlers_pb2


def main():
    logging.basicConfig(format='%(levelname)s %(asctime)s %(module)s %(message)s', level=logging.INFO)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 4711))
    sock.listen(1)

    logging.info("Waiting for connection...")

    try:
        while True:
            conn, addr = sock.accept()
            logging.info("Connection from: %s", str(addr))

            rawMsgLength = recvall(conn, 8)
            if not rawMsgLength:
                break
            msgLength = struct.unpack('>Q', rawMsgLength)[0]

            msg = recvall(conn, msgLength)
            logging.info("Received: %d", len(msg))

            protoBufString = gzip.decompress(msg)
            responseProtobufString = createResponse(protoBufString)
            compressedProtoBufString = gzip.compress(responseProtobufString)

            response = struct.pack('>Q', len(compressedProtoBufString)) + compressedProtoBufString
            conn.sendall(response)

            conn.close()
    except KeyboardInterrupt:
        logging.info("Closing socket")
        sock.close()
        sys.exit(0)
    finally:
        sock.close()


def recvall(sock, msgLength):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < msgLength:
        packet = sock.recv(msgLength - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def createResponse(requestProtoBufString):
    requestProtoBuf = container_pb2.RequestContainer()
    requestProtoBuf.ParseFromString(requestProtoBufString)

    responseProtoBuf = container_pb2.ResponseContainer()
    responseProtoBuf.status = container_pb2.ResponseContainer.StatusCode.OK

    if requestProtoBuf.type == meta_pb2.RequestType.GENERIC:
        request = generic_container_pb2.GenericRequest()
        requestProtoBuf.request.Unpack(request)

        response = generic_container_pb2.GenericResponse()

        response.graph.uid = request.graph.uid

        for vertex in request.graph.vertexList:
            protoVertex = response.graph.vertexList.add()
            protoVertex.uid = vertex.uid
            protoVertex.x = vertex.x
            protoVertex.y = vertex.y

        for edge in request.graph.edgeList:
            protoEdge = response.graph.edgeList.add()
            protoEdge.uid = edge.uid
            protoEdge.inVertexUid = edge.inVertexUid
            protoEdge.outVertexUid = edge.outVertexUid

        responseProtoBuf.response.Pack(response)
    elif requestProtoBuf.type == meta_pb2.RequestType.AVAILABLE_HANDLERS:
        response = available_handlers_pb2.AvailableHandlersResponse()
        responseProtoBuf.type = meta_pb2.RequestType.AVAILABLE_HANDLERS

        handler = response.handlers.add()
        handler.request_type = meta_pb2.RequestType.GENERIC
        handler.name = "Shortest Path"

        graphField = handler.fields.add()
        graphField.type = available_handlers_pb2.FieldInformation.FieldType.GRAPH
        graphField.label = "Graph"
        graphField.key = "graph"
        #graphField.default.Pack(0)
        graphField.required = True

        costField = handler.fields.add()
        costField.type = available_handlers_pb2.FieldInformation.FieldType.EDGE_COSTS
        costField.label = "Edge Costs"
        costField.key = "edgeCosts"
        #costField.default.Pack(0)
        costField.required = True

        coordsField = handler.fields.add()
        coordsField.type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_COORDINATES
        coordsField.label = "Vertex Coordinates"
        coordsField.key = "vertexCoordinates"
        #coordsField.default.Pack(0)
        coordsField.required = True

        startUid = handler.fields.add()
        startUid.type = available_handlers_pb2.FieldInformation.FieldType.VERTEX_COORDINATES
        startUid.label = "Start Vertex"
        startUid.key = "intAttributes.startUid"
        #startUid.default.Pack(0)
        startUid.required = True

        graphResult = handler.results.add()
        graphResult.type = available_handlers_pb2.ResultInformation.HandlerReturnType.GRAPH
        graphResult.label = "Graph"
        graphResult.key = "graph"

        costResult = handler.results.add()
        costResult.type = available_handlers_pb2.ResultInformation.HandlerReturnType.EDGE_COSTS
        costResult.label = "Edge Costs"
        costResult.key = "edgeCosts"

        coordsResult = handler.results.add()
        coordsResult.type = available_handlers_pb2.ResultInformation.HandlerReturnType.VERTEX_COORDINATES
        coordsResult.label = "Vertex Coordinates"
        coordsResult.key = "vertexCoordinates"

        responseProtoBuf.response.Pack(response)

    responseString = responseProtoBuf.SerializeToString()
    return responseString


if __name__ == "__main__":
    main()
