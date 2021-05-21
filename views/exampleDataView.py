from .baseContentView import BaseContentView
from ..controllers.example import ExampleController

from qgis.gui import QgsFileWidget


class ExampleDataView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "example data"
        self.controller = ExampleController(self)

    def setupWindow(self):
        # set up file upload widget
        self.dialog.example_data_output.setStorageMode(QgsFileWidget.SaveFile)

        # change example data
        self.dialog.example_data_input.currentIndexChanged.connect(self.controller.changeFilter)

        # create button
        self.dialog.create_example_data_btn.clicked.connect(self.controller.createData)

    def setVectorFilter(self):
        self.setFilter("GPKG files (*.gpkg);;Shape files (*.shp)")

    def setRasterFilter(self):
        self.setFilter("TIF files (*.tif);;IMG files (*.img)")

    def setFilter(self, filter):
        self.dialog.example_data_output.setFilter(filter)

    def getExample(self):
        return self.dialog.example_data_input.currentText()

    def getData(self):
        return self.dialog.example_data_input.currentData()

    def addExample(self, name, userData=None):
        self.dialog.example_data_input.addItem(name, userData)

    def getFilePath(self):
        return self.dialog.example_data_output.filePath()
