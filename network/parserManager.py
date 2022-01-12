from copy import deepcopy

from .exceptions import NetworkClientError


class ParserPair():
    def __init__(self, request, response):
        self.request = request
        self.response = response


parser = {}


def getRequestParser(handlerType):
    try:
        return deepcopy(parser[handlerType].request)
    except KeyError as error:
        raise NetworkClientError("Unknown handler type") from error


def getRequestParsers():
    requests = {}
    for key, parserPair in parser.items():
        requests[key] = deepcopy(parserPair.request)
    return requests


def getResponseParser(handlerType):
    try:
        response = deepcopy(parser[handlerType].response)
        response.resetData()
        return response
    except KeyError as error:
        raise NetworkClientError("Unknown handler type") from error


def getResponseParsers():
    responses = {}
    for key, parserPair in parser.items():
        responses[key] = deepcopy(parserPair.response)
    return responses


def getParserPairs():
    requests = {}
    responses = {}
    for key, parserPair in parser.items():
        requests[key] = deepcopy(parserPair.request)
        responses[key] = deepcopy(parserPair.response)

    return requests, responses


def insertParserPair(request, response):
    parser[request.key] = ParserPair(request, response)


def resetParsers():
    parser.clear()
