from .baseContentView import BaseContentView
from .. import helperFunctions as helper

from qgis.gui import QgsFileWidget
from qgis.core import QgsVectorLayer, QgsProject, QgsVectorFileWriter, QgsWkbTypes

import os

class ExampleDataView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "example data"

    def setupWindow(self):
        # fill example data input
        # todo add more example data
        self.dialog.example_data_input.addItem("airports")
        # self.dialog.example_data_input.addItem("streets")

        # set up file upload widget
        self.dialog.example_data_output.setFilter("Shape File (*.shp)")
        self.dialog.example_data_output.setStorageMode(QgsFileWidget.SaveFile)

        # Create button
        self.dialog.create_example_data_btn.clicked.connect(self.createData)

    def createData(self):
        example = self.dialog.example_data_input.currentText()
        path = self.dialog.example_data_output.filePath()

        exampleLayer = QgsVectorLayer(helper.getExamplePath("{}.shp".format(example)), example, "ogr")
        if exampleLayer.isValid():
            if path:
                # copy layer to path
                QgsVectorFileWriter.writeAsVectorFormat(exampleLayer, path, "UTF-8", exampleLayer.crs(), "ESRI Shapefile")
                # load created layer
                createdLayer = QgsVectorLayer(path, os.path.splitext(os.path.basename(path))[0], "ogr")
                if createdLayer.isValid():
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.showError("Layer is invalid!")
            else:
                # create scratch layer
                wkbType= QgsWkbTypes.displayString(exampleLayer.wkbType())
                tmpLayer = QgsVectorLayer(wkbType, example, "memory")
                tmpLayer.setCrs(exampleLayer.crs())
                tmpLayerData = tmpLayer.dataProvider()
                tmpLayerData.addAttributes(exampleLayer.fields())
                tmpLayer.updateFields()
                tmpLayerData.addFeatures(exampleLayer.getFeatures())
                if tmpLayer.isValid():
                    QgsProject.instance().addMapLayer(tmpLayer)
                else:
                    self.showError("Layer is invalid!")
