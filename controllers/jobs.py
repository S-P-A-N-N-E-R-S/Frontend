from .base import BaseController
from ..models.QgsGraphLayer import QgsGraphLayer
from .. import helperFunctions as helper
from .. import mainPlugin

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError
from ..network.protocol.build.available_handlers_pb2 import ResultInformation
from ..network.protocol.build.status_pb2 import StatusType

from qgis.core import QgsSettings


class JobsController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: JobsView
        """
        super().__init__(view)

        self.settings = QgsSettings()

        self.view.setResultVisible(False)

        self.STATUS_TEXTS = {
            StatusType.UNKNOWN_STATUS: self.tr("unknown"),
            StatusType.WAITING: self.tr("waiting"),
            StatusType.RUNNING: self.tr("running"),
            StatusType.SUCCESS: self.tr("success"),
            StatusType.FAILED: self.tr("failed"),
            StatusType.ABORTED: self.tr("unknown"),
        }

    def fetchResult(self):
        if self.view.getCurrentJob() is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        host = self.settings.value("ogdfplugin/host", "")
        port = int(self.settings.value("ogdfplugin/port", 4711))

        # Get result from finished job
        try:
            with Client(host, port) as client:
                response = client.getJobResult(int(self.view.getCurrentJob()[0]))
        except (NetworkClientError, ParseError) as error:
            self.view.showError(str(error), self.tr("Network Error"))

        # print(response.getGraph().mEdges)
        # print(response.getGraph().mVertices)

        # show graph in qgis
        graphLayer = QgsGraphLayer()
        graphLayer.setGraph(response.getGraph())
        success, errorMsg = helper.saveGraph(response.getGraph(), graphLayer, self.tr("Result"), self.view.getDestinationFilePath())
        if not success:
            self.view.showError(errorMsg)

        # show text results in response
        resultString = ""
        for resultKey, resultData in response.data.items():
            result = response.results[resultKey]
            if result.type in [ResultInformation.HandlerReturnType.INT, ResultInformation.HandlerReturnType.DOUBLE,
                               ResultInformation.HandlerReturnType.STRING]:
                resultString += result.label + ": " + str(resultData) + "\n"
        self.view.setResultHtml(resultString)
        self.view.setResultVisible(resultString != "")

        self.view.showSuccess(self.tr("Result fetched!"))

    def fetchOriginGraph(self):
        pass

    def refreshJobs(self):
        self.view.clearJobs()

        host = self.settings.value("ogdfplugin/host", "")
        port = int(self.settings.value("ogdfplugin/port", 4711))

        # get response
        try:
            with Client(host, port) as client:
                states = client.getJobStatus()
                # add jobs
                for job in states:
                    jobStatus = states[job].get("status", "")
                    self.view.addJob(str(job), self.STATUS_TEXTS.get(jobStatus, "status not supported"))
        except (NetworkClientError, ParseError) as error:
            self.view.showError(str(error), self.tr("Network Error"))

    def abortJob(self):
        pass

    def restartJob(self):
        pass
