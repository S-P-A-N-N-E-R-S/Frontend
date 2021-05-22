from .baseContentView import BaseContentView
from ..controllers.graph import CreateGraphController

from qgis.core import QgsMapLayerProxyModel


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"
        self.controller = CreateGraphController(self)

        # set up layer inputs
        self.dialog.create_graph_input.setFilters(QgsMapLayerProxyModel.PointLayer | QgsMapLayerProxyModel.LineLayer | QgsMapLayerProxyModel.RasterLayer)
        self.dialog.create_graph_poi_input.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dialog.create_graph_raster_input.setFilters(QgsMapLayerProxyModel.RasterLayer)

        # show layer fields
        self.dialog.create_graph_cost_input.setLayer(self.getLayer())
        self.dialog.create_graph_input.layerChanged.connect(self.dialog.create_graph_cost_input.setLayer)

        self.dialog.create_graph_create_btn.clicked.connect(self.controller.createGraph)

    def getLayer(self):
        return self.dialog.create_graph_input.currentLayer()

    def isRandom(self):
        return self.dialog.random_graph_checkbox.isChecked()

    def getSavePath(self):
        return self.dialog.create_graph_dest_output.filePath()

    # advanced parameters

    def addDistance(self, distance, userData=None):
        self.dialog.create_graph_distance_input.addItem(distance, userData)

    def getDistance(self):
        return self.dialog.create_graph_distance_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def getCostField(self):
        return self.dialog.create_graph_cost_input.currentField()

    def getPOILayer(self):
        return self.dialog.create_graph_poi_input.currentLayer()

    def getRasterLayer(self):
        return self.dialog.create_graph_raster_input.currentLayer()

    def addRasterType(self, type, userData=None):
        self.dialog.create_graph_rastertype_input.addItem(type, userData)

    def getRasterType(self):
        return self.dialog.create_graph_rastertype_input.currentText(), self.dialog.create_graph_rastertype_input.currentData()

