import os

from qgis.core import QgsSettings, QgsApplication, QgsProject

from .base import BaseController
from ..models.GraphBuilder import GraphBuilder
from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer

from ..exceptions import FieldRequiredError

# client imports
from ..network.client import Client
from ..network.requests.shortestPathRequest import ShortestPathRequest
from ..network.responses.shortestPathResponse import ShortestPathResponse
from ..network.exceptions import NetworkClientError


class OGDFAnalysisController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OGDFAnalysisView
        """
        super().__init__(view)

        self.settings = QgsSettings()
        self.authManager = QgsApplication.authManager()

        self.host = self.settings.value("ogdfplugin/host", "")
        self.port = int(self.settings.value("ogdfplugin/port", 4711))

        self.view.addAnalysis(self.tr("shortest path"), "shortest path")

        # add available analysis
        # with Client(self.host, self.port) as client:
        #     try:
        #         client.getAvailableHandlers()
        #         for requestName in client.requestTypes:
        #             request = client.requestTypes[requestName]
        #             self.view.addAnalysis(requestName, request)
        #     except NetworkClientError as e:
        #         self.view.showError(str(e))

    def runJob(self):
        # todo: pass authId to client
        authId = self.settings.value("ogdfplugin/authId")
        if not (self.host and self.port):
            self.view.showError(self.tr("Please set host and port in options!"))
            return None

        # get user parameter fields data
        try:
            parameterFieldsData = self.view.getParameterFieldsData()
        except FieldRequiredError as e:
            self.view.showError(str(e))
            return

        # set field data into request
        analysisLabel, request = self.view.getAnalysis()
        for key in parameterFieldsData:
            fieldData = parameterFieldsData[key]
            request.setFieldData(key, fieldData)

        # with Client(self.host, self.port) as client:
        #     shortPathRequest = ShortestPathRequest(graph, startNodeIndex, endNodeIndex)
        #     _msgLength = client.send(shortPathRequest)
        #
        #     try:
        #         # receive response
        #         response = ShortestPathResponse(ExtGraph())
        #         client.recv(response)
        #     except NetworkClientError as e:
        #         self.view.showError(str(e))

        # # show graph in qgis
        # builder = GraphBuilder()
        # builder.setGraph(response.graph)
        # graphLayer = builder.createGraphLayer(False)
        # graphLayer.setName("ResultGraphLayer")
        # QgsProject.instance().addMapLayer(graphLayer)
        # self.view.showSuccess(self.tr("Analysis complete!"))

    # def __getGraph(self):
    #     """
    #     Loads graph from input
    #     :return:
    #     """
    #     if not self.view.hasInput():
    #         self.view.showError(self.tr("Please select a graph!"))
    #         return None
    #
    #     if self.view.isInputLayer():
    #         # return graph from graph layer
    #         graphLayer = self.view.getInputLayer()
    #         if not isinstance(graphLayer, QgsGraphLayer):
    #             self.view.showError(self.tr("The selected layer is not a graph layer!"))
    #         if graphLayer.isValid():
    #             return graphLayer.getGraph()
    #         else:
    #             self.view.showError(self.tr("The selected graph layer is invalid!"))
    #     else:
    #         # if file path as input
    #         path = self.view.getInputPath()
    #         fileName, extension = os.path.splitext(path)
    #         if extension == ".graphml":
    #             graph = ExtGraph()
    #             graph.readGraphML(path)
    #             return graph
    #     return None
