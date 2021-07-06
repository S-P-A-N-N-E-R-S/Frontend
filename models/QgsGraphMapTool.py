from qgis.core import *
from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QPoint

class QgsGraphMapTool(QgsMapTool):
    """QgsGraphMapTool should enable the user to edit a QgsGraphLayer

    Args:
        QgsMapTool ([type]): [description]
    """

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.mCanvas = canvas

        self.mLayer = layer

    def canvasPressEvent(self, event):
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        converter = QgsVertexMarker(iface.mapCanvas())
        clickPosition = converter.toMapCoordinates(clickPosition)

        print("OldFeatureCount: ", self.mLayer.dataProvider().featureCount(), self.mLayer.mGraph.vertexCount())

        # add feature and vertex
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(clickPosition))

        feat.setAttributes([self.mLayer.mGraph.vertexCount(), clickPosition.x(), clickPosition.y()])
        self.mLayer.dataProvider().addFeature(feat)

        self.mLayer.mGraph.addVertex(clickPosition)

        print("NewFeatureCount: ", self.mLayer.dataProvider().featureCount(), self.mLayer.mGraph.vertexCount())

        self.mLayer.triggerRepaint()
        self.mCanvas.refresh()

    def isEditTool(self):
        return True