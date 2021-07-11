from qgis.core import *
from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QPoint, Qt

class QgsGraphMapTool(QgsMapTool):
    """QgsGraphMapTool should enable the user to edit a QgsGraphLayer

    Args:
        QgsMapTool ([type]): [description]
    """

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.mCanvas = canvas

        self.mLayer = layer

        self.firstFound = False
        self.ctrlPressed = False

    def canvasPressEvent(self, event):
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        converter = QgsVertexMarker(iface.mapCanvas())
        clickPosition = converter.toMapCoordinates(clickPosition)
        clickPosition = self.mLayer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        if event.button() == Qt.LeftButton: # LeftClick

            # add feature and vertex
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(clickPosition))

            feat.setAttributes([self.mLayer.mGraph.vertexCount(), clickPosition.x(), clickPosition.y()])
            self.mLayer.dataProvider().addFeature(feat)

            self.mLayer.mGraph.addVertex(clickPosition)

        elif event.button() == Qt.RightButton: # RightClick

            # TODO: find a way to set a satisfying tolerance for the checkup
            vertexId = self.mLayer.mGraph.findVertex(clickPosition, 100000)
            if vertexId > 0 and not self.firstFound and not self.ctrlPressed:
                # mark first found vertex
                self.firstFound = True
                self.firstFoundVertex = self.mLayer.mGraph.vertex(vertexId)
                self.firstMarker = QgsVertexMarker(iface.mapCanvas())
                self.firstMarker.setIconType(QgsVertexMarker.ICON_DOUBLE_TRIANGLE)
                self.firstMarker.setCenter(clickPosition)
            
            elif self.firstFound:
                # for now remove first found vertex, later get next marking spot as new position (maybe in left click instead?)
                self.firstFound = False
                iface.mapCanvas().scene().removeItem(self.firstMarker)
                
                del self.firstFoundVertex
                del self.firstMarker

            elif self.ctrlPressed: # CTRL + RightClick
                # remove vertex if found on click
                # TODO: add function in PGGraph deleteVertex
                # self.mLayer.mGraph.deleteVertex(vertexId)

        iface.mapCanvas().scene().removeItem(converter)
        
        self.mLayer.triggerRepaint()
        self.mCanvas.refresh()

    def keyPressEvent(self, event):
        # TODO: seems like keyPressEvent needs canvasPressEvent beforehand?
        if event.key() == Qt.Key_Control:
            self.ctrlPressed = True

    def keyReleaseEvent(self, event):
        self.ctrlPressed = False
    
    def isEditTool(self):
        return True