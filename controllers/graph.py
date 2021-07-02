import os

from .base import BaseController

from ..models.GraphBuilder import GraphBuilder
from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer
from .. import helperFunctions as helper

from qgis.core import QgsVectorLayer, QgsProject, QgsTask, QgsApplication, QgsMessageLog, Qgis
from qgis.utils import iface


class CreateGraphController(BaseController):

    # class variable contains list of taskTuples: (task, taskId)
    activeGraphTasks = []
    # allowed number of parallel tasks
    maxNumberTasks = 3

    def __init__(self, view):
        """
        Constructor
        :type view: CreateGraphView
        """
        super().__init__(view)

        self.view.addRandomArea("Germany")
        self.view.addRandomArea("France")
        self.view.addRandomArea("Osnabrueck")
        self.view.addRandomArea("United States")
        self.view.addRandomArea("Rome")
        self.view.addRandomArea("Australia")

        self.view.addConnectionType("None")
        self.view.addConnectionType("Nearest neighbor")
        self.view.addConnectionType("Complete")
        self.view.addConnectionType("ClusterComplete")
        self.view.addConnectionType("ClusterNN")

        self.view.addEdgeDirection("Directed")
        self.view.addEdgeDirection("Undirected")

        self.view.addDistance("Euclidean")
        self.view.addDistance("Manhattan")
        self.view.addDistance("Geodesic")
        self.view.addDistance("Advanced")

        self.view.addRasterType("elevation")
        self.view.addRasterType("prohibited area")
        self.view.addRasterType("cost")
        self.view.addRasterType("rgb vector")

        self.view.addPolygonType("prohibited area")

        # set save path formats
        self.view.setSavePathFilter("GraphML (*.graphml );;Shape files (*.shp)")

        # load possibly available active tasks into table and reconnect slots
        self.view.loadTasksTable(CreateGraphController.activeGraphTasks)
        for taskTuple in CreateGraphController.activeGraphTasks:
            task, taskId = taskTuple
            task.statusChanged.connect(
                lambda: self.view.updateTaskInTable(task, taskId)
            )

    def createGraph(self):
        if len(CreateGraphController.activeGraphTasks) >= CreateGraphController.maxNumberTasks:
            self.view.showWarning("Can not building graph due to task limit of {}!".format(
                CreateGraphController.maxNumberTasks))
            return

        self.view.showInfo("Start graph building..")
        self.view.insertLogText("Start graph building..\n")
        builder = GraphBuilder()
        builder.setOption("createGraphAsLayers", False)
        graphName = "New"   # default name

        # raster data
        rasterLayer = self.view.getRasterLayer()
        rasterBand = self.view.getRasterLayer()
        if rasterLayer and rasterBand:
            builder.setRasterLayer(rasterLayer, rasterBand)

        # polygon cost layer
        polygonCostLayer = self.view.getPolygonCostLayer()
        if polygonCostLayer:
            builder.setPolygonsForCostFunction(polygonCostLayer)

        # polygon forbidden area
        forbiddenAreaLayer = self.view.getForbiddenAreaLayer()
        if forbiddenAreaLayer:
            builder.setForbiddenAreas(forbiddenAreaLayer)

        # additional point layer
        additionalPointLayer = self.view.getAdditionalPointLayer()
        if additionalPointLayer:
            builder.setAdditionalPointLayer(additionalPointLayer)

        # set advanced cost function
        costFunction = self.view.getCostFunction()
        if costFunction:
            if not builder.setCostFunction(costFunction):
                self.view.showWarning("Advanced cost function can not be set!")


        # set options
        builder.setOption("connectionType", self.view.getConnectionType()[0])
        builder.setOption("neighborNumber", self.view.getNeighborNumber())
        builder.setOption("nnAllowDoubleEdges", self.view.isDoubleEdgesAllowed())
        builder.setOption("clusterNumber", self.view.getClusterNumber())
        builder.setOption("edgeDirection", self.view.getEdgeDirection()[0])
        builder.setOption("distanceStrategy", self.view.getDistance()[0])

        # set builder options for random graph
        if self.view.isRandom():
            graphName = "Random"
            builder.setOption("createRandomGraph", True)
            builder.setRandomOption("numberOfVertices", self.view.getRandomVerticesNumber())
            builder.setRandomOption("area", self.view.getRandomArea()[0])

        # set vector layer in builder if input layer exist
        elif self.view.hasInput() and self.view.isInputLayer():
            layer = self.view.getInputLayer()
            graphName = layer.name()
            # build graph from layer
            builder.setVectorLayer(layer)

        # if file path as input
        elif self.view.hasInput() and not self.view.isInputLayer():
            path = self.view.getInputPath()
            fileName, extension = os.path.splitext(path)
            graphName = os.path.basename(fileName)
            if extension == ".graphml":
                # create graph from .graphml file
                graph = ExtGraph()
                graph.readGraphML(path)

                if not graph:
                    self.view.showError("File can not be parsed!")
                    return

                # set graph to graph builder
                builder.graph = graph

                # create graph layer
                graphLayer = builder.createGraphLayer(False)

                self.saveGraph(graph, graphLayer, graphName)
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

        # set name to save path basename
        savePath = self.view.getSavePath()
        if savePath:
            fileName, extension = os.path.splitext(savePath)
            graphName = os.path.basename(fileName)

        # create and run task from function
        graphLayer = QgsGraphLayer()
        graphTask = QgsTask.fromFunction("Building graph: {}".format(graphName), builder.makeGraphTask,
                                         graphLayer=graphLayer, graphName=graphName, on_finished=self.completed)
        taskId = QgsApplication.taskManager().addTask(graphTask)
        CreateGraphController.activeGraphTasks.append((graphTask, taskId))

        # add task to table
        self.view.addTaskToTable(graphTask, taskId)
        graphTask.statusChanged.connect(
            lambda: self.view.updateTaskInTable(graphTask, taskId)  # update task if status changed
        )

    def completed(self, exception, result=None):
        """
        Processes the make graph task results
        :param exception: possible exception raised in task
        :param result: return value of task
        :return:
        """
        QgsMessageLog.logMessage("Process make graph task results", level=Qgis.Info)

        # first remove all completed or canceled tasks from list
        CreateGraphController.activeGraphTasks = [task for task in CreateGraphController.activeGraphTasks
                                                  if task[0].isActive()]
        QgsMessageLog.logMessage("Remaining tasks: {}".format(len(CreateGraphController.activeGraphTasks)),
                                 level=Qgis.Info)

        if exception is None:
            if result is None:
                QgsMessageLog.logMessage("Task completed with no result", level=Qgis.Warning)
                self.view.insertLogText("Graph process completed with no result\n")
            else:
                graph = result["graph"]
                graphLayer = result["graphLayer"]
                graphName = result["graphName"]
                if not graph:
                    self.view.showError("Error during graph creation!")
                    return

                # save graph to destination
                self.saveGraph(graph, graphLayer, graphName)

                self.view.showSuccess("Graph created!")
                iface.messageBar().pushMessage("Success", "Graph created!", level=Qgis.Success)
                self.view.insertLogText("Graph created!\n")

            self.view.insertLogText("Remaining graph creation processes : {}\n".format(
                len(CreateGraphController.activeGraphTasks)))
        else:
            QgsMessageLog.logMessage("Exception: {}".format(exception), level=Qgis.Critical)
            raise exception

    def saveGraph(self, graph, graphLayer, graphName=""):
        """
        Saves graph to destination
        :param graph: ExtGraph
        :param graphLayer:
        :param graphName:
        :return:
        """
        savePath = self.view.getSavePath()
        if savePath:
            fileName, extension = os.path.splitext(savePath)
            if extension == ".graphml":
                graph.writeGraphML(savePath)
            else:
                # if layer path as .shp
                # create vector layer from graph layer
                vectorLayer = graphLayer.createVectorLayer()

                # save vector layer to path
                vectorLayer = helper.saveLayer(vectorLayer, vectorLayer.name(), "vector", savePath, extension)

                # add vector layer to project
                QgsProject.instance().addMapLayer(vectorLayer)

        # add graph layer to project
        graphLayer.setName(graphName + "GraphLayer")
        QgsProject.instance().addMapLayer(graphLayer)

    def discardTask(self, taskId):
        """
        Cancels an active task and removes it from the task table
        :return:
        """
        self.view.removeTaskInTable(taskId)
        # cancel active task if available
        for activeTaskTuple in CreateGraphController.activeGraphTasks:
            activeTask, activeTaskId = activeTaskTuple
            if activeTaskId == taskId:
                activeTask.cancel()
