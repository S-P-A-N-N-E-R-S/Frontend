import os

from qgis.core import QgsSettings

from .base import BaseController
# from ..network.client import Client
from ..models.GraphBuilder import GraphBuilder
from ..models.PGGraph import PGGraph

class OGDFAnalysisController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OGDFAnalysisView
        """
        super().__init__(view)

        # set up client
        self.settings = QgsSettings()
        self.client = None
        host = self.settings.value("protoplugin/host", None)
        port = self.settings.value("protoplugin/port", None)

        # try:
        #     if host and port:
        #         self.client = Client(host, port)
        # except Exception as e:
        #     print(e)

        self.view.addAnalysis("t-Spanner")
        self.view.addAnalysis("minimum spanner")
        self.view.addAnalysis("shortest path")
        self.view.addAnalysis("steiner tree")
        self.view.addAnalysis("delaunay triangulation")

    def runJob(self):
        # if not self.client:
        #     self.view.showWarning("Please configure the server!")
        #     return

        startNodeIndex = self.view.getStartNode()
        endNodeIndex = self.view.getEndNode()

        graph = self.__getGraph()
        if not graph:
            return

        # try:
        #     self.client.connect()
        #
        #     # shortPathRequest = ShortPathRequest(graph, startIndex, endIndex)
        #     # msgLength = self.client.sendShortPathRequest(shortPathRequest)
        #
        #     graph = self.client.readShortPathResponse()
        #
        #     self.client.disconnectSocket()
        # except Exception as e:
        #     print(e)

        # show graph in qgis
        builder = GraphBuilder()
        builder.setGraph(graph)
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
