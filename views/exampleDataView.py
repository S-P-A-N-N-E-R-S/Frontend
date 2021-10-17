#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz
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

from .baseContentView import BaseContentView
from ..controllers.example import ExampleController
from ..helperFunctions import getRasterFileFilter, getVectorFileFilter

from qgis.gui import QgsFileWidget


class ExampleDataView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "example data"
        self.controller = ExampleController(self)

        # set up file upload widget
        self.dialog.example_data_output.setStorageMode(QgsFileWidget.SaveFile)
        self.dialog.example_data_output.lineEdit().setPlaceholderText("[Save to temporary layer]")

        # change example data
        self.dialog.example_data_input.currentIndexChanged.connect(self.controller.changeFilter)

        # create button
        self.dialog.create_example_data_btn.clicked.connect(self.controller.createData)

    def getExample(self):
        return self.dialog.example_data_input.currentText(), self.dialog.example_data_input.currentData()

    def addExample(self, name, userData=None):
        self.dialog.example_data_input.addItem(name, userData)

    # destination output

    def setFilter(self, filter):
        self.dialog.example_data_output.setFilter(filter)

    def setVectorFilter(self):
        self.setFilter(getVectorFileFilter())

    def setRasterFilter(self):
        self.setFilter(getRasterFileFilter())

    def getFilePath(self):
        return self.dialog.example_data_output.filePath()
