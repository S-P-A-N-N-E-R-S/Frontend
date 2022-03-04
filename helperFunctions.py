#  Basic helper functions
#
#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz, Timo Glane, Leon Nienhüser
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
from os.path import abspath, join, dirname, splitext, basename, isfile
import re
import configparser
from enum import Enum

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsWkbTypes, QgsProcessingUtils, QgsRasterPipe,QgsRasterFileWriter, QgsRasterLayer,  QgsSettings


class TlsOption(Enum):
    DISABLED = 1
    ENABLED_NO_CHECK = 2
    ENABLED = 3


def getHost():
    """ Get the server host address"""
    return QgsSettings().value("ogdfplugin/host", "localhost")


def getPort():
    """ Get the server port address"""
    return int(QgsSettings().value("ogdfplugin/port", 4711))


def getEncryptionOption():
    """ Get the use ssl value"""
    val = QgsSettings().value("ogdfplugin/ssl", True)
    if isinstance(val, bool):
        return val
    else:
        return val != "false"


def getEncryptionCertCheckOption():
    """ Get the ssl check certificates value"""
    if not getEncryptionOption():
        return False

    val = QgsSettings().value("ogdfplugin/sslCheck", True)
    if isinstance(val, bool):
        return val
    else:
        return val != "false"


def getTlsOption():
    """ Get the TlsOption depending on the encryption options """
    if getEncryptionCertCheckOption():
        return TlsOption.ENABLED
    elif getEncryptionOption():
        return TlsOption.ENABLED_NO_CHECK
    else:
        return TlsOption.DISABLED


def getUsername():
    """ Get the last saved username"""
    return QgsSettings().value("ogdfplugin/username", "")


def getAuthId():
    """ Get the authId"""
    return QgsSettings().value("ogdfplugin/authId")


def getPluginPath():
    """ Get the absolute path to plugin root folder"""
    return abspath(dirname(__file__))


def getResourcesPath(example):
    """ Get the example path """
    return join(getPluginPath(), "resources")


def getImagePath(image):
    """ Get the image path """
    path = join(getPluginPath(), "resources/images")
    return abspath(join(path, image))


def getDatasetPath(example, extension):
    """
    Get the example path
    :param example: example name
    :param extension: extension of file specifies format like .shp
    :return: path to example data
    """
    path = join(getPluginPath(), "resources/datasets/data/"+example)
    return abspath(join(path, example + extension))


def getDatasetDescriptionPath(example):
    """
    Get the path to the html example descriptions
    :param example:
    :return: Path to description if file exists
    """
    path = join(getPluginPath(), "resources/datasets/descriptions")
    absolutePath = abspath(join(path, example + ".html"))
    if isfile(absolutePath):
        return absolutePath
    return None


def getHelpUrl():
    """
    Get the URL to the homepage from metadata
    :return: URL
    """
    # save homepage as static variable to parse metadata once
    if not hasattr(getHelpUrl, "homepage"):
        config = configparser.ConfigParser()
        config.read(join(getPluginPath(), "metadata.txt"))
        getHelpUrl.homepage = config["general"]["homepage"]
    return getHelpUrl.homepage


def tr(message, context="@default"):
    """
    Get the translation for a string using Qt translation API.

    :param message: String for translation.
    :type message: str, QString
    :returns: Translated version of message.
    """
    return QCoreApplication.translate(context, message)


