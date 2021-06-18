import os

from .base import BaseController

from ..models.GraphBuilder import GraphBuilder
from ..models.PGGraph import PGGraph
from .. import helperFunctions as helper

from qgis.core import QgsVectorLayer, QgsProject, QgsTask, QgsApplication, QgsMessageLog, Qgis
from qgis.utils import iface


class CreateGraphController(BaseController):

    # class variables shared by all instances
    activeGraphTasks = []
    maxNumberTasks = 3

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
        if len(self.activeGraphTasks) >= self.maxNumberTasks:
            self.view.showWarning("Can not building graph due to task limit of {}!".format(self.maxNumberTasks))
            return

        self.view.showInfo("Start graph building..")
        builder = GraphBuilder()
        builder.setOption("createGraphAsLayers", False)

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

        # set builder options for random graph
        if self.view.isRandom():
            builder.setOption("createRandomGraph", True)
            numVertices = 100
            builder.setRandomOptions("numberOfVertices", numVertices)
            area = "Germany"
            builder.setRandomOptions("area", area)

        # set vector layer in builder if input layer exist
        elif self.view.hasInput() and self.view.isInputLayer():
            layer = self.view.getInputLayer()
            # build graph from layer
            builder.setVectorLayer(layer)

        # if file path as input
        elif self.view.hasInput() and not self.view.isInputLayer():
            path = self.view.getInputPath()
            fileName, extension = os.path.splitext(path)
            if extension == ".graphml":
                # create graph from .graphml file
                graph = PGGraph()
                graph.readGraphML(path)

                if not graph:
                    self.view.showError("File can not be parsed!")
                    return

                # set graph to graph builder
                builder.setGraph(graph)

                # create graph layers
                vertexLayer = builder.createVertexLayer(False)
                edgeLayer = builder.createEdgeLayer(False)

                self.saveGraph(graph, vertexLayer, edgeLayer)
                self.view.showSuccess("Graph created!")
                return
            else:
                # load shape file and set this layer in builder
                layer = QgsVectorLayer(path, "", "ogr")
                # build graph from layer
                builder.setVectorLayer(layer)

        # no input and not random
        else:
            self.view.showWarning("No input and not random graph!")
            return

        # create and run task from function
        graphTask = QgsTask.fromFunction("Make graph task", builder.makeGraphTask, on_finished=self.completed)
        self.activeGraphTasks.append(graphTask)
        QgsApplication.taskManager().addTask(graphTask)

    def completed(self, exception, result=None):
        """
        Processes the make graph task results
        :param exception: possible exception raised in task
        :param result: return value of task
        :return:
        """
        QgsMessageLog.logMessage("Process make graph task results", level=Qgis.Info)

        # first remove all completed or canceled tasks from list
        self.activeGraphTasks = [task for task in self.activeGraphTasks if task.isActive()]
        QgsMessageLog.logMessage("Remaining tasks: {}".format(len(self.activeGraphTasks)), level=Qgis.Info)

        if exception is None:
            if result is None:
                QgsMessageLog.logMessage("Task completed with no result", level=Qgis.Warning)
            else:
                graph = result["graph"]
                vertexLayer = result["vertexLayer"]
                edgeLayer = result["edgeLayer"]
                if not graph:
                    self.view.showError("Error during graph creation!")
                    return

                # save graph to destination
                self.saveGraph(graph, vertexLayer, edgeLayer)

                self.view.showSuccess("Graph created!")
                iface.messageBar().pushMessage("Success", "Graph created!", level=Qgis.Success)
        else:
            QgsMessageLog.logMessage("Exception: {}".format(exception), level=Qgis.Critical)
            raise exception

    def saveGraph(self, graph, vertexLayer, edgeLayer):
        """
        Saves graph to destination
        :param graph: PGGraph
        :param vertexLayer: graph vertices
        :param edgeLayer: graph edges
        :return:
        """
        savePath = self.view.getSavePath()
        if savePath:
            fileName, extension = os.path.splitext(savePath)
            if extension == ".graphml":
                graph.writeGraphML(savePath)
            else:
                # if layer path as .shp
                vertexLayer = helper.saveLayer(vertexLayer, vertexLayer.name(), "vector",
                                               fileName + "_vertices" + extension, extension)
                edgeLayer = helper.saveLayer(edgeLayer, edgeLayer.name(), "vector", fileName + "_edges" + extension,
                                             extension)

                # change layer names
                vertexLayer.setName(os.path.basename(fileName) + "Vertices")
                edgeLayer.setName(os.path.basename(fileName) + "Edges")

        # add layer to project
        QgsProject.instance().addMapLayer(vertexLayer)
        QgsProject.instance().addMapLayer(edgeLayer)
