from .baseContentView import BaseContentView
from ..controllers.graph import CreateGraphController

from qgis.core import QgsMapLayerProxyModel


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"
        self.controller = CreateGraphController(self)

        # set up layer inputs
        self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer)
        # self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer | QgsMapLayerProxyModel.RasterLayer | QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.create_graph_poi_input.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dialog.create_graph_raster_input.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dialog.create_graph_polygon_input.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        # set null layer as default
        self.dialog.create_graph_poi_input.setCurrentIndex(0)
        self.dialog.create_graph_raster_input.setCurrentIndex(0)
        self.dialog.create_graph_polygon_input.setCurrentIndex(0)

        # show layer fields
        self.dialog.create_graph_cost_input.setLayer(self.getInputLayer())
        self.dialog.create_graph_input.layerChanged.connect(self.dialog.create_graph_cost_input.setLayer)

        # set up file upload
        self.dialog.create_graph_input_tools.clicked.connect(
            lambda: self._browseFile("create_graph_input", "Shape files (*.shp);;GraphML (*.graphml )")
        )

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

        self.dialog.create_graph_create_btn.clicked.connect(self.controller.createGraph)


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