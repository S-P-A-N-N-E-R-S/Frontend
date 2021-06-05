import os

from qgis.core import QgsSettings

from .base import BaseController
from ..models.GraphBuilder import GraphBuilder
from ..models.PGGraph import PGGraph

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

        # set up client
        self.settings = QgsSettings()

        # self.view.addAnalysis("t-Spanner")
        # self.view.addAnalysis("minimum spanner")
        self.view.addAnalysis("shortest path")
        # self.view.addAnalysis("steiner tree")
        # self.view.addAnalysis("delaunay triangulation")

    def runJob(self):
        startNodeIndex = self.view.getStartNode()
        endNodeIndex = self.view.getEndNode()

        graph = self.__getGraph()
        if not graph:
            return

        host = self.settings.value("protoplugin/host", None)
        port = int(self.settings.value("protoplugin/port", None))
        if not (host and port):
            self.view.showError("Please set host and port in options!")
            return None

        with Client(host, port) as client:
            shortPathRequest = ShortPathRequest(graph, startNodeIndex, endNodeIndex)
            msgLength = client.sendShortPathRequest(shortPathRequest)

            try:
                response = client.readShortPathResponse(ShortPathResponse(PGGraph()))
            except NetworkClientError as e:
                self.view.showError(str(e))

        # show graph in qgis
        builder = GraphBuilder()
        builder.setGraph(response.graph)
        vertexLayer = builder.createVertexLayer(True)
        edgeLayer = builder.createEdgeLayer(True)

    def __getGraph(self):
        if not self.view.hasInput():
            self.view.showError("Please select a graph!")
            return None

        if self.view.isInputLayer():
            # todo: graph layer handling
            layer = self.view.getInputLayer()
        else:
            # if file path as input
            path = self.view.getInputPath()
            fileName, extension = os.path.splitext(path)
            if extension == ".graphml":
                graph = PGGraph()
                graph.readGraphML(path)
                return graph
