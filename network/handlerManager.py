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


class HandlerPair():
    def __init__(self, request, response):
        self.request = request
        self.response = response


handlers = {}


def getRequestHandler(handlerType):
    try:
        return deepcopy(handlers[handlerType].request)
    except KeyError as error:
        raise NetworkClientError("Unknown handler type") from error


def getRequestHandlers():
    requests = {}
    for key, handlerPair in handlers.items():
        requests[key] = deepcopy(handlerPair.request)
    return requests


def getResponseHandler(handlerType):
    try:
        response = deepcopy(handlers[handlerType].response)
        response.resetData()
        return response
    except KeyError as error:
        raise NetworkClientError("Unknown handler type") from error


def getResponseHandlers():
    responses = {}
    for key, handlerPair in handlers.items():
        responses[key] = deepcopy(handlerPair.response)
    return responses


def getHandlerPairs():
    requests = {}
    responses = {}
    for key, handlerPair in handlers.items():
        requests[key] = deepcopy(handlerPair.request)
        responses[key] = deepcopy(handlerPair.response)

    return requests, responses


def insertHandlerPair(request, response):
    handlers[request.key] = HandlerPair(request, response)


def handlerListEmpty():
    return len(handlers) == 0


def resetHandlers():
    handlers.clear()
