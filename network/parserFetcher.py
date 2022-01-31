from qgis.core import QgsApplication, QgsTask
from qgis.PyQt.QtCore import QObject, pyqtSignal

from .. import helperFunctions as helper
from . import parserManager
from .client import Client
from .exceptions import NetworkClientError, ParseError, ServerError

class ParserFetcher(QObject):
    activeTask = None
    parsersRefreshed = pyqtSignal(object, name='parsersRefreshed')

    def refreshParsers(self):
        """
        fetches all available handlers from server
        :return:
        """
        if ParserFetcher.activeTask:
            return

        parserManager.resetParsers()

        task = QgsTask.fromFunction(
            "Refreshing algorithms...",
            self.createFetchHandlersTask,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            on_finished=self.fetchHandlersCompleted
        )
        QgsApplication.taskManager().addTask(task)
        ParserFetcher.activeTask = task

    def createFetchHandlersTask(self, _task, host, port, tlsOption):
        try:
            with Client(host, port, tlsOption) as client:
                client.getAvailableHandlers()
                return {"success": "Algorithms refreshed!",}
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

    def fetchHandlersCompleted(self, exception, result=None):
        """
        Processes the results of the fetch handlers task.
        """
        # first remove active task to allow a new request.
        ParserFetcher.activeTask = None

        if exception is None:
            self.parsersRefreshed.emit(result)
        else:
            result["exception"] = exception
            self.parsersRefreshed.emit(result)

    def resetParsers(self):
        parserManager.resetParsers()
        self.parsersRefreshed.emit({"reset": True})


_inst = ParserFetcher()


def instance():
    return _inst
