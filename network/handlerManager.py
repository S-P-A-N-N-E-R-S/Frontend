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
    """Data structure that contains a request and response pair"""

    def __init__(self, request, response):
        """
        Constructor

        :param request: Request handler
        :param response: Response handler
        """

        self.request = request
        self.response = response


handlers = {}


def getRequestHandler(handlerType):
    """
    Returns a deep copy of a request handler of the specified handler type

    :param handlerType: Type of the request handler
    :raises NetworkClientError: If the handler type is unknown
    :return: A request handler of the specified handler type
    """

    try:
        return deepcopy(handlers[handlerType].request)
    except KeyError as error:
        raise NetworkClientError("Unknown handler type") from error


def getRequestHandlers():
    """
    Returns deep copies of all request handlers as a dictionairy

    :return: All request handlers
    """

    requests = {}
    for key, handlerPair in handlers.items():
        requests[key] = deepcopy(handlerPair.request)
    return requests


def getResponseHandler(handlerType):
    """
    Returns a deep copy of a response handler of the specified handler type

    :param handlerType: Type of the response handler
    :raises NetworkClientError: If the handler type is unknown
    :return: A response handler of the specified handler type
    """

    try:
        response = deepcopy(handlers[handlerType].response)
        response.resetData()
        return response
    except KeyError as error:
        raise NetworkClientError("Unknown handler type") from error


def getResponseHandlers():
    """
    Returns deep copies of all response handlers as a dictionairy

    :return: All response handlers
    """

    responses = {}
    for key, handlerPair in handlers.items():
        responses[key] = deepcopy(handlerPair.response)
    return responses


def getHandlerPairs():
    """
    Returns two dictionaries as a tuple, containing deep copies of all
    request/response handlers respectively

    :return: Tuple containing all request and response handlers
    """

    requests = {}
    responses = {}
    for key, handlerPair in handlers.items():
        requests[key] = deepcopy(handlerPair.request)
        responses[key] = deepcopy(handlerPair.response)

    return requests, responses


def insertHandlerPair(request, response):
    """
    Inserts a new HandlerPair to be saved, containing the supplied
    request and response

    :param request: Request to be saved
    :param response: Response to be saved
    """

    handlers[request.key] = HandlerPair(request, response)


def handlerListEmpty():
    """
    Returns whether or not the handler list is empty

    :return: Boolean describing if the handler list is empty
    """

    return len(handlers) == 0


def resetHandlers():
    """Deletes all saved handlers and resets handler list"""

    handlers.clear()
