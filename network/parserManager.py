#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
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


def parserListEmpty():
    return len(parser) == 0


def resetParsers():
    parser.clear()
