#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz
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
    """ Controller for loading of sample data sets """

    def __init__(self, view):
        """
        Constructor
        :type view: ResourceView
        """
        super().__init__(view)

        # add vector resources to view
        self.view.addResource(self.tr("airports"), ("airports", "vector"))
        self.view.addResource(self.tr("berlin streets"), ("berlin streets", "vector"))
        self.view.addResource(self.tr("brandenburg nature reserves"), ("brandenburg nature reserves", "vector"))
        self.view.addResource(self.tr("brandenburg water conservation areas"),
                             ("brandenburg water conservation areas", "vector"))
        self.view.addResource(self.tr("berlin environmental zone"), ("berlin environmental zone", "vector"))

        # add raster resources to view
        self.view.addResource(self.tr("berlin elevation"), ("berlin elevation", "raster"))

        # initialize resource
        self.changeResource()

    def changeResource(self):
        """ Changes the information to the selected resource """
        resource, resourceType = self.view.getResource()[1]
        # set filter
        if resourceType == "vector":
            self.view.setVectorFilter()
        elif resourceType == "raster":
            self.view.setRasterFilter()

        # set description
        self.view.setDescriptionSource(helper.getDatasetDescriptionPath(resource))

    def createData(self):
        """ Loads the selected data and stores it to the destination path if specified """
        LayerName = self.view.getResource()[0]
        resource, resourceType = self.view.getResource()[1]
        path = self.view.getFilePath()
        extension = os.path.splitext(path)[1]

        if path and not extension:
            self.view.showError(self.tr("No file format is specified!"))
            return

        if resourceType == "vector":
            resourceLayer = QgsVectorLayer(helper.getDatasetPath(resource, ".shp"), resource, "ogr")
            if resourceLayer.isValid():
                createdLayer = helper.saveLayer(resourceLayer, LayerName, "vector", path, extension)
                if createdLayer:
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.view.showError(self.tr("Layer or file format is invalid!"))
            else:
                self.view.showError(self.tr("Layer is invalid!"))
        elif resourceType == "raster":
            resourceLayer = QgsRasterLayer(helper.getDatasetPath(resource, ".tif"), resource)
            if resourceLayer.isValid():
                createdLayer = helper.saveLayer(resourceLayer, LayerName, "raster", path, extension)
                if createdLayer:
                    QgsProject.instance().addMapLayer(createdLayer)
                else:
                    self.view.showError(self.tr("Layer or file format is invalid!"))
            else:
                self.view.showError(self.tr("Layer is invalid!"))


