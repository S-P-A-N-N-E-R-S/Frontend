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

from .baseView import BaseView
from ..controllers.resource import ResourceController
from ..helperFunctions import getRasterFileFilter, getVectorFileFilter

from qgis.gui import QgsFileWidget

from qgis.PyQt.QtCore import QUrl


class ResourceView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "resource data"
        self.controller = ResourceController(self)

        # set up file upload widget
        self.dialog.create_from_resource_output.setStorageMode(QgsFileWidget.SaveFile)
        self.dialog.create_from_resource_output.lineEdit().setPlaceholderText("[Save to temporary layer]")

        # change resource data
        self.dialog.create_from_resource_input.currentIndexChanged.connect(self.controller.changeResource)

        # create button
        self.dialog.create_from_resource_btn.clicked.connect(self.controller.createData)

    def getResource(self):
        return self.dialog.create_from_resource_input.currentText(), self.dialog.create_from_resource_input.currentData()

    def addResource(self, name, userData=None):
        self.dialog.create_from_resource_input.addItem(name, userData)

    def setDescriptionSource(self, source):
        if source is None:
            self.dialog.create_from_resource_description_textbrowser.setPlainText(self.tr("No description available"))
        else:
            self.dialog.create_from_resource_description_textbrowser.setSource(QUrl(source))

    # destination output

    def setFilter(self, filter):
        self.dialog.create_from_resource_output.setFilter(filter)

    def setVectorFilter(self):
        self.setFilter(getVectorFileFilter())

    def setRasterFilter(self):
        self.setFilter(getRasterFileFilter())

    def getFilePath(self):
        return self.dialog.create_from_resource_output.filePath()
