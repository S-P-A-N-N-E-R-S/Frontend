import os

from qgis.core import QgsSettings, QgsApplication, QgsProject

from .base import BaseController
from ..models.GraphBuilder import GraphBuilder
from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer

# client imports
from ..network.client import Client
from ..network.requests.shortPathRequest import ShortPathRequest
from ..network.responses.shortPathResponse import ShortPathResponse
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

        # self.view.addAnalysis("t-Spanner")
        # self.view.addAnalysis("minimum spanner")
        self.view.addAnalysis(self.tr("shortest path"), "shortest path")
        # self.view.addAnalysis("steiner tree")
        # self.view.addAnalysis("delaunay triangulation")

    def runJob(self):
        startNodeIndex = self.view.getStartNode()
        endNodeIndex = self.view.getEndNode()

        graph = self.__getGraph()
        if not graph:
            return

        host = self.settings.value("protoplugin/host", "")
        port = int(self.settings.value("protoplugin/port", 4711))
        # todo: pass authId to client
        authId = self.settings.value("protoplugin/authId")
        if not (host and port):
            self.view.showError(self.tr("Please set host and port in options!"))
            return None

        with Client(host, port) as client:
            shortPathRequest = ShortPathRequest(graph, startNodeIndex, endNodeIndex)
            _msgLength = client.send(shortPathRequest)

            try:
                # receive response
                response = ShortPathResponse(ExtGraph())
                client.recv(response)
            except NetworkClientError as e:
                self.view.showError(str(e))

        # show graph in qgis
        builder = GraphBuilder()
        builder.setGraph(response.graph)
        graphLayer = builder.createGraphLayer(False)
        graphLayer.setName("ResultGraphLayer")
        QgsProject.instance().addMapLayer(graphLayer)
        self.view.showSuccess(self.tr("Analysis complete!"))

    def __getGraph(self):
        """
        Loads graph from input
        :return:
        """
        if not self.view.hasInput():
            self.view.showError(self.tr("Please select a graph!"))
            return None

        if self.view.isInputLayer():
            # return graph from graph layer
            graphLayer = self.view.getInputLayer()
            if not isinstance(graphLayer, QgsGraphLayer):
                self.view.showError(self.tr("The selected layer is not a graph layer!"))
            if graphLayer.isValid():
                return graphLayer.getGraph()
            else:
                self.view.showError(self.tr("The selected graph layer is invalid!"))
        else:
            # if file path as input
            path = self.view.getInputPath()
            fileName, extension = os.path.splitext(path)
            if extension == ".graphml":
                graph = ExtGraph()
                graph.readGraphML(path)
                return graph
        return None
