from qgis.core import *
from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QPoint, Qt

class QgsGraphMapTool(QgsMapTool):
    """
    QgsGraphMapTool should enable the user to edit a QgsGraphLayer
    """

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.mCanvas = canvas

        self.mLayer = layer

        self.firstFound = False
        self.ctrlPressed = False

    def activate(self):
        print("QgsGraphMapTool activated")
        # emit self.activated()
        pass

    def deactivate(self):
        print("QgsGraphMapTool deactivated")
        # emit self.deactivated()
        pass

    def _addVertex(self, point):
        """
        Adds a vertex to the Graphlayers graph.
        Also adds the vertex as feature to the layers DataProvider if necessary.

        :type point: QgsPointXY
        """
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(point))

        feat.setAttributes([self.mLayer.mGraph.vertexCount(), point.x(), point.y()])
        self.mLayer.dataProvider().addFeature(feat, True)

        self.mLayer.mGraph.addVertex(point)

    def _addEdge(self, p1, p2):
        """
        Adds an edge to the Graphlayers graph.
        Also adds the edge as feature to the layers DataProvider if necessary.

        Deletes the edge from the Graphlayers graph if it already existed.
        Also deletes the corresponding features from the Graphlayers DataProvider.

        :type p1: Integer
        :type p2: Integer
        """
        if p1 == p2:
            return

        edgeId = self.mLayer.mGraph.hasEdge(p1, p2)
        if edgeId >= 0:
            # delete possibly existing edge
            self.mLayer.mGraph.deleteEdge(edgeId)
            self.mLayer.mDataProvider.deleteFeature(edgeId, False)

            if self.mLayer.mGraph.edgeCount() == 0:
                # no edges exist anymore
                self.mLayer.mDataProvider.setGeometryToPoint(True)
        else:
            if self.mLayer.mGraph.edgeCount() == 0:
                # now edges exist
                self.mLayer.mDataProvider.setGeometryToPoint(False)
            
            # add new edge
            edgeId = self.mLayer.mGraph.addEdge(p1, p2)
            
            edge = self.mLayer.mGraph.edge(edgeId)

            feat = QgsFeature()
            fromVertex = self.mLayer.mGraph.vertex(edge.fromVertex()).point()
            toVertex = self.mLayer.mGraph.vertex(edge.toVertex()).point()
            feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

            feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex(), self.mLayer.mGraph.costOfEdge(edgeId)], False)

            self.mLayer.mDataProvider.addFeature(feat, False)


    def _deleteVertex(self, idx):
        """
        Deletes a vertex and its outgoing and incoming edges from the Graphlayers graph.
        Also deletes the corresponding features from the layers DataProvider.

        :type idx: Integer
        """
        deletedEdges = self.mLayer.mGraph.deleteVertex(idx)
        
        self.mLayer.mDataProvider.deleteFeature(idx, True)
        
        for edgeId in deletedEdges:
            self.mLayer.mDataProvider.deleteFeature(edgeId, False)


    def canvasPressEvent(self, event):
        """
        Contains graph editing functions on MouseClick:
        LeftClick: AddVertex without Edges on clicked position
        CTRL + LeftClick: AddVertex with Edges (according to GraphBuilder options) on clicked position
        RightClick: 1) Mark Vertex, 2) Move Vertex (with edges) on LeftClick OR Add Edge to Vertex on RightClick
        CTRL + RightClick: deleteVertex if found on clicked position

        :type event: QgsMapMouseEvent
        """
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        self.converter = QgsVertexMarker(iface.mapCanvas())
        clickPosition = self.converter.toMapCoordinates(clickPosition)
        clickPosition = self.mLayer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        if event.button() == Qt.LeftButton: # LeftClick

            if not self.ctrlPressed:
                if not self.firstFound: # addVertex
                    self._addVertex(clickPosition)
                
                else: # move firstFoundVertex to new position
                    # deleteVertex firstFoundVertex, addVertex (without edges) on clicked position
                    self._deleteVertex(self.firstFoundVertex)
                    
                    self._addVertex(clickPosition)
                    
                    self.__removeFirstFound()

            else: # CTRL + LeftClick
                if not self.firstFound:
                    # TODO: use addVertex from GraphBuilder to also add edges
                    self.__removeFirstFound()
                else:
                    # deleteVertex firstFoundVertex, addVertex (with edges) on clicked position
                    self._deleteVertex(self.firstFoundVertex)
                    # TODO: use addVertex from GraphBuilder to also add edges
                    self.__removeFirstFound()

        elif event.button() == Qt.RightButton: # RightClick

            # TODO: find a way to set a satisfying tolerance for the checkup
            vertexId = self.mLayer.mGraph.findVertex(clickPosition, iface.mapCanvas().mapUnitsPerPixel() * 4)
            
            if vertexId > 0 and not self.firstFound and not self.ctrlPressed: # first RightClick
                # mark first found vertex
                self.firstFound = True
                self.firstFoundVertex = vertexId
                self.firstMarker = QgsVertexMarker(iface.mapCanvas())
                self.firstMarker.setIconType(QgsVertexMarker.ICON_DOUBLE_TRIANGLE)
                self.firstMarker.setCenter(clickPosition)
            
            elif vertexId < 0 and self.firstFound: # second RightClick (no vertex found)
                self.__removeFirstFound()

            elif vertexId > 0 and self.firstFound and not self.ctrlPressed: # second RightClick
                # add edge between firstFoundVertex and vertexId
                # deletes edge if it already exits
                self._addEdge(self.firstFoundVertex, vertexId)                
                
                self.__removeFirstFound()

            elif vertexId > 0 and self.firstFound and self.ctrlPressed: # second CTRL + RightClick
                # remove vertex if found on click
                self._deleteVertex(vertexId)

                self.__removeFirstFound()

        iface.mapCanvas().scene().removeItem(self.converter)
        del self.converter  
        
        self.mLayer.triggerRepaint()
        # self.mCanvas.refresh()

    def keyPressEvent(self, event):
        """
        Additional edit options by pressing and holding keys:
        HOLD CTRL: enable new options on MouseClick, see canvasPressEvent
        ESC: quit edit mode

        :type event: QKeyEvent
        """
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