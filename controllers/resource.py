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

import os

from .base import BaseController
from .. import helperFunctions as helper

from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject, QgsVectorFileWriter, QgsRasterPipe, QgsRasterFileWriter, QgsWkbTypes, QgsProcessingUtils


class ResourceController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: ResourceView
        """
        super().__init__(view)

        # add vector examples to view
        self.view.addExample(self.tr("airports"), ("airports", "vector"))
        self.view.addExample(self.tr("berlin streets"), ("berlin streets", "vector"))
        self.view.addExample(self.tr("brandenburg nature reserves"), ("brandenburg nature reserves", "vector"))
        self.view.addExample(self.tr("brandenburg water conservation areas"),
                             ("brandenburg water conservation areas", "vector"))
        self.view.addExample(self.tr("berlin environmental zone"), ("berlin environmental zone", "vector"))

        # add raster examples to view
        self.view.addExample(self.tr("berlin elevation"), ("berlin elevation", "raster"))

        # vector example first
        self.view.setVectorFilter()

    def changeFilter(self):
        _, type = self.view.getExample()[1]
        if type == "vector":
            self.view.setVectorFilter()
        elif type == "raster":
            self.view.setRasterFilter()

    def createData(self):
        LayerName = self.view.getExample()[0]
        example, type = self.view.getExample()[1]
        path = self.view.getFilePath()
        extension = os.path.splitext(path)[1]

        if path and not extension:
            self.view.showError(self.tr("No file format is specified!"))
            return

        if type == "vector":
            exampleLayer = QgsVectorLayer(helper.getExamplePath("{}.shp".format(example)), example, "ogr")
            if exampleLayer.isValid():
                createdLayer = helper.saveLayer(exampleLayer, LayerName, "vector", path, extension)
                if createdLayer:
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.view.showError(self.tr("Layer or file format is invalid!"))
            else:
                self.view.showError(self.tr("Layer is invalid!"))
        elif type == "raster":
            exampleLayer = QgsRasterLayer(helper.getExamplePath("{}.tif".format(example)), example)
            if exampleLayer.isValid():
                createdLayer = helper.saveLayer(exampleLayer, LayerName, "raster", path, extension)
                if createdLayer:
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.view.showError(self.tr("Layer or file format is invalid!"))
            else:
                self.view.showError(self.tr("Layer is invalid!"))


