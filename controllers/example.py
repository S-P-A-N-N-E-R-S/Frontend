import os

from .base import BaseController
from .. import helperFunctions as helper

from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject, QgsVectorFileWriter, QgsRasterPipe, QgsRasterFileWriter, QgsWkbTypes, QgsProcessingUtils


class ExampleController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: ExampleDataView
        """
        super().__init__(view)

        # add vector examples to view
        self.view.addExample("airports", "vector")
        self.view.addExample("berlin streets", "vector")
        self.view.addExample("brandenburg naturschutzgebiete", "vector")
        self.view.addExample("brandenburg wasserschutzgebiete", "vector")
        self.view.addExample("berlin umweltzone", "vector")

        # add raster examples to view
        self.view.addExample("berlin elevation", "raster")

        # vector example first
        self.view.setVectorFilter()

    def changeFilter(self):
        _, type = self.view.getExample()
        if type == "vector":
            self.view.setVectorFilter()
        elif type == "raster":
            self.view.setRasterFilter()

    def createData(self):
        example, type = self.view.getExample()
        path = self.view.getFilePath()
        extension =  os.path.splitext(path)[1] if path else "tif"

        if type == "vector":
            exampleLayer = QgsVectorLayer(helper.getExamplePath("{}.shp".format(example)), example, "ogr")
            if exampleLayer.isValid():
                createdLayer = helper.saveLayer(exampleLayer, example, "vector", path, extension)
                if createdLayer:
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.view.showError("Layer is invalid!")
            else:
                self.view.showError("Layer is invalid!")
        elif type == "raster":
            exampleLayer = QgsRasterLayer(helper.getExamplePath("{}.tif".format(example)), example)
            if exampleLayer.isValid():
                createdLayer = helper.saveLayer(exampleLayer, example, "raster", path, extension)
                if createdLayer:
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.view.showError("Layer is invalid!")
            else:
                self.view.showError("Layer is invalid!")


