#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Dennis Benz, Timo Glane, Leon Nienhüser
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.


import socket
import ssl
import struct
import gzip

from . import handlerManager, protoParser, statusManager
from .exceptions import NetworkClientError, ParseError
from .handlers.statusHandler import StatusRequest
from .handlers.resultHandler import ResultRequest
from .handlers.abortJobHandler import AbortJobRequest
from .handlers.deleteJobHandler import DeleteJobRequest
from .handlers.originGraphHandler import OriginGraphRequest
from ..helperFunctions import TlsOption

from .protocol.build import meta_pb2


LENGTH_FIELD_SIZE = 8


class Client():
    """Class that manages all network communication of the plugin"""

    def __init__(self, host, port, tlsOption=TlsOption.ENABLED_NO_CHECK, maxRetryAttempts=1):
        """
        Constructor

        :param host: IP address of the server
        :param port: Port of the server
        :param tlsOption: TLS setting of the server, defaults to TlsOption.ENABLED_NO_CHECK
        :param maxRetryAttempts: Maximum number of connect attempts, defaults to 1
        :raises TypeError: If tlsOption is not of Type TlsOption
        """

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
        """
        Establishes a connection with the server

        :param attempt: Current number of connect attempts, defaults to 0
        :raises NetworkClientError: If connection to server was not possible
        """

        if attempt < self.maxRetryAttempts:
            try:
                self.socket.connect((self.host, self.port))
            except socket.error:
                self.connect(attempt+1)
        else:
            raise NetworkClientError("Can't connect to host")

    def disconnect(self):
        """Closes connection to server"""

        self.socket.close()

    def checkAuthenticationData(self):
        """
        Checks the currently saved authentication data with the server

        :return: True, if the authentication data is valid
        """

        metaString = protoParser.getMetaStringFromType(meta_pb2.RequestType.AUTH)
        self._sendProtoBufString(metaString, bytearray())

        self.recv()
        return True

    def createUser(self):
        """
        Tries to create a new user account on the server with the currently saved authentication data

        :return: True, if the user creation was successful
        """

        metaString = protoParser.getMetaStringFromType(meta_pb2.RequestType.CREATE_USER)
        self._sendProtoBufString(metaString, bytearray())

        self.recv()
        return True

    def getAvailableHandlers(self):
        """
        Fetches all available handlers from the server

        :return: HandlerPairs of all available handlers
        """

        # Send request of type AVAILABLE_HANDLERS with empty container to receive handlers
        metaString = protoParser.getMetaStringFromType(meta_pb2.RequestType.AVAILABLE_HANDLERS)

        self._sendProtoBufString(metaString, bytearray())

        # Wait for answer
        self.recv()
        return handlerManager.getHandlerPairs()

    def getJobStatus(self):
        """
        Fetches all job states associated to the current user from the server

        :return: All job states associated to the current user
        """

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
        """
        Fetches the job state with the specified job ID from the server;
        This method is not implemented yet!

        :param jobId: ID of the desired job state
        :raises NetworkClientError: Always
        """

        raise NetworkClientError("Not implemented!")

    def getJobResult(self, jobId):
        """
        Fetches the job result with the specified job ID from the server

        :param jobId: ID of the desired job result
        :return: Job response object of the job with the specified ID
        """

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
        """
        Aborts the job with the specified job ID

        :param jobId: ID of the job to be aborted
        :return: True, if abort message was successful
        """

        request = AbortJobRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        self.recv()
        return True

    def deleteJob(self, jobId):
        """
        Deletes the job with the specified job ID

        :param jobId: ID of the job to be deleted
        :return: True, if delete message was successful
        """

        request = DeleteJobRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        self.recv()
        return True

    def getOriginGraph(self, jobId):
        """
        Fetches the origin graph of the request with the specified job ID from the server

        :param jobId: Job ID of the request with the desired origin graph
        :return: Job response object containing the desired origin graph
        """

        request = OriginGraphRequest(jobId)
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        response = self.recv()
        return response

    def sendJobRequest(self, request):
        """
        Sends a job request to be executed on the server

        :param request: Job request to be executed on the server
        :return: ID of the new job
        """

        # Create compressed wire format
        protoBufString = protoParser.createProtoBuf(request)
        compressedProtoBufString = gzip.compress(protoBufString)

        metaString = protoParser.getMetaStringFromRequest(request, len(compressedProtoBufString))

        self._sendProtoBufString(metaString, compressedProtoBufString)

        # Wait for answer
        newjobResponse = self.recv()
        return newjobResponse.jobId

    def _sendProtoBufString(self, metaString, compressedProtoBufString):
        """
        Helper function that sends a compressed protobuf string with its meta data to the server

        :param metaString: Meta data string
        :param compressedProtoBufString: Compressed protobuf string
        :raises NetworkClientError: If message could not be sent to the server
        :return: Length of the message sent to the server
        """

        # Pack message and send
        msg = struct.pack('!Q', len(metaString)) + metaString + compressedProtoBufString

        try:
            self.socket.sendall(msg)
        except (BrokenPipeError, AttributeError) as sendError:
            raise NetworkClientError from sendError

        return len(msg)

    def recv(self, handlerType=None):
        """
        Receives and parses a protobuf message from the server

        :param handlerType: Optional handler type of the message to be received, defaults to None
        :raises NetworkClientError: If no message could be received
        :raises ParseError: If the hanlder type is invalid
        :return: Parsed protobuf message
        """

        # Get meta data length
        rawMsgLength = self._recvAll(LENGTH_FIELD_SIZE)
        if not rawMsgLength:
            raise NetworkClientError("No ProtoBuf length received")
        msgLength = struct.unpack('!Q', rawMsgLength)[0]

        # Get meta data
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
        """
        Helper function to recv n bytes or return None if EOF is hit

        :param msgLength: Number of bytes to receive
        :raises NetworkClientError: If no message could be received
        :return: Received data
        """

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
