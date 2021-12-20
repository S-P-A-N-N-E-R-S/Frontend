#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz, Tim Hartmann
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

import os

from .base import BaseController

from ..models.GraphBuilder import GraphBuilder
from ..models.QgsGraphLayer import QgsGraphLayer
from .. import helperFunctions as helper

from qgis.core import *
from qgis.utils import iface


class GraphController(BaseController):

    # class variable contains list of taskTuples: (task, taskId)
    activeGraphTasks = []
    # allowed number of parallel tasks
    maxNumberTasks = 3

    def __init__(self, view):
        """
        Constructor
        :type view: GraphView
        """
        super().__init__(view)                           
             
        self.view.addRandomArea(self.tr("Germany"), "Germany")
        self.view.addRandomArea(self.tr("France"), "France")
        self.view.addRandomArea(self.tr("Osnabrueck"), "Osnabrueck")
        self.view.addRandomArea(self.tr("United States"), "United States")
        self.view.addRandomArea(self.tr("Rome"), "Rome")
        self.view.addRandomArea(self.tr("Australia"), "Australia")

        self.view.addConnectionType(self.tr("Nearest neighbor"), "Nearest neighbor")
        self.view.addConnectionType(self.tr("None"), "None")      
        self.view.addConnectionType(self.tr("Complete"), "Complete")
        self.view.addConnectionType(self.tr("ClusterComplete"), "ClusterComplete")
        self.view.addConnectionType(self.tr("ClusterNN"), "ClusterNN")
        self.view.addConnectionType(self.tr("DistanceNN"), "DistanceNN")
        self.view.addConnectionType(self.tr("Random"), "Random")
        self.view.addConnectionType(self.tr("LineLayerBased"), "LineLayerBased")

        self.view.addEdgeDirection(self.tr("Undirected"), "Undirected")
        self.view.addEdgeDirection(self.tr("Directed"), "Directed")

        self.view.addDistanceStrategy(self.tr("Euclidean"), "Euclidean")
        self.view.addDistanceStrategy(self.tr("Manhattan"), "Manhattan")
        self.view.addDistanceStrategy(self.tr("Geodesic (Haversine formula)"), "Geodesic")
        self.view.addDistanceStrategy(self.tr("Advanced"), "Advanced")
        self.view.addDistanceStrategy(self.tr("Ellipsoidal (Not usable with all CRS)"), "Ellipsoidal")
        self.view.addDistanceStrategy(self.tr("None"), "None")

        # load possibly available active tasks into table and reconnect slots
        for taskTuple in GraphController.activeGraphTasks:
            task, taskId = taskTuple
            task.statusChanged.connect(
                lambda: self.view.updateTaskInTable(task, taskId)
            )
        self.view.loadTasksTable(GraphController.activeGraphTasks)

    def createGraph(self):
        """
        Starts the graph creation process. This function is called from view.
        :return:
        """
        if len(GraphController.activeGraphTasks) >= GraphController.maxNumberTasks:
            self.view.showWarning(self.tr("Can not building graph due to task limit of {}!").format(
                GraphController.maxNumberTasks))
            return

        # no input and not random
        if not self.view.hasInput() and not self.view.isRandom():
            self.view.showWarning(self.tr("No input and not random graph!"))
            return

        self.view.showInfo(self.tr("Start graph building.."))
        self.view.insertLogText("Start graph building..\n")
        builder = GraphBuilder()
        builder.setOption("createGraphAsLayers",False)
        graphName = "New"   # default name
        savePath = self.view.getSavePath()

        # raster data
        for rasterInput in self.view.getRasterData():
            rasterLayer, rasterBand = rasterInput
            if rasterLayer and rasterBand:
                if not rasterLayer.isValid():
                    self.view.showWarning(self.tr("Raster layer:{}[{}] is invalid!").format(rasterLayer.name(), rasterBand))
                    return
                builder.setRasterLayer(rasterLayer, rasterBand)

        # polygon cost layer
        polygonCostLayers = self.view.getPolygonCostLayers()
        for idx, polygonCostLayer in enumerate(polygonCostLayers):
            if not polygonCostLayer.isValid():
                self.view.showWarning(self.tr("Polygon cost layer[{}] is invalid!").format(idx))
                return            
            builder.setPolygonsForCostFunction(polygonCostLayer)           

        # polygon forbidden area
        forbiddenAreaLayer = self.view.getForbiddenAreaLayer()
        if forbiddenAreaLayer:
            if not forbiddenAreaLayer.isValid():
                self.view.showWarning(self.tr("Forbidden area layer is invalid!"))
                return
            builder.setForbiddenAreas(forbiddenAreaLayer)

        # additional point layer
        additionalPointLayer = self.view.getAdditionalPointLayer()
        if additionalPointLayer:
            if not additionalPointLayer.isValid():
                self.view.showWarning(self.tr("Additional point layer is invalid!"))
                return
            if additionalPointLayer.crs() != self.view.getInputLayer().crs():
                self.view.showWarning(self.tr("Invalid crs of additional point layer"))
                return
            builder.setAdditionalPointLayer(additionalPointLayer)

        # set options
        builder.setOption("connectionType", self.view.getConnectionType()[1])
        builder.setOption("neighborNumber", self.view.getNeighborNumber())
        builder.setOption("nnAllowDoubleEdges", self.view.isDoubleEdgesAllowed())
        builder.setOption("distance", self.view.getDistance())
        builder.setOption("clusterNumber", self.view.getClusterNumber())
        builder.setOption("edgeDirection", self.view.getEdgeDirection()[1])
        builder.setOption("distanceStrategy", self.view.getDistanceStrategy()[1])
        builder.setOption("createShortestPathView", self.view.isShortPathViewChecked())
        builder.setOption("randomConnectionNumber", self.view.getRandomEdgesNumber())
        
        if self.view.getConnectionType()[1] == "LineLayerBased":
            lineLayer = self.view.getLineLayerForConnection()
            if not lineLayer.isValid():
                self.view.showWarning(self.tr("Line layer is invalid!"))
                return     
            builder.setLineLayer(lineLayer)

        # set builder options for random graph
        if self.view.isRandom():
            graphName = "Random"
            builder.setOption("createRandomGraph", True)
            builder.setRandomOption("numberOfVertices", self.view.getRandomVerticesNumber())
            builder.setRandomOption("seed", self.view.getRandomSeed())
            # set predefined or user defined random area
            area, areaData = self.view.getRandomArea()
            if areaData == "custom area":
                builder.setRandomOption("area", self.view.getRandomUserArea())
            else:
                builder.setRandomOption("area", area)

        # set vector layer in builder if input layer exist
        elif self.view.hasInput() and self.view.isInputLayer():
            layer = self.view.getInputLayer()
            if not layer.isValid():
                self.view.showWarning(self.tr("Input layer is invalid!"))
                return
            graphName = layer.name()
            # build graph from layer
            builder.setVectorLayer(layer)

        # if graph as input
        elif self.view.hasInput() and not self.view.isInputLayer():
            graph = self.view.getInputGraph()
            if not graph:
                self.view.showError(self.tr("File can not be parsed!"))
                return

            # create empty graph layer
            graphLayer = QgsGraphLayer()

            # set graph to graph layer
            graphLayer.setGraph(graph)

            # set user specified crs
            graphCrs = self.view.getCRS()
            if graphCrs and graphCrs.isValid():
                graphLayer.setCrs(graphCrs)

            success, errorMsg = helper.saveGraph(graph, graphLayer, graphName, savePath, self.view.isRenderGraphChecked())
            if not success:
                self.view.showError(errorMsg)
            else:
                self.view.showSuccess(self.tr("Graph created!"))
            return

        # set advanced cost function
        costFunctions = self.view.getCostFunctions()
        if costFunctions and builder.getOption("distanceStrategy") == "Advanced":
            for index, costFunction in enumerate(costFunctions):
                status = builder.addCostFunction(costFunction)
                if not status == "No error found":
                    self.view.showError(format(status), self.tr("Error in cost function with index {}").format(index))
                    return

        # set name to save path basename
        if savePath:
            fileName, extension = os.path.splitext(savePath)
            graphName = os.path.basename(fileName)

        # create and run task from function
        graphLayer = QgsGraphLayer()
        graphTask = QgsTask.fromFunction("Building graph: {}".format(graphName), builder.makeGraphTask,
                                         graphLayer=graphLayer, graphName=graphName, on_finished=self.completed)
        taskId = QgsApplication.taskManager().addTask(graphTask)
        GraphController.activeGraphTasks.append((graphTask, taskId))

        # add task to table
        graphTask.statusChanged.connect(
            lambda: self.view.updateTaskInTable(graphTask, taskId)  # update task if status changed
        )
        graphTask.progressChanged.connect(
            lambda: self.view.updateTaskInTable(graphTask, taskId)  # update task if progress changed
        )
        self.view.addTaskToTable(graphTask, taskId)

    def completed(self, exception, result=None):
        """
        Processes the make graph task results
        :param exception: possible exception raised in task
        :param result: return value of task
        :return:
        """
        QgsMessageLog.logMessage("Process make graph task results", level=Qgis.Info)

        # first remove all completed or canceled tasks from list
        GraphController.activeGraphTasks = [task for task in GraphController.activeGraphTasks
                                            if task[0].isActive()]
        QgsMessageLog.logMessage("Remaining tasks: {}".format(len(GraphController.activeGraphTasks)),
                                 level=Qgis.Info)

        if exception is None:
            if result is None:
                QgsMessageLog.logMessage("Task completed with no result", level=Qgis.Warning)
                self.view.insertLogText("Graph process completed with no result\n")
            else:
                graph = result["graph"]
                graphLayer = result["graphLayer"]
                graphName = result["graphName"]
                shortestPathViewLayers = result["shortestPathViewLayers"]
                if not graph:
                    self.view.showError(self.tr("Error during graph creation!"))
                    return

                # show shortest path view layers
                for shortestPathViewLayer in shortestPathViewLayers:
                    QgsProject.instance().addMapLayer(shortestPathViewLayer)

                # save graph to destination
                savePath = self.view.getSavePath()
                success, errorMsg = helper.saveGraph(graph, graphLayer, graphName, savePath, self.view.isRenderGraphChecked())
                if not success:
                    self.view.showError(errorMsg)
                else:
                    # show success message
                    self.view.showSuccess(self.tr("Graph created!"))
                    iface.messageBar().pushMessage("Success", self.tr("Graph created!"), level=Qgis.Success)
                    self.view.insertLogText("Graph created!\n")

            self.view.insertLogText("Remaining graph creation processes : {}\n".format(
                len(GraphController.activeGraphTasks)))
        else:
            QgsMessageLog.logMessage("Exception: {}".format(exception), level=Qgis.Critical)
            raise exception

    def discardTask(self, taskId):
        """
        Cancels an active task and removes it from the task table
        :return:
        """
        self.view.removeTaskInTable(taskId)
        # cancel active task if available
        for activeTaskTuple in GraphController.activeGraphTasks:
            activeTask, activeTaskId = activeTaskTuple
            if activeTaskId == taskId:
                activeTask.cancel()
