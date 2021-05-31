#!/usr/bin/env python

import gzip
import sys
import struct
import socket
import logging

from protocol.protos import GraphData_pb2


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
    requestProtoBuf = GraphData_pb2.RequestContainer()
    requestProtoBuf.ParseFromString(requestProtoBufString)

    request = GraphData_pb2.ShortPathRequest()
    requestProtoBuf.request.Unpack(request)

    responseProtoBuf = GraphData_pb2.ResponseContainer()
    responseProtoBuf.status = GraphData_pb2.ResponseContainer.StatusCode.OK

    response = GraphData_pb2.ShortPathResponse()

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
    return responseProtoBuf.SerializeToString()


if __name__ == "__main__":
    main()
