from .base import BaseController
from ..models.QgsGraphLayer import QgsGraphLayer
from .. import helperFunctions as helper
from .. import mainPlugin

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError
from ..network.protocol.build.available_handlers_pb2 import ResultInformation


class JobsController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: JobsView
        """
        super().__init__(view)

        self.view.setResultVisible(False)

    def fetchResult(self):
        if self.view.getCurrentJob() is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        jobName, requestKey = self.view.getCurrentJob()
        response = mainPlugin.OGDFPlugin.responses[requestKey]

        resultGraph = ExtGraph()  # empty(?) ExtGraph which will contain result
        response.setFieldData(response.graphKey, resultGraph)

        for idx, edgeCostFieldKey in enumerate(response.getEdgeCostFields()):
            response.setFieldData(edgeCostFieldKey, idx)  # costfunction index for each edgeCostField

        for idx, vertexCostFieldKey in enumerate(response.getVertexCostFields()):
            response.setFieldData(vertexCostFieldKey, idx)  # costfunction index for each vertexCostField

        # get response
        host = self.settings.value("ogdfplugin/host", "")
        port = int(self.settings.value("ogdfplugin/port", 4711))
        try:
            with Client(host, port) as client:
                client.recv(response)
        except NetworkClientError as error:
            self.view.showError(str(error))
        except ParseError as error:
            self.view.showError(str(error))

        # show graph in qgis
        graphLayer = QgsGraphLayer()
        graphLayer.setGraph(resultGraph)
        success, errorMsg = helper.saveGraph(resultGraph, graphLayer, self.tr("Result"), self.view.getDestinationFilePath())
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
        self.view.setResultVisible(True)

        self.view.showSuccess(self.tr("Result fetched!"))

    def fetchOriginGraph(self):
        pass

    def refreshJobs(self):
        self.view.clearJobs()

        requestsKeys = mainPlugin.OGDFPlugin.activeRequestsKeys

        # add jobs
        for key in requestsKeys:
            self.view.addJob(mainPlugin.OGDFPlugin.requests[key].name, key)

    def abortJob(self):
        pass

    def restartJob(self):
        pass
