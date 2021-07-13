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
        """Contains graph editing functions on MouseClick:
           LeftClick: AddVertex without Edges on clicked position
           CTRL + LeftClick: AddVertex with Edges (according to GraphBuilder options) on clicked position
           RightClick: 1) Mark Vertex, 2) Move Vertex (with edges) on LeftClick OR Add Edge to Vertex on RightClick
           CTRL + RightClick: deleteVertex if found on clicked position

        Args:
            event ([type]): [description]
        """
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        self.converter = QgsVertexMarker(iface.mapCanvas())
        clickPosition = self.converter.toMapCoordinates(clickPosition)
        clickPosition = self.mLayer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        if event.button() == Qt.LeftButton: # LeftClick

            if not self.ctrlPressed:
                if not self.firstFound: # addVertex
                    
                    if self.mLayer.mGraph.edgeCount == 0:
                        feat = QgsFeature()
                        feat.setGeometry(QgsGeometry.fromPointXY(clickPosition))

                        feat.setAttributes([self.mLayer.mGraph.vertexCount(), clickPosition.x(), clickPosition.y()])
                        self.mLayer.dataProvider().addFeature(feat)

                    self.mLayer.mGraph.addVertex(clickPosition)
                
                else: # move firstFoundVertex to new position
                    # deleteVertex firstFoundVertex, addVertex (with edges) on clicked position
                    self.__removeFirstFound()

            else: # CTRL + LeftClick
                # use addVertex from GraphBuilder to also add edges
                self.__removeFirstFound()

        elif event.button() == Qt.RightButton: # RightClick

            # TODO: find a way to set a satisfying tolerance for the checkup
            vertexId = self.mLayer.mGraph.findVertex(clickPosition, 100000)
            
            if vertexId > 0 and not self.firstFound and not self.ctrlPressed: # first RightClick
                # mark first found vertex
                self.firstFound = True
                self.firstFoundVertex = vertexId
                self.firstMarker = QgsVertexMarker(iface.mapCanvas())
                self.firstMarker.setIconType(QgsVertexMarker.ICON_DOUBLE_TRIANGLE)
                self.firstMarker.setCenter(clickPosition)
            
            elif vertexId > 0 and self.firstFound and not self.ctrlPressed: # second RightClick
                # add edge between firstFoundVertex and vertexId                
                self.mLayer.mGraph.addEdge(self.firstFoundVertex, vertexId)

                if self.mLayer.mGraph.edgeCount() != 0:
                    # TODO: what to do if graph had no edges before -> GraphLayer has points as features
                    # -> Two Ideas: 1) don't allow add edges, 2) remove all features and add edge feature
                    
                    edgeId = self.mLayer.mGraph.edgeCount() - 1
                    edge = self.mLayer.mGraph.edge(edgeId)

                    feat = QgsFeature()
                    fromVertex = self.mLayer.mGraph.vertex(edge.fromVertex()).point()
                    toVertex = self.mLayer.mGraph.vertex(edge.toVertex()).point()
                    feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                    feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex(), self.mLayer.mGraph.costOfEdge(edgeId)])

                    self.mLayer.mDataProvider.addFeature(feat)
                
                self.__removeFirstFound()

            elif vertexId > 0 and self.ctrlPressed: # CTRL + RightClick
                # remove vertex if found on click
                # TODO: add function in PGGraph deleteVertex
                # self.mLayer.mGraph.deleteVertex(vertexId)
                self.__removeFirstFound()

        iface.mapCanvas().scene().removeItem(self.converter)
        del self.converter  
        
        self.mLayer.triggerRepaint()
        self.mCanvas.refresh()

    def keyPressEvent(self, event):
        # TODO: seems like keyPressEvent needs canvasPressEvent beforehand?
        if event.key() == Qt.Key_Control:
            self.ctrlPressed = True
        elif event.key() == Qt.Key_Escape:
            # stop edit mode on Key_Escape
            if self.firstFound:
                self.__removeFirstFound()

            self.mLayer.toggleEdit()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrlPressed = False

    def __removeFirstFound(self):
        if self.firstFound:
            self.firstFound = False
            
            iface.mapCanvas().scene().removeItem(self.firstMarker)
            del self.firstMarker

    def isEditTool(self):
        return True