import socket
import struct
import gzip

from . import protoParser
from .exceptions import NetworkClientError

LENGTH_FIELD_SIZE = 8


class Client():

    def __init__(self, host, port, maxRetryAttempts=10):
        self.host = host
        self.port = port
        self.maxRetryAttempts = maxRetryAttempts
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, _type, _value, _traceback):
        self.socket.close()

    def connect(self, attempt=0):
        if attempt < self.maxRetryAttempts:
            try:
                self.socket.connect((self.host, self.port))
            except socket.error:
                self.connect(attempt+1)
        else:
            raise NetworkClientError("Can't connect to host")

    def disconnect(self):
        self.socket.close()

    def sendShortPathRequest(self, shortPathRequest):
        protoBufString = protoParser.createProtoBuf(shortPathRequest)

        return self._sendProtoBufString(protoBufString)

    def _sendProtoBufString(self, protoBufString):
        compressedProtoBufString = gzip.compress(protoBufString)

        msg = struct.pack('!Q', len(compressedProtoBufString)) + compressedProtoBufString

        try:
            self.socket.sendall(msg)
        except (BrokenPipeError, AttributeError) as sendError:
            raise NetworkClientError from sendError

        return len(msg)

    def readShortPathResponse(self):
        protoBufString = self._readProtobufString()

        graph = protoParser.parseProtoBuf(protoBufString)

        return graph

    def _readProtobufString(self):
        rawMsgLength = self._recvAll(LENGTH_FIELD_SIZE)
        if not rawMsgLength:
            raise NetworkClientError("No ProtoBuf length received")

        msgLength = struct.unpack('!Q', rawMsgLength)[0]

        compressedProtoBufString = self._recvAll(msgLength)
        if not compressedProtoBufString:
            raise NetworkClientError("No ProtoBuf received")

        return gzip.decompress(compressedProtoBufString)

    def _recvAll(self, msgLength):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < msgLength:
            try:
                packet = self.socket.recv(msgLength - len(data))
            except (BrokenPipeError, AttributeError) as readError:
                raise NetworkClientError from readError
            if not packet:
                raise NetworkClientError("No protobuf received")
            data.extend(packet)
        return data
