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
        self.iface = iface

    def initGui(self):
        self.action = QAction(QIcon(getImagePath("icon.png")), "Proto Plugin", self.iface.mainWindow())
        self.action.triggered.connect(self.openDialog)
        self.action.setWhatsThis("Select VectorLayer and click green Button")
        self.action.setStatusTip("Select VectorLayer and click green Button")

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Proto Plugin", self.action)

    def openDialog(self):
        dialog = ProtoPluginDialog()
        dialog.exec_()

    def unload(self):
        self.iface.removePluginMenu("&Proto Plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

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