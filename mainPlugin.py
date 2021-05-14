from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import QVariant

from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

from . import resources

import time

from .ui.protoPluginDialog import ProtoPluginDialog
from .helperFunctions import getImagePath, getPluginPath


class ProtoPlugin:

    def __init__(self, iface):
        """
        Constructor
        :type iface: QgisInterface
        """
        self.iface = iface
        self.initActions()

    def initActions(self):
        self.exampleAction = QAction("Create example data", self.iface.mainWindow())
        self.exampleAction.triggered.connect(lambda: self.openView(ProtoPluginDialog.Views.ExampleDataView))
        self.exampleAction.setWhatsThis("Create example data")
        self.exampleAction.setStatusTip("Create example data")

        self.graphAction = QAction("Create graph", self.iface.mainWindow())
        self.graphAction.triggered.connect(lambda: self.openView(ProtoPluginDialog.Views.CreateGraphView))
        self.graphAction.setWhatsThis("Create graph")
        self.graphAction.setStatusTip("Create graph")

        self.ogdfAnalysisAction = QAction("OGDF analysis", self.iface.mainWindow())
        self.ogdfAnalysisAction.triggered.connect(lambda: self.openView(ProtoPluginDialog.Views.OGDFAnalysisView))
        self.ogdfAnalysisAction.setWhatsThis("OGDF analysis")
        self.ogdfAnalysisAction.setStatusTip("OGDF analysis")

        self.ogdfJobsAction = QAction("OGDF jobs", self.iface.mainWindow())
        self.ogdfJobsAction.triggered.connect(lambda: self.openView(ProtoPluginDialog.Views.JobsView))
        self.ogdfJobsAction.setWhatsThis("OGDF jobs")
        self.ogdfJobsAction.setStatusTip("OGDF jobs")

        self.optionsAction = QAction("Options", self.iface.mainWindow())
        self.optionsAction.triggered.connect(lambda: self.openView(ProtoPluginDialog.Views.OptionsView))
        self.optionsAction.setWhatsThis("Options")
        self.optionsAction.setStatusTip("Options")

        self.defaultAction = QAction(QIcon(getImagePath("icon.png")), "Create example data", self.iface.mainWindow())
        self.defaultAction.triggered.connect(lambda: self.openView(ProtoPluginDialog.Views.ExampleDataView))
        self.defaultAction.setWhatsThis("Create example data")
        self.defaultAction.setStatusTip("Create example data")

    def initGui(self):
        # create menu
        menu = QMenu("Proto Plugin")
        menu.setIcon(QIcon(getImagePath("icon.png")))
        menu.addAction(self.exampleAction)
        menu.addAction(self.graphAction)
        menu.addAction(self.ogdfAnalysisAction)
        menu.addAction(self.ogdfJobsAction)
        menu.addAction(self.optionsAction)
        self.menuAction = menu.menuAction()

        # create toolbar entry
        self.toolBarButton = QToolButton()
        self.toolBarButton.setMenu(menu)
        self.toolBarButton.setDefaultAction(self.defaultAction)
        self.toolBarButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolBarAction = self.iface.addToolBarWidget(self.toolBarButton)

        # create menu entry
        plugin_menu = self.iface.pluginMenu()
        plugin_menu.addMenu(menu)

    def openView(self, view):
        dialog = ProtoPluginDialog()
        dialog.setView(view)
        dialog.exec()

    def unload(self):
        # remove toolbar entry
        self.iface.removeToolBarIcon(self.toolBarAction)

        # remove menu entry
        plugin_menu = self.iface.pluginMenu()
        plugin_menu.removeAction(self.menuAction)

    def run(self):
        print("ProtoPlugin: Run Called!")
        self.createGraph()

    def createGraph(self):
        layer = self.iface.activeLayer()

        # check if layer type is vectorLayer
        vector = True
        if layer and layer.type() != QgsMapLayer.VectorLayer:
            vector = False
            print("No VectorLayer found.")
        
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

            # create new VectorLayer to show graph
            newVectorLayer = QgsVectorLayer("LineString", "LinesFromGraph", "memory")
            newDataProvider = newVectorLayer.dataProvider()

            # add Fields to VectorLayer
            newDataProvider.addAttributes([QgsField("edgeNr", QVariant.Int), QgsField("type", QVariant.String)])
            newVectorLayer.updateFields()

            # add Feature for every edge in graph based on its points
            for edgeId in range(graph.edgeCount()):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(graph.vertex(graph.edge(edgeId).fromVertex()).point()),
                                                            QgsPoint(graph.vertex(graph.edge(edgeId).toVertex()).point())]))
                feat.setAttributes([edgeId, "EdgeFromGraph"])
                newDataProvider.addFeature(feat)
            
            newVectorLayer.updateExtents()
            QgsProject.instance().addMapLayer(newVectorLayer)

            print("Done: ", graph.edgeCount(), " edges added.")
        
        # if layer consists only of points, a QgsGraph has to be filled with those points
        elif points:
            graph = QgsGraph()

            # get points from features of layer
            for feat in layer.getFeatures():
                geom = feat.geometry()
                graph.addVertex(geom.asPoint())


            # create new VectorLayer to show graph
            # TODO: add function to create VectorLayer (used for points and lines) to minimize double code
            newVectorLayer = QgsVectorLayer("Point", "PointsFromGraph", "memory")
            newDataProvider = newVectorLayer.dataProvider()

            # add Fields to VectorLayer
            newDataProvider.addAttributes([QgsField("vertexNr", QVariant.Int), QgsField("type", QVariant.String)])
            newVectorLayer.updateFields()

            # add Feature for every vertex in graph
            for vertexId in range(graph.vertexCount()):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(graph.vertex(vertexId).point()))
                feat.setAttributes([vertexId, "VertexFromGraph"])
                newDataProvider.addFeature(feat)

            newVectorLayer.updateExtents()
            QgsProject.instance().addMapLayer(newVectorLayer)

            print("Done: ", graph.vertexCount(), " vertices added")