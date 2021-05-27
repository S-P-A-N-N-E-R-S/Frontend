from .baseContentView import BaseContentView
from ..controllers.graph import CreateGraphController

from qgis.core import QgsMapLayerProxyModel

from PyQt5.QtWidgets import QFileDialog, QAction


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"
        self.controller = CreateGraphController(self)

        # set up layer inputs
        self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer | QgsMapLayerProxyModel.RasterLayer | QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.create_graph_poi_input.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dialog.create_graph_raster_input.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dialog.create_graph_polygon_input.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        # show layer fields
        self.dialog.create_graph_cost_input.setLayer(self.getInputLayer())
        self.dialog.create_graph_input.layerChanged.connect(self.dialog.create_graph_cost_input.setLayer)

        # set up file upload
        self.dialog.create_graph_input_tools.clicked.connect(
            lambda: self.__browseFile("create_graph_input", "GPKG files (*.gpkg);;Shape files (*.shp);;GraphML (*.graphml )")
        )

        self.dialog.create_graph_create_btn.clicked.connect(self.controller.createGraph)

    def __browseFile(self, layerComboBox, filter):
        """
        Allows to browse for a file and adds it to the QGSMapLayerComboBox
        :param layerComboBox: name of the QGSMapLayerComboBox
        :param filter: supported file types
        :return:
        """
        path, selectedFilter = QFileDialog.getOpenFileName(filter=filter)
        if path:
            comboBox = getattr(self.dialog, layerComboBox)
            comboBox.setAdditionalItems([path])
            comboBox.setCurrentIndex(self.dialog.create_graph_input.count()-1)

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
        if not self.isInputLayer():
            return self.dialog.create_graph_input.additionalItems()[0]
        return None

    def isRandom(self):
        return self.dialog.random_graph_checkbox.isChecked()

    def setSavePathFilter(self, filter):
        self.dialog.create_graph_dest_output.setFilter(filter)

    def getSavePath(self):
        return self.dialog.create_graph_dest_output.filePath()

    # advanced parameters

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

    # log

    def setLogText(self, text):
        self.dialog.create_graph_log.setPlainText(text)

    def insertLogText(self, text):
        self.dialog.create_graph_log.insertPlainText(text)

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