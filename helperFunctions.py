""" Basic helper functions """

from qgis.PyQt.QtCore import QCoreApplication

from os.path import abspath, join, dirname, splitext, basename

from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsWkbTypes, QgsProcessingUtils, QgsRasterPipe, QgsRasterFileWriter, QgsRasterLayer


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


def getExamplePath(example):
    """ Get the example path """
    path = join(getPluginPath(), "resources/examples")
    return abspath(join(path, example))


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
    :return:
    """
    if layer.isValid():
        if type == "vector":
                if path:
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
