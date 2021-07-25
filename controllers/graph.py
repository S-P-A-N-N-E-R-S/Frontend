import os

from .base import BaseController

from ..models.GraphBuilder import GraphBuilder
from ..models.PGGraph import PGGraph
from .. import helperFunctions as helper

from qgis.core import QgsVectorLayer, QgsProject


class CreateGraphController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: CreateGraphView
        """
        super().__init__(view)

        self.view.addConnectionType("Nearest neighbor")
        self.view.addConnectionType("Complete")
        self.view.addConnectionType("ShortestPathNetwork")

        self.view.addDistance("Euclidean")
        self.view.addDistance("Manhatten")
        self.view.addDistance("Speed")

        self.view.addRasterType("elevation")
        self.view.addRasterType("prohibited area")
        self.view.addRasterType("cost")
        self.view.addRasterType("rgb vector")

        self.view.addPolygonType("prohibited area")

        # set save path formats
        self.view.setSavePathFilter("GraphML (*.graphml );;Shape files (*.shp)")

    def createGraph(self):
        builder = GraphBuilder()
        builder.setOption("createGraphAsLayers", False)
        graph = None
        graphName = "New"   # default name

        # raster data
        rasterLayer = self.view.getRasterLayer()
        if rasterLayer:
            builder.setRasterLayer(rasterLayer)

        # polygon data
        polygonLayer = self.view.getPolygonLayer()
        if polygonLayer:
            builder.setPolygonLayer(polygonLayer)

        # poi layer
        poiLayer = self.view.getPOILayer()
        if poiLayer and self.view.getConnectionType()[0] == "ShortestPathNetwork":
            builder.setAdditionalLineLayer(poiLayer)

        # additional line layer
        additionalLineLayer = self.view.getAdditionalLineLayer()
        if additionalLineLayer:
            builder.setAdditionalLineLayer(additionalLineLayer)

        # set options
        builder.setOption("connectionType", self.view.getConnectionType()[0])
        builder.setOption("edgeDirection", "Directed")
        builder.setOption("speedOption", self.view.getCostField())
        builder.setOption("distanceStrategy", self.view.getDistance()[0])

        # create random graph
        if self.view.isRandom():
            graphName = "Random"
            builder.setOption("createRandomGraph", True)
            numVertices = 100
            builder.setRandomOptions("numberOfVertices", numVertices)
            area = "Germany"
            builder.setRandomOptions("area", area)
            graph = builder.makeGraph()

        # create graph from input layer
        elif self.view.hasInput():
            layer = None
            # if layer as Input
            if self.view.isInputLayer():
                layer = self.view.getInputLayer()
            # if file path as input
            else:
                path = self.view.getInputPath()
                fileName, extension = os.path.splitext(path)
                graphName = os.path.basename(fileName)
                if extension == ".graphml":
                    graph = PGGraph()
                    graph.readGraphML(path)

                    # set graph to graph builder
                    builder.setGraph(graph)
                else:
                    # load shape file
                    layer = QgsVectorLayer(path, "", "ogr")

            if layer:
                graphName = layer.name()
                # build graph from layer
                builder.setVectorLayer(layer)

                graph = builder.makeGraph()

        # no input and not random
        else:
            self.view.showWarning("No input and not random graph!")
            return

        if not graph:
            self.view.showError("Error during graph creation!")
            return

        # create graph layer
        graphLayer = builder.createGraphLayer(False)

        # save graph to destination
        savePath = self.view.getSavePath()
        if savePath:
            fileName, extension = os.path.splitext(savePath)
            graphName = os.path.basename(fileName)
            if extension == ".graphml":
                graph.writeGraphML(savePath)
            else:
                # if layer path as .shp
                # create vector layer from graph layer
                [vectorPointLayer, vectorLineLayer] = graphLayer.createVectorLayer()

                # save vector layer to path
                # vectorPointLayer = helper.saveLayer(vectorPointLayer, vectorPointLayer.name(), "vector", savePath, extension)
                vectorLineLayer = helper.saveLayer(vectorLineLayer, vectorLineLayer.name(), "vector", savepath, extension)

                # add vector layer to project
                QgsProject.instance().addMapLayer(vectorPointLayer)
                QgsProject.instance().addMapLayer(vectorLineLayer)

        # add graph layer to project
        graphLayer.setName(graphName + "GraphLayer")
        QgsProject.instance().addMapLayer(graphLayer)

        self.view.showSuccess("Graph created!")
