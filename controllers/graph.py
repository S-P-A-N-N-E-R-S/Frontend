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

        # create random graph
        if self.view.isRandom():
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
                if extension == ".graphml":
                    graph = PGGraph()
                    graph.readGraphML(path)

                    # set graph to graph builder
                    builder.setGraph(graph)
                else:
                    # load shape file
                    layer = QgsVectorLayer(path, "", "ogr")

            if layer:
                # build graph from layer
                builder.setVectorLayer(layer)

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
                    builder.setAdditionalLineLayer(polygonLayer)

                # set options
                builder.setOption("connectionType", self.view.getConnectionType()[0])
                builder.setOption("edgeDirection", "Directed")
                builder.setOption("speedOption", self.view.getCostField())
                builder.setOption("distanceStrategy", self.view.getDistance()[0])

                graph = builder.makeGraph()

        # no input and not random
        else:
            self.view.showWarning("No input and not random graph!")
            return

        if not graph:
            self.view.showError("Error during graph creation!")
            return

        # create graph layers
        vertexLayer = builder.createVertexLayer(False)
        edgeLayer = builder.createEdgeLayer(False)

        # save graph to destination
        savePath = self.view.getSavePath()
        if savePath:
            fileName, extension = os.path.splitext(savePath)
            if extension == ".graphml":
                graph.writeGraphML(savePath)
            else:
                # if layer path as .shp
                vertexLayer = helper.saveLayer(vertexLayer, vertexLayer.name(), "vector", fileName+"_vertices"+extension, extension)
                edgeLayer = helper.saveLayer(edgeLayer, edgeLayer.name(), "vector", fileName+"_edges"+extension, extension)

                # change layer names
                vertexLayer.setName(os.path.basename(fileName)+"Vertices")
                edgeLayer.setName(os.path.basename(fileName)+"Edges")

        # add layer to project
        QgsProject.instance().addMapLayer(vertexLayer)
        QgsProject.instance().addMapLayer(edgeLayer)

        self.view.showSuccess("Graph created!")
