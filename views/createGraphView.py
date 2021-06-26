from .baseContentView import BaseContentView
from ..controllers.graph import CreateGraphController
from ..helperFunctions import getImagePath

from qgis.core import QgsMapLayerProxyModel, QgsTask

from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem,QPushButton
from PyQt5.QtGui import QIcon

import time


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"

        # set up layer inputs
        self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer)
        # self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer | QgsMapLayerProxyModel.RasterLayer | QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.create_graph_poi_input.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dialog.create_graph_raster_input.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dialog.create_graph_polygon_input.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.create_graph_additionalline_input.setFilters(QgsMapLayerProxyModel.LineLayer)

        # set null layer as default
        self.dialog.create_graph_poi_input.setCurrentIndex(0)
        self.dialog.create_graph_raster_input.setCurrentIndex(0)
        self.dialog.create_graph_polygon_input.setCurrentIndex(0)
        self.dialog.create_graph_additionalline_input.setCurrentIndex(0)

        # show layer fields
        self.dialog.create_graph_cost_input.setLayer(self.getInputLayer())
        self.dialog.create_graph_input.layerChanged.connect(self.dialog.create_graph_cost_input.setLayer)

        # show raster bands
        self.dialog.create_graph_raster_input.layerChanged.connect(self.dialog.create_graph_rasterband_input.setLayer)

        # set up file upload
        self.dialog.create_graph_input_tools.clicked.connect(
            lambda: self._browseFile("create_graph_input", "Shape files (*.shp);;GraphML (*.graphml )")
        )

        # set up tasks table
        self.dialog.graph_tasks_table.setColumnCount(4)
        self.dialog.graph_tasks_table.setColumnWidth(0, 100)
        self.dialog.graph_tasks_table.setColumnWidth(2, 100)
        self.dialog.graph_tasks_table.setColumnWidth(3, 60)
        # stretch remaining column
        self.dialog.graph_tasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dialog.graph_tasks_table.setHorizontalHeaderLabels(["Task Id", "Description", "State", "Discard"])

        # hide all unused inputs
        self.dialog.create_graph_cost_label.hide()
        self.dialog.create_graph_cost_input.hide()

        self.dialog.create_graph_coordinatetype_label.hide()
        self.dialog.create_graph_coordinatetype_planar.hide()
        self.dialog.create_graph_coordinatestype_spherical.hide()

        self.dialog.create_graph_poi_label.hide()
        self.dialog.create_graph_poi_input.hide()
        self.dialog.create_graph_poi_input_tools.hide()

        self.dialog.create_graph_rastertype_label.hide()
        self.dialog.create_graph_rastertype_input.hide()

        self.dialog.create_graph_rasterrange_label.hide()
        self.dialog.create_graph_rasterrangemode_label.hide()
        self.dialog.create_graph_rasterrange_scale_input.hide()
        self.dialog.create_graph_rasterrange_cutoff_input.hide()
        self.dialog.create_graph_rastermin_label.hide()
        self.dialog.create_graph_rastermin_input.hide()
        self.dialog.create_graph_rastermax_label.hide()
        self.dialog.create_graph_rastermax_input.hide()

        self.dialog.create_graph_polygontype_label.hide()
        self.dialog.create_graph_polygontype_input.hide()

        self.dialog.create_graph_crs_label.hide()
        self.dialog.create_graph_crs_input.hide()

        # disable input field if random is checked
        self.dialog.random_graph_checkbox.stateChanged.connect(self.dialog.create_graph_input.setDisabled)
        self.dialog.random_graph_checkbox.stateChanged.connect(self.dialog.create_graph_input_tools.setDisabled)

        # set up controller
        self.controller = CreateGraphController(self)

        self.dialog.create_graph_create_btn.clicked.connect(self.controller.createGraph)
        # immediately disable button and enable after 1 seconds
        self.dialog.create_graph_create_btn.clicked.connect(self._disableButton)

    def _disableButton(self):
        """
        Disables the button and enables it after 1 seconds
        :return:
        """
        self.dialog.create_graph_create_btn.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.dialog.create_graph_create_btn.setEnabled(True))

    def hasInput(self):
        return self.dialog.create_graph_input.count() > 0

    def isInputLayer(self):
        """
        True: if input is layer
        False: if input is path
        :return:
        """
        if self.dialog.create_graph_input.currentLayer():
            return True
        return False

    def getInputLayer(self):
        """
        Returns the current selected layer or none if path is sleceted
        :return: Layer or None if path is selected
        """
        return self.dialog.create_graph_input.currentLayer()

    def getInputPath(self):
        """
        Returns input path of selected file path in layer combobox
        :return: Path to file or None if layer is selected
        """
        # assumed that only one additional item is inserted
        if self.hasInput() and not self.isInputLayer():
            return self.dialog.create_graph_input.additionalItems()[0]
        return None

    def isRandom(self):
        return self.dialog.random_graph_checkbox.isChecked()

    def setSavePathFilter(self, filter):
        self.dialog.create_graph_dest_output.setFilter(filter)

    def getSavePath(self):
        return self.dialog.create_graph_dest_output.filePath()

    # advanced parameters

    def addConnectionType(self, type, userData=None):
        self.dialog.create_graph_connectiontype_input.addItem(type, userData)

    def getConnectionType(self):
        return self.dialog.create_graph_connectiontype_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def addDistance(self, distance, userData=None):
        self.dialog.create_graph_distance_input.addItem(distance, userData)

    def getDistance(self):
        return self.dialog.create_graph_distance_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def getCostField(self):
        return self.dialog.create_graph_cost_input.currentField()

    def getCoordinateType(self):
        if self.dialog.create_graph_coordinatetype_planar.isChecked():
            return "planar"
        else:
            return "spherical"

    def getPOILayer(self):
        return self.dialog.create_graph_poi_input.currentLayer()

    def getRasterLayer(self):
        return self.dialog.create_graph_raster_input.currentLayer()

    def getRasterBand(self):
        return self.dialog.create_graph_raster_input.currentBand()

    def addRasterType(self, type, userData=None):
        self.dialog.create_graph_rastertype_input.addItem(type, userData)

    def getRasterType(self):
        return self.dialog.create_graph_rastertype_input.currentText(), self.dialog.create_graph_rastertype_input.currentData()

    def getRasterMinimum(self):
        return self.dialog.create_graph_rastermin_input.int()

    def getRasterMaximum(self):
        return self.dialog.create_graph_rastermax_input.int()

    def isRasterRangeModeSelected(self):
        return True if self.getRasterRangeMode() else False

    def getRasterRangeMode(self):
        if self.dialog.create_graph_rasterrange_scale_input.isChecked():
            return "scale"
        elif self.dialog.create_graph_rasterrange_cutoff_input.isChecked():
            return "cut-off"
        # if both not checked
        return False

    def getPolygonLayer(self):
        return self.dialog.create_graph_polygon_input.currentLayer()

    def addPolygonType(self, type, userData=None):
        self.dialog.create_graph_polygontype_input.addItem(type, userData)

    def getPolygonType(self):
        return self.dialog.create_graph_polygontype_input.currentText(), self.dialog.create_graph_rastertype_input.currentData()

    def getCRS(self):
        return self.dialog.create_graph_crs_input.crs()

    def getAdditionalLineLayer(self):
        return self.dialog.create_graph_additionalline_input.currentLayer()

    # task overview

    def __getTaskStatus(self, status):
        """
        Return the task status as string
        :param status: int
        :return:
        """
        statusDict = {
            QgsTask.Queued: "queued",
            QgsTask.OnHold: "onHold",
            QgsTask.Running: "running",
            QgsTask.Complete: "complete",
            QgsTask.Terminated: "terminated",
        }
        return statusDict.get(status, "unknown")

    def __setTableRow(self, row, task, taskId):
        taskIdItem = QTableWidgetItem(str(taskId))
        descriptionItem = QTableWidgetItem(task.description())
        statusItem = QTableWidgetItem(self.__getTaskStatus(task.status()))
        self.dialog.graph_tasks_table.setItem(row, 0, taskIdItem)
        self.dialog.graph_tasks_table.setItem(row, 1, descriptionItem)
        self.dialog.graph_tasks_table.setItem(row, 2, statusItem)

        # Add cancel button
        cancelButton = QPushButton(QIcon(getImagePath("close.svg")), "")
        cancelButton.setFlat(True)
        cancelButton.setIconSize(QSize(25, 25))
        cancelButton.clicked.connect(lambda: self.controller.discardTask(taskId))
        self.dialog.graph_tasks_table.setCellWidget(row, 3, cancelButton)

    def loadTasksTable(self, tasks):
        """
        Loads task table with passed tasks
        :param tasks: list of taskTuples: (task, taskId)
        :return:
        """
        self.dialog.graph_tasks_table.clearContents()
        self.dialog.graph_tasks_table.setRowCount(len(tasks))
        row = 0
        for tuple in tasks:
            task, taskId = tuple
            self.__setTableRow(row, task, taskId)
            row += 1

    def addTaskToTable(self, task, taskId):
        """
        Adds a task to end of table
        :param task:
        :param taskId:
        :return:
        """
        row = 0
        self.dialog.graph_tasks_table.insertRow(row)
        self.__setTableRow(row, task, taskId)

    def updateTaskInTable(self, task, taskId):
        """
        Update task by given taskId
        :param task:
        :param taskId:
        :return:
        """
        matchItems = self.dialog.graph_tasks_table.findItems(str(taskId), Qt.MatchExactly)
        for item in matchItems:
            # if id column
            if self.dialog.graph_tasks_table.column(item) == 0:
                row = self.dialog.graph_tasks_table.row(item)
                self.__setTableRow(row, task, taskId)

    def removeTaskInTable(self, taskId):
        """
        Removes task by given id
        :param taskId:
        :return:
        """
        matchItems = self.dialog.graph_tasks_table.findItems(str(taskId), Qt.MatchExactly)
        for item in matchItems:
            # if id column
            if self.dialog.graph_tasks_table.column(item) == 0:
                row = self.dialog.graph_tasks_table.row(item)
                self.dialog.graph_tasks_table.removeRow(row)

    # log

    def setLogText(self, text):
        self.dialog.create_graph_log.setPlainText(self._logText(text))

    def insertLogText(self, text):
        self.dialog.create_graph_log.insertPlainText(self._logText(text))

    def setLogHtml(self, text):
        self.dialog.create_graph_log.setHtml(text)

    def insertLogHtml(self, text):
        self.dialog.create_graph_log.insertHtml(text)

    def clearLog(self):
        self.dialog.create_graph_log.clear()

    def getLogText(self):
        return self.dialog.create_graph_log.toPlainText()

    def getLogHtml(self):
        return self.dialog.create_graph_log.toHtml()

    def _logText(self, text):
        return "{asctime} - {text}".format(asctime=time.asctime(), text=text)