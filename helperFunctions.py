""" Basic helper functions """

from qgis.PyQt.QtCore import QCoreApplication

from os.path import abspath, join, dirname, splitext, basename

from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsWkbTypes, QgsProcessingUtils, QgsRasterPipe,QgsRasterFileWriter, QgsRasterLayer,  QgsProcessingParameterVectorDestination


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

