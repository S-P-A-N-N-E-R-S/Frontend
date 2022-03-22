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


from qgis.core import QgsApplication, QgsTask
from qgis.PyQt.QtCore import QObject, pyqtSignal

from .. import helperFunctions as helper
from . import handlerManager
from .client import Client
from .exceptions import NetworkClientError, ParseError, ServerError

class HandlerFetcher(QObject):
    """Class that fetches available handlers from server"""

    activeTask = None
    handlersRefreshed = pyqtSignal(object, name='handlersRefreshed')

    def refreshHandlers(self):
        """Creates a task that fetches available handlers from server"""

        if HandlerFetcher.activeTask:
            return

        handlerManager.resetHandlers()

        task = QgsTask.fromFunction(
            "Refreshing algorithms...",
            self.createFetchHandlersTask,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            on_finished=self.fetchHandlersCompleted
        )
        QgsApplication.taskManager().addTask(task)
        HandlerFetcher.activeTask = task

    def createFetchHandlersTask(self, _task, host, port, tlsOption):
        """
        Fetches available handlers from server

        :param _task: Task object; Not used
        :param host: Server IP address
        :param port: Server port
        :param tlsOption: TLS setting
        :return: Success and error messages
        """

        try:
            with Client(host, port, tlsOption) as client:
                client.getAvailableHandlers()
                return {"success": "Algorithms refreshed!",}
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

    def fetchHandlersCompleted(self, exception, result=None):
        """
        Processes the results of the fetch handlers task

        :param exception: Exceptions that occurred during the task execution
        :param result: Result of the task, defaults to None
        """

        # remove active task to allow a new request.
        HandlerFetcher.activeTask = None

        if exception is None:
            self.handlersRefreshed.emit(result)
        else:
            result["exception"] = exception
            self.handlersRefreshed.emit(result)

    def resetHandlers(self):
        """Resets saved available handlers and emits reset signal"""

        handlerManager.resetHandlers()
        self.handlersRefreshed.emit({"reset": True})


_inst = HandlerFetcher()


def instance():
    """
    Returns HandlerFetcher instance

    :return: HandlerFetcher instance
    """

    return _inst
