from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtXml import *

from qgis.core import *
from qgis.gui import *
from qgis.analysis import *


from .qgsgraphlayer import QgsGraphLayer, QgsGraphLayerType, QgsGraphDataProvider

class ProtoPlugin:

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction(QIcon(":/plugins/ProtoPlugin/icon.png"), "Proto Plugin", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.action.setWhatsThis("Select VectorLayer and click green Button")
        self.action.setStatusTip("Select VectorLayer and click green Button")

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Proto Plugin", self.action)

        QgsApplication.pluginLayerRegistry().addPluginLayerType(QgsGraphLayerType())

        QgsProviderRegistry.instance().registerProvider(QgsProviderMetadata(QgsGraphDataProvider.providerKey(),
                                                                            QgsGraphDataProvider.description(),
                                                                            QgsGraphDataProvider.createProvider()))

        # re-read and therefore reload plugin layers after adding QgsGraphLayerType to PluginLayerRegistry
        self.reloadPluginLayers()

    def unload(self):
        self.iface.removePluginMenu("&Proto Plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

        QgsApplication.pluginLayerRegistry().removePluginLayerType(QgsGraphLayer.LAYER_TYPE)


    def run(self):
        print("ProtoPlugin: Run Called!")
        self.createGraph()

    def reloadPluginLayers(self):
        """Re-reads and reloads plugin layers
        """
        # read project file as QDomDocument
        with open(QgsProject.instance().absoluteFilePath(), 'r') as projectFile:
            projectDocument = QDomDocument()
            projectDocument.setContent(projectFile.read())

            # for every maplayer node in project file
            mapLayerNodeList = projectDocument.elementsByTagName("maplayer")
            for mapLayerNodeId in range(mapLayerNodeList.count()):
                mapLayerNode = mapLayerNodeList.at(mapLayerNodeId)

                # check if maplayer is a plugin layer
                mapLayerElem = mapLayerNode.toElement()
                if mapLayerElem.attribute("type") == "plugin":
                    # re-read plugin layer from node
                    QgsProject.instance().readLayer(mapLayerNode)

        # readLayer() adds a new layer but does not remove not correctly loaded layer
        # TODO: find a way to remove those layers -> following mapLayers() doesnt return those layers
        # for remLayer in QgsProject.instance().mapLayers():
        #     if remLayer.type() == None:
        #         QgsProject.instance().removeMapLayer(remLayer)

    def addLayer(self, layerType):
        layer = QgsGraphLayer()
        layer.setLayerType(layerType)

        if layer.isValid():
            # coordRefSys = layerType.coordRefSys(self.iface.mapCanvas().mapSettings().destinationCrs())
            QgsProject.instance().addMapLayer(layer)


        return layer


    def createGraph(self):
        layer = self.iface.activeLayer()
        
        # check layerType of layer (vector or graph else raster)
        vector = False
        graphLoaded = False
        if layer and layer.type() == QgsMapLayer.VectorLayer:
            vector = True
            print("VectorLayer found.")

        elif isinstance(layer, QgsGraphLayer):
            print("GraphLayer found")
            graphLoaded = True

        else:
            print("No Vector-/GraphLayer found", layer)

        # check features (only one representative)
        points = False
        lines = False
        if vector:
            for feat in layer.getFeatures():
                geom = feat.geometry()
            
                # check for geometry, assume no mixture of e.g. lines and points
                points = False
                lines = False
                if geom.type() == QgsWkbTypes.PointGeometry:
                    points = True
                    print("Points Found.")
                elif geom.type() == QgsWkbTypes.LineGeometry:
                    lines = True
                    print("Lines Found.")
                else:
                    # no points or lines in vectorLayer found
                    print("No Points or Lines found. Error!")

                break

        # if layer consists only of lines, GraphBuilder can be applied
        if lines:
            director = QgsVectorLayerDirector(layer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)
            director.addStrategy(QgsNetworkDistanceStrategy())

            graphBuilder = QgsGraphBuilder(layer.crs())
            director.makeGraph(graphBuilder, [])
            graph = graphBuilder.graph()

            # create new graphLayer to show graph
            newGraphLayer = QgsGraphLayer()
            newGraphLayer.setCrs(layer.crs())
            newGraphLayer.setGraph(graph)

            QgsProject.instance().addMapLayer(newGraphLayer)

            print("Done: ", graph.edgeCount(), " edges added.")
        
        # if layer consists only of points, a QgsGraph has to be filled with those points
        # if layer is GraphLayer, a QgsGraph can be retrieved from layer directly
        elif points or graphLoaded:
            
            if not graphLoaded:                
                graph = QgsGraph()

                # get points from features of layer
                for feat in layer.getFeatures():
                    geom = feat.geometry()
                    addedPoint = geom.asPoint()
                    graph.addVertex(addedPoint)
            else:
                print("Get existing graph from graphLayer")
                graph = layer.getGraph()

            # create graphLayer to show graph
            newGraphLayer = self.addLayer(QgsGraphLayer.LAYER_TYPE)
            newGraphLayer.setCrs(layer.crs())
            newGraphLayer.setGraph(graph)

            print(newGraphLayer.dataProvider().dataSourceUri())

            newGraphLayer.exportToShapefile()

            print("Done: ", graph.vertexCount(), " vertices added")
