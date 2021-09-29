import socket
import struct
import gzip

from . import parserManager, protoParser, statusManager
from .exceptions import NetworkClientError, ParseError
from .protocol.build import meta_pb2
from .requests.statusRequest import StatusRequest
from .requests.resultRequest import ResultRequest


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

    def getAvailableHandlers(self):
        # Send request of type AVAILABLE_HANDLERS with empty container to receive handlers
        self._sendProtoBufString(meta_pb2.RequestType.AVAILABLE_HANDLERS, bytearray())

        # Wait for answer
        self.recv()
        return parserManager.getParserPairs()

    def getJobStatus(self):
        # Send status request
        self._sendProtoBufString(meta_pb2.RequestType.STATUS,
            protoParser.createProtoBuf(StatusRequest()))

        # Wait for answer
        self.recv()
        return statusManager.getJobStates()

    def getJobStatusById(self, jobId):
        # Not implemented in the backend yet
        pass

    def getJobResult(self, jobId):
        self._sendProtoBufString(meta_pb2.RequestType.RESULT,
            protoParser.createProtoBuf(ResultRequest(jobId)))

        # Wait for answer
        handlerType = statusManager.getJobState(jobId).handlerType
        jobResponse = self.recv(handlerType)
        return jobResponse

    def sendJobRequest(self, request):
        # Create compressed wire format
        protoBufString = protoParser.createProtoBuf(request)
        self._sendProtoBufString(request.type, protoBufString, request.key)

        # Wait for answer
        newjobResponse = self.recv()
        return newjobResponse.jobId

    def _sendProtoBufString(self, requestType, protoBufString, handlerType=None):
        compressedProtoBufString = gzip.compress(protoBufString)

        # Create meta message
        metaData = meta_pb2.MetaData()
        metaData.containerSize = len(compressedProtoBufString)
        metaData.type = requestType
        if handlerType:
            metaData.handlerType = handlerType
        metaString = metaData.SerializeToString()

        # Pack message and send
        msg = struct.pack('!Q', len(metaString)) + metaString + compressedProtoBufString

        try:
            self.socket.sendall(msg)
        except (BrokenPipeError, AttributeError) as sendError:
            raise NetworkClientError from sendError

        return len(msg)

    def recv(self, handlerType=None):
        # Get meta message length
        rawMsgLength = self._recvAll(LENGTH_FIELD_SIZE)
        if not rawMsgLength:
            raise NetworkClientError("No ProtoBuf length received")
        msgLength = struct.unpack('!Q', rawMsgLength)[0]

        # Get meta message
        metaString = self._recvAll(msgLength)
        metaData = meta_pb2.MetaData()
        metaData.ParseFromString(metaString)
        if metaData.containerSize <= 0:
            raise NetworkClientError("Empty Message")

        if handlerType or metaData.handlerType:
            if not handlerType or not metaData.handlerType or handlerType != metaData.handlerType:
                raise ParseError("Invalid handler type")

        # Get container
        compressedProtoBufString = self._recvAll(metaData.containerSize)
        if not compressedProtoBufString:
            raise NetworkClientError("No ProtoBuf received")
        return protoParser.parseProtoBuf(gzip.decompress(compressedProtoBufString), metaData.type, handlerType)

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
