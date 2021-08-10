from .baseContentView import BaseContentView
from .widgets.QgsCostFunctionDialog import QgsCostFunctionDialog
from ..controllers.graph import CreateGraphController
from ..helperFunctions import getImagePath, getRasterFileFilter, getVectorFileFilter
from ..models.ExtGraph import ExtGraph

from qgis.core import QgsMapLayerProxyModel, QgsTask, QgsUnitTypes, QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox, QgsProjectionSelectionWidget
from qgis.utils import iface

from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QPushButton, QHBoxLayout, QSizePolicy, QLineEdit, QToolButton
from PyQt5.QtGui import QIcon

import time, os


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"

        # set up layer inputs
        self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer)
        self.dialog.create_graph_raster_input.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dialog.create_graph_polycost_input.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.create_graph_forbiddenarea_input.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.create_graph_additionalpoint_input.setFilters(QgsMapLayerProxyModel.PointLayer)

        # set null layer as default
        self.dialog.create_graph_raster_input.setCurrentIndex(0)
        self.dialog.create_graph_polycost_input.setCurrentIndex(0)
        self.dialog.create_graph_forbiddenarea_input.setCurrentIndex(0)
        self.dialog.create_graph_additionalpoint_input.setCurrentIndex(0)

        # enable and disable inputs when input is changed
        self.dialog.create_graph_input.currentIndexChanged.connect(self._inputChanged)
        self.dialog.random_graph_checkbox.stateChanged.connect(self._inputChanged)

        # set up file upload
        self.dialog.create_graph_input_tools.clicked.connect(
            lambda: self._browseFile("create_graph_input", "GraphML (*.graphml );;"+getVectorFileFilter())
        )

        # show output placeholder
        self.dialog.create_graph_dest_output.lineEdit().setPlaceholderText("[Save to temporary layer]")
        # set save path formats
        self.dialog.create_graph_dest_output.setFilter("GraphML (*.graphml );;"+getVectorFileFilter())

        # enable and disable inputs when connection type is changed
        self.dialog.create_graph_connectiontype_input.currentIndexChanged.connect(self._connectionTypeChanged)

        # standard units
        self.standardDistanceUnits = [
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceMeters), QgsUnitTypes.DistanceMeters),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceKilometers), QgsUnitTypes.DistanceKilometers),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceFeet), QgsUnitTypes.DistanceFeet),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceNauticalMiles), QgsUnitTypes.DistanceNauticalMiles),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceYards), QgsUnitTypes.DistanceYards),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceMiles), QgsUnitTypes.DistanceMiles),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceCentimeters), QgsUnitTypes.DistanceCentimeters),
            (QgsUnitTypes.toString(QgsUnitTypes.DistanceMillimeters), QgsUnitTypes.DistanceMillimeters)
        ]

        # enable and disable inputs when distance strategy is changed
        self.dialog.create_graph_distancestrategy_input.currentIndexChanged.connect(self._distanceStrategyChanged)

        # show raster bands
        self.dialog.create_graph_raster_input.layerChanged.connect(self.dialog.create_graph_rasterband_input.setLayer)

        # set up add raster data button
        self.dialog.create_graph_raster_plus_btn.clicked.connect(self._addRasterDataInput)

        # set up advance cost widget button
        self.dialog.create_graph_costfunction_define_btn.clicked.connect(lambda: self._showCostFunctionDialog(0))

        # set up add cost function button
        self.dialog.create_graph_costfunction_add_btn.clicked.connect(self._addCostFunctionInput)

        # set up tasks table
        self.dialog.graph_tasks_table.setColumnCount(4)
        self.dialog.graph_tasks_table.setColumnWidth(0, 100)
        self.dialog.graph_tasks_table.setColumnWidth(2, 100)
        self.dialog.graph_tasks_table.setColumnWidth(3, 80)
        # stretch remaining column
        self.dialog.graph_tasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dialog.graph_tasks_table.setHorizontalHeaderLabels([self.tr("Task Id"), self.tr("Description"),
                                                                 self.tr("State"), self.tr("Discard")])

        # set up crs selection
        self.dialog.create_graph_crs_input.setOptionVisible(QgsProjectionSelectionWidget.CurrentCrs, False)

        # set up random extent
        self.addRandomArea(self.tr("Custom"), "custom area")
        self.dialog.create_graph_randomarea_extent.setMapCanvas(iface.mapCanvas())
        self.dialog.create_graph_randomarea_input.currentIndexChanged.connect(self._randomAreaChanged)

        # set up controller
        self.controller = CreateGraphController(self)

        self.dialog.create_graph_create_btn.clicked.connect(self.controller.createGraph)
        # immediately disable button and enable after 1 seconds
        self.dialog.create_graph_create_btn.clicked.connect(self._disableButton)

        self._inputChanged()

    def _inputChanged(self):
        """
        Disables and enables parameter inputs based on input
        :return:
        """
        inputText = self.dialog.create_graph_input.currentText()
        root, ext = os.path.splitext(inputText)
        # show only crs input and hide other params if graph file is selected and not random
        self.dialog.create_graph_advanced_parameters_groupbox.setHidden(ext == ".graphml" and not self.isRandom())
        self.dialog.create_graph_crs_label.setVisible(ext == ".graphml" and not self.isRandom())
        self.dialog.create_graph_crs_input.setVisible(ext == ".graphml" and not self.isRandom())

        # disable input field and enable random params if random is checked
        self.dialog.create_graph_input_widget.setDisabled(self.isRandom())
        self.dialog.create_graph_randomNumber_input.setEnabled(self.isRandom())
        self.dialog.create_graph_randomarea_widget.setEnabled(self.isRandom())

        # update distance units
        self._updateDistanceUnits()

        # show input layer type specific params
        layer = self.getInputLayer()
        isPointLayer = layer is not None and layer.geometryType() == QgsWkbTypes.PointGeometry
        isLineLayer = layer is not None and layer.geometryType() == QgsWkbTypes.LineGeometry and not self.isRandom()

        self.dialog.create_graph_connectiontype_input.setEnabled(isPointLayer or self.isRandom())

        if isLineLayer:
            # disable all parameters associated with connection type
            self.dialog.create_graph_connectiontype_input.setCurrentIndex(
                self.dialog.create_graph_connectiontype_input.findData("None"))

        self.dialog.create_graph_additionalpoint_input.setEnabled(isLineLayer)

    def _updateDistanceUnits(self):
        """
        Updates distances units belonging to layer map unit
        :return:
        """
        layer = self.getInputLayer()

        # set units according to layer crs or random
        unit = QgsUnitTypes.DistanceUnknownUnit
        if self.isRandom():
            # random graph has degree unit
            unit = QgsUnitTypes.DistanceDegrees
        elif layer is not None:
            layerCrs = layer.crs()
            if layerCrs.isValid():
                unit = layerCrs.mapUnits()

        self.dialog.create_graph_distance_unit_input.clear()
        if QgsUnitTypes.unitType(unit) != QgsUnitTypes.Standard:
            # if geographic or unknown unit
            self.dialog.create_graph_distance_unit_input.addItem(QgsUnitTypes.toString(unit), unit)
        else:
            # if standard unit like meters etc.
            for standardUnit in self.standardDistanceUnits:
                self.dialog.create_graph_distance_unit_input.addItem(standardUnit[0], standardUnit[1])
                self.dialog.create_graph_distance_unit_input.setCurrentIndex(
                    self.dialog.create_graph_distance_unit_input.findData(unit))

    def _connectionTypeChanged(self):
        """
        Disables and enables parameter inputs based on selected connection type
        :return:
        """
        _, connectionType = self.getConnectionType()
        self.dialog.create_graph_nearest_neighbor_widget.setEnabled(connectionType in ["Nearest neighbor", "ClusterNN",
                                                                                       "DistanceNN"])
        self.dialog.create_graph_numberneighbor_input.setEnabled(connectionType != "DistanceNN")
        self.dialog.create_graph_distance_widget.setEnabled(connectionType == "DistanceNN")
        self.dialog.create_graph_clusternumber_input.setEnabled(connectionType in ["ClusterComplete", "ClusterNN"])

    def _distanceStrategyChanged(self):
        """
        Disables and enables parameter inputs based on selected distance strategy
        :return:
        """
        _, distanceStrategy = self.getDistanceStrategy()
        self.dialog.create_graph_costfunction_widget.setEnabled(distanceStrategy == "Advanced")
        self.dialog.create_graph_polycost_input.setEnabled(distanceStrategy == "Advanced")
        self.dialog.create_graph_rasterdata_widget.setEnabled(distanceStrategy == "Advanced")

    def _addRasterDataInput(self):
        """
        Appends a new raster band input line
        :return:
        """
        #  change add button to remove button
        lastLayout = self.dialog.create_graph_rasterdata_widget.layout().itemAt(self.dialog.create_graph_rasterdata_widget.layout().count()-1)
        button = lastLayout.itemAt(lastLayout.count()-1).widget()
        button.setText("➖")
        button.setToolTip(self.tr("Remove raster input"))
        button.clicked.disconnect()
        button.clicked.connect(lambda: self._removeLayoutFromWidget("create_graph_rasterdata_widget", lastLayout))

        layerComboBox = QgsMapLayerComboBox()
        layerComboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        layerComboBox.setAllowEmptyLayer(True)
        layerComboBox.setCurrentIndex(0)
        layerComboBox.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        layerComboBox.setToolTip(self.tr("Select raster layer"))

        bandComboBox = QgsRasterBandComboBox()
        bandComboBox.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))
        bandComboBox.setMinimumSize(150, 0)
        bandComboBox.setToolTip(self.tr("Select raster band"))
        layerComboBox.layerChanged.connect(bandComboBox.setLayer)

        addButton = QPushButton("➕")
        addButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        addButton.setMaximumSize(25, 25)
        addButton.setToolTip(self.tr("Add raster layer"))
        addButton.clicked.connect(self._addRasterDataInput)

        layout = QHBoxLayout()
        layout.addWidget(layerComboBox)
        layout.addWidget(bandComboBox)
        layout.addWidget(addButton)

        self.dialog.create_graph_rasterdata_widget.layout().addLayout(layout)

    def _addCostFunctionInput(self):
        """
        Appends a new cost function input line
        :return:
        """
        costFunctionWidget = self.dialog.create_graph_costfunction_widget
        #  change add button to remove button
        lastLayout = costFunctionWidget.layout().itemAt(costFunctionWidget.layout().count() - 1)
        button = lastLayout.itemAt(lastLayout.count() - 1).widget()
        button.setText("➖")
        button.setToolTip(self.tr("Remove cost function"))
        button.clicked.disconnect()
        button.clicked.connect(lambda: self._removeLayoutFromWidget("create_graph_costfunction_widget", lastLayout))

        costLineEdit = QLineEdit()
        costLineEdit.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        costLineEdit.setToolTip(self.tr("Define advanced cost function"))

        costWidgetDialogButton = QToolButton()
        costWidgetDialogButton.setText("...")
        costWidgetDialogButton.setToolTip(self.tr("Show cost editor"))

        addButton = QPushButton("➕")
        addButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        addButton.setMaximumSize(25, 25)
        addButton.clicked.connect(self._addCostFunctionInput)
        addButton.setToolTip(self.tr("Add cost function"))

        layout = QHBoxLayout()
        layout.addWidget(costLineEdit)
        layout.addWidget(costWidgetDialogButton)
        layout.addWidget(addButton)

        costFunctionWidget.layout().addLayout(layout)

        # show cost function dialog when button is clicked
        costWidgetDialogButton.clicked.connect(lambda: self._showCostFunctionDialog(
            costFunctionWidget.layout().indexOf(layout)))

    def _removeLayoutFromWidget(self, widget, layout):
        """
        Removes the passed layout from widget
        :param layout to be deleted
        :return:
        """
        widget = getattr(self.dialog, widget)
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()
        widget.layout().removeItem(layout)

    def _showCostFunctionDialog(self, index):
        """
        Creates and displays the cost function Dialog
        :return:
        """
        costFunctionDialog = QgsCostFunctionDialog()
        costFunctionDialog.setCostFunction(self.getCostFunction(index))
        costFunctionDialog.setVectorLayer(self.getInputLayer())
        costFunctionDialog.setPolygonLayer(self.getPolygonCostLayer())
        costFunctionDialog.setRasterData(self.getRasterData())
        # load cost function when ok button is clicked
        costFunctionDialog.accepted.connect(lambda: self.setCostFunction(costFunctionDialog.costFunction(), index))
        costFunctionDialog.exec()

    def _disableButton(self):
        """
        Disables the button and enables it after 1 seconds
        :return:
        """
        self.dialog.create_graph_create_btn.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.dialog.create_graph_create_btn.setEnabled(True))

    def _randomAreaChanged(self):
        area, userdata = self.getRandomArea()
        if userdata == "custom area":
            self.dialog.create_graph_randomarea_extent.setDisabled(False)
        else:
            self.dialog.create_graph_randomarea_extent.setDisabled(True)

    def hasInput(self):
        return self.dialog.create_graph_input.count() > 0

    def isInputLayer(self):
        """
        True: if input is layer
        False: if input is graph
        None: if no input available
        :return:
        """
        if self.hasInput():
            if self.dialog.create_graph_input.currentLayer():
                return True

            # assumed that only one additional item is inserted
            path = self.dialog.create_graph_input.additionalItems()[0]
            name, ext = os.path.splitext(os.path.basename(path))
            if ext != ".graphml":
                return True
            else:
                return False
        return None

    def getInputLayer(self):
        """
        Returns the input layer or none if no layer is given
        :return: Layer or None if no layer
        """
        if self.hasInput() and self.isInputLayer():
            layer = self.dialog.create_graph_input.currentLayer()
            if layer is not None:
                return layer

            # load layer from file path
            path = self.dialog.create_graph_input.additionalItems()[0]
            name, ext = os.path.splitext(os.path.basename(path))
            if ext != ".graphml":
                return QgsVectorLayer(path, name, "ogr")
        return None

    def getInputGraph(self):
        """
        Returns input graph
        :return: ExtGraph or None
        """
        # assumed that only one additional item is inserted
        if self.hasInput() and not self.isInputLayer():
            path = self.dialog.create_graph_input.additionalItems()[0]
            name, ext = os.path.splitext(os.path.basename(path))
            if ext == ".graphml":
                graph = ExtGraph()
                graph.readGraphML(path)
                return graph
        return None

    def isRandom(self):
        return self.dialog.random_graph_checkbox.isChecked()

    def getSavePath(self):
        return self.dialog.create_graph_dest_output.filePath()

    # advanced parameters

    def getRandomVerticesNumber(self):
        return self.dialog.create_graph_randomNumber_input.value()

    def addRandomArea(self, area, userData=None):
        self.dialog.create_graph_randomarea_input.addItem(area, userData)

    def getRandomArea(self):
        return self.dialog.create_graph_randomarea_input.currentText(), self.dialog.create_graph_randomarea_input.currentData()

    def getRandomUserArea(self):
        """
        Return user defined area.
        :return: tuple (extent, crs) of (QgsRectangle, QgsCoordinateReferenceSystem)
        """
        if self.dialog.create_graph_randomarea_extent.isValid():
            # if extent is set by user
            return self.dialog.create_graph_randomarea_extent.outputExtent(), self.dialog.create_graph_randomarea_extent.outputCrs()
        else:
            # return map extent if no extent is selected
            return iface.mapCanvas().extent(), iface.mapCanvas().mapSettings().destinationCrs()

    def addConnectionType(self, type, userData=None):
        self.dialog.create_graph_connectiontype_input.addItem(type, userData)

    def getConnectionType(self):
        return self.dialog.create_graph_connectiontype_input.currentText(), self.dialog.create_graph_connectiontype_input.currentData()

    def getNeighborNumber(self):
        return self.dialog.create_graph_numberneighbor_input.value()

    def isDoubleEdgesAllowed(self):
        return self.dialog.create_graph_allowdoubleedges_checkbox.isChecked()

    def getDistance(self):
        """
        Gets the user entered distance and selected distance unit
        :return: (distance, QgsUnitTypes::DistanceUnit)
        """
        return self.dialog.create_graph_distance_input.value(), self.dialog.create_graph_distance_unit_input.currentData()

    def getClusterNumber(self):
        return self.dialog.create_graph_clusternumber_input.value()

    def addEdgeDirection(self, direction, userData=None):
        self.dialog.create_graph_edgedirection_input.addItem(direction, userData)

    def getEdgeDirection(self):
        return self.dialog.create_graph_edgedirection_input.currentText(), self.dialog.create_graph_edgedirection_input.currentData()

    def addDistanceStrategy(self, distance, userData=None):
        self.dialog.create_graph_distancestrategy_input.addItem(distance, userData)

    def getDistanceStrategy(self):
        return self.dialog.create_graph_distancestrategy_input.currentText(), self.dialog.create_graph_distancestrategy_input.currentData()

    def getRasterData(self):
        """
        Collects all not empty user selected raster layer and corresponding bands
        :return: Array of raster inputs and each input is a tuple: (layer, band)
        """
        rasterData = []
        for i in range(self.dialog.create_graph_rasterdata_widget.layout().count()):
            inputLayout = self.dialog.create_graph_rasterdata_widget.layout().itemAt(i)
            rasterLayer = inputLayout.itemAt(0).widget().currentLayer()
            rasterBand = inputLayout.itemAt(1).widget().currentBand()
            if rasterLayer is not None:
                rasterData.append((rasterLayer, rasterBand))
        return rasterData

    def getPolygonCostLayer(self):
        return self.dialog.create_graph_polycost_input.currentLayer()

    def getForbiddenAreaLayer(self):
        return self.dialog.create_graph_forbiddenarea_input.currentLayer()

    def getAdditionalPointLayer(self):
        return self.dialog.create_graph_additionalpoint_input.currentLayer()

    def getCostFunctions(self):
        """
        Collects all non-empty user defined cost functions
        :return: Array of cost functions
        """
        costFunctions = []
        for i in range(self.dialog.create_graph_costfunction_widget.layout().count()):
            costFunction = self.getCostFunction(i)
            if costFunction is not None:
                costFunctions.append(costFunction)
        return costFunctions

    def getCostFunction(self, index):
        """
        Gets cost function at given index
        :param index:
        :return:
        """
        costLineEdit = self.dialog.create_graph_costfunction_widget.layout().itemAt(index).itemAt(0).widget()
        return costLineEdit.text()

    def setCostFunction(self, costFunction, index):
        """
        Sets cost function at given index
        :param costFunction:
        :param index:
        :return:
        """
        costLineEdit = self.dialog.create_graph_costfunction_widget.layout().itemAt(index).itemAt(0).widget()
        costLineEdit.setText(costFunction)

    def getCRS(self):
        return self.dialog.create_graph_crs_input.crs()

    def isRenderGraphChecked(self):
        return self.dialog.create_graph_render_graph_checkbox.isChecked()

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