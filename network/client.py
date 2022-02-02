import socket
import ssl
import struct
import gzip

from . import parserManager, protoParser, statusManager
from .exceptions import NetworkClientError, ParseError
from .protocol.build import meta_pb2
from .requests.statusRequest import StatusRequest
from .requests.resultRequest import ResultRequest
from .requests.abortJobRequest import AbortJobRequest
from .requests.deleteJobRequest import DeleteJobRequest
from .requests.originGraphRequest import OriginGraphRequest
from ..helperFunctions import TlsOption


LENGTH_FIELD_SIZE = 8


class Client():

    def __init__(self, host, port, tlsOption=TlsOption.ENABLED_NO_CHECK, maxRetryAttempts=1):
        if not isinstance(tlsOption, TlsOption):
            raise TypeError("Parameter tlsOption is not of Type TlsOption")

        self.host = host
        self.port = port
        self.maxRetryAttempts = maxRetryAttempts

        # Create the socket depending on the encryption/tls setting
        if tlsOption == TlsOption.ENABLED:
            self.context = ssl.SSLContext()
            self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_REQUIRED

            self.unwrappedSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.unwrappedSocket)
        elif tlsOption == TlsOption.ENABLED_NO_CHECK:
            self.context = ssl.SSLContext()
            self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE

            self.unwrappedSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.unwrappedSocket)
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        self.socket.settimeout(1)  # 1 second
        self.connect()
        self.socket.settimeout(None)  # blocking mode
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

    def checkAuthenticationData(self):
        metaString = protoParser.getMetaStringFromType(meta_pb2.RequestType.AUTH)
        self._sendProtoBufString(metaString, bytearray())

        self.recv()
        return True

    def createUser(self):
        metaString = protoParser.getMetaStringFromType(meta_pb2.RequestType.CREATE_USER)
        self._sendProtoBufString(metaString, bytearray())

        self.recv()
        return True

    def getAvailableHandlers(self):
        # Send request of type AVAILABLE_HANDLERS with empty container to receive handlers
        metaString = protoParser.getMetaStringFromType(meta_pb2.RequestType.AVAILABLE_HANDLERS)

        self._sendProtoBufString(metaString, bytearray())

        # Wait for answer
        self.recv()
        return parserManager.getParserPairs()

    def getJobStatus(self):
        # Send status request
        request = StatusRequest()
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        self.recv()
        return statusManager.getJobStates()

    def getJobStatusById(self, jobId):
        # Not implemented in the backend yet
        pass

    def getJobResult(self, jobId):
        request = ResultRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        handlerType = statusManager.getJobState(jobId).handlerType
        jobResponse = self.recv(handlerType)
        return jobResponse

    def abortJob(self, jobId):
        request = AbortJobRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        self.recv()
        return True

    def deleteJob(self, jobId):
        request = DeleteJobRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        self.recv()
        return True

    def getOriginGraph(self, jobId):
        request = OriginGraphRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        response = self.recv()
        return response

    def sendJobRequest(self, request):
        # Create compressed wire format
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        newjobResponse = self.recv()
        return newjobResponse.jobId

    def _sendProtoBufString(self, metaString, compressedProtoBufString):
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
        metaData = protoParser.parseMetaData(metaString)

        if handlerType or metaData.handlerType:
            if not handlerType or not metaData.handlerType or handlerType != metaData.handlerType:
                raise ParseError("Invalid handler type")

        if metaData.containerSize:
            # Get container
            compressedProtoBufString = self._recvAll(metaData.containerSize)
            if not compressedProtoBufString:
                raise NetworkClientError("No ProtoBuf received")
            return protoParser.parseProtoBuf(gzip.decompress(compressedProtoBufString), metaData.type, handlerType)
        else:
            raise NetworkClientError("No ProtoBuf received")

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