def saveLayer(layer, layerName, type, path=None, format=None):
    """
    Saves passed layer and returns created layer. Can used to copy a layer. Returns a new layer.
    :param layer: raster or vector layer
    :param path: file path or None. If none a temporary layer will be created.
    :param layerName: Name of the layer displayed in QGIS
    :param type: "vector" or "raster"
    :param format: not all tested and not for temporary vector layer available. In this case set None.
                    vector: 'gpkg', 'shp', '000', 'bna', 'csv', 'dgn', 'dxf', 'geojson', 'geojsonl', 'geojsons', 'gml', 'gpx', 'gxt', 'ili', 'itf', 'json', 'kml', 'ods', 'sql', 'sqlite', 'tab', 'txt', 'xlsx', 'xml', 'xtf'
                    raster: "tif", "gen", "bmp", "bt", "byn", "bil", "ers", "gpkg", "grd", "grd", "gtx", "img", "mpr", "lbl", "kro", "ter", "mbtiles", "hdr", "mrf", "ntf", "gsb", "grd", "pix", "map", "pdf", "xml", "pgm", "rsw", "grd", "rst", "sdat", "rgb", "ter", "vrt", "nc"
                   The default format for raster layer is tif.
    :return: created Layer. None if created layer is invalid.
    """
    if layer.isValid():
        if type == "vector":
            if path:
                if not format:
                    # use extension
                    format = splitext(path)[1]
                # copy layer to path
                QgsVectorFileWriter.writeAsVectorFormat(layer, path, "UTF-8", layer.crs(), QgsVectorFileWriter.driverForExtension(format))
                # load created layer
                createdLayer = QgsVectorLayer(path, splitext(basename(path))[0], "ogr")
                if createdLayer.isValid():
                    return createdLayer
            else:
                # create scratch layer by copy vector data
                wkbType = QgsWkbTypes.displayString(layer.wkbType())
                tmpLayer = QgsVectorLayer(wkbType, layerName, "memory")
                tmpLayer.setCrs(layer.crs())
                tmpLayerData = tmpLayer.dataProvider()
                tmpLayerData.addAttributes(layer.fields())
                tmpLayer.updateFields()
                tmpLayerData.addFeatures(layer.getFeatures())
                if tmpLayer.isValid():
                    return tmpLayer

        elif type == "raster":
            if not path:
                # create temporary path
                path = QgsProcessingUtils.generateTempFilename(layerName)
            if not format:
                # use tif
                format = "tif"
            # copy layer to path
            provider = layer.dataProvider()
            pipe = QgsRasterPipe()
            pipe.set(provider.clone())

            fileWriter = QgsRasterFileWriter(path)
            fileWriter.setOutputFormat(fileWriter.driverForExtension(format))
            fileWriter.writeRaster(pipe, provider.xSize(), provider.ySize(), provider.extent(), provider.crs())

            # load created layer
            createdLayer = QgsRasterLayer(path, splitext(basename(path))[0])
            if createdLayer.isValid():
                return createdLayer
    return None


def saveGraph(graph, graphLayer, graphName="", savePath=None, renderGraph=True):
    """
    Saves graph or created graph layers to destination and adds the created layers to project
    :param graph: ExtGraph
    :param graphLayer:
    :param graphName:
    :return: successful or not
    """
    success = True
    errorMsg = ""
    if savePath:
        fileName, extension = splitext(savePath)
        if extension == ".graphml":
            graph.writeGraphML(savePath)
        else:
            # if layer path as .shp
            # create vector layer from graph layer
            [vectorPointLayer, vectorLineLayer] = graphLayer.createVectorLayer()

            # adjust path to point or lines
            savePath = savePath[:-len(extension)]
            savePathPoints = savePath
            savePathLines = savePath

            savePathPoints += "Points" + extension
            savePathLines += "Lines" + extension

            # save vector layers to path
            vectorPointLayer = saveLayer(vectorPointLayer, vectorPointLayer.name(), "vector", savePathPoints, extension)
            vectorLineLayer = saveLayer(vectorLineLayer, vectorLineLayer.name(), "vector", savePathLines, extension)

            # add vector layers to project
            if vectorPointLayer:
                QgsProject.instance().addMapLayer(vectorPointLayer)
            else:
                errorMsg = tr("Created point layer can not be loaded due to invalidity!")
                success = False

            if vectorLineLayer:
                QgsProject.instance().addMapLayer(vectorLineLayer)
            else:
                errorMsg = tr("Created line layer can not be loaded due to invalidity!")
                success = False

    # add graph layer to project
    graphLayer.setName(graphName + "GraphLayer")
    if graphLayer.isValid():
        QgsProject.instance().addMapLayer(graphLayer)

        # disable graph rendering if checkbox is not checked
        if not renderGraph:
            QgsProject.instance().layerTreeRoot().findLayer(graphLayer).setItemVisibilityChecked(False)
    else:
        errorMsg = tr("Created graph layer can not be loaded due to invalidity!")
        success = False
    return success, errorMsg


def getVectorFileFilter():
    """
    Returns all Vector File Filters, e.g.
    "GeoPackage (*.gpkg *.GPKG);;ESRI Shapefile (*.shp *.SHP);;..."
    :return:
    """
    return QgsVectorFileWriter.fileFilterString()


def getRasterFileFilter():
    """
    Resturn all Raster File Filters, e.g.
    "GeoTIFF (*.tif *.TIF *.tiff *.TIFF);;ARC Digitized Raster Graphics (*.gen *.GEN);;..."
    :return:
    """
    filters = []
    for filterAndFormat in QgsRasterFileWriter.supportedFiltersAndFormats():
        filters.append(filterAndFormat.filterString)
    return ";;".join(filters)


def hasAStarC():
    """
    Checks if performant A* c++ implementation is available
    :return: true if cpp library available
    """
    pattern = re.compile("AStarC")
    dir = join(getPluginPath(), "lib")
    for filepath in os.listdir(dir):
        if pattern.search(filepath):
            return True
    return False
