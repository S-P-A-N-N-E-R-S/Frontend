from qgis.core import *
from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtWidgets import QDialog, QPushButton, QBoxLayout, QLabel, QDoubleSpinBox, QGroupBox

from .QgsGraphUndoCommands import ExtVertexUndoCommand, ExtEdgeUndoCommand

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
        self.advancedCosts = self.mLayer.mGraph.distanceStrategy == "Advanced"
        # emit self.activated()
        pass

    def deactivate(self):
        # emit self.deactivated()
        pass

    def _addVertex(self, point, movePoint=False):
        """
        Adds a vertex to the Graphlayers graph.
        Also adds the vertex as feature to the layers DataProvider if necessary.

        :type point: QgsPointXY
        :type movePoint: Bool instead of adding new vertex, move fristFoundVertex
        """
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(point))

        # add new vertex
        if not movePoint:
            feat.setAttributes([self.mLayer.mGraph.vertexCount(), point.x(), point.y()])
            
            if len(self.mLayer.mGraph.availableVertexIndices) > 0:
                vertexId = self.mLayer.mGraph.availableVertexIndices[0]
            else:
                vertexId = self.mLayer.mGraph.vertexCount()

            vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), vertexId, point, "Add")

        # move vertex
        else:
            feat.setAttributes([self.firstFoundVertex, point.x(), point.y()])

            oldPos = self.mLayer.mGraph.vertex(self.firstFoundVertex).point()
            
            vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), self.firstFoundVertex, oldPos, "Move", point)
        
        self.mLayer.mUndoStack.push(vertexUndoCommand)
        self.mLayer.dataProvider().addFeature(feat, True)

    def _deleteEdge(self, edgeIdx):
        if edgeIdx >= 0:
            edge = self.mLayer.mGraph.edge(edgeIdx)

            # delete possibly existing edge            
            edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeIdx, edge.fromVertex(), edge.toVertex(), True)
            self.mLayer.mUndoStack.push(edgeUndoCommand)

            self.mLayer.mDataProvider.deleteFeature(edgeIdx, False)

            if self.mLayer.mGraph.edgeCount() == 0:
                # no edges exist anymore
                self.mLayer.mDataProvider.setGeometryToPoint(True)

    def _addEdge(self, p1, p2):
        """
        Adds an edge to the Graphlayers graph.
        Also adds the edge as feature to the layers DataProvider if necessary.

        For existing edges, a new Dialog for this edge will be opened.

        :type p1: Integer
        :type p2: Integer
        """
        if p1 == p2:
            return

        edgeId = self.mLayer.mGraph.hasEdge(p1, p2)
        if edgeId >= 0:
            win = QDialog(iface.mainWindow())
            win.setVisible(True)

            # QBoxLayout to add widgets to
            layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

            # QLabel with information about the GraphLayer
            informationLabel = QLabel("Edge " +  str(edgeId))
            informationLabel.setWordWrap(True)
            informationLabel.setVisible(True)
            informationLabel.setStyleSheet("border: 1px solid black;")
            layout.addWidget(informationLabel)

            if self.mLayer.mGraph.distanceStrategy == "Advanced":
                costs = []
                
                def _setNewCosts(idx, cost):
                    costs[idx] = cost

                def _updateCosts():
                    edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeId, -1, -1, False)
                    edgeUndoCommand.setNewCosts(costs)
                    self.mLayer.mUndoStack.push(edgeUndoCommand)

                applyButton = QPushButton("Apply")
                applyButton.setVisible(True)
                applyButton.setEnabled(False)
                applyButton.clicked.connect(_updateCosts)

                costGroupBox = QGroupBox("Edge Cost per Advanced Cost Function")
                costLayout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
                for i in range(self.mLayer.mGraph.amountOfEdgeCostFunctions()):
                    costSpinBox = QDoubleSpinBox()
                    costs.append(self.mLayer.mGraph.costOfEdge(edgeId, i))
                    costSpinBox.setValue(costs[i])
                    costSpinBox.setVisible(True)
                    costSpinBox.valueChanged.connect(lambda: applyButton.setEnabled(True))
                    costSpinBox.valueChanged.connect(lambda: _setNewCosts(i, costSpinBox.value()))
                    costLayout.addWidget(costSpinBox)

                costGroupBox.setLayout(costLayout)
                costGroupBox.setVisible(True)
                layout.addWidget(costGroupBox)

                layout.addWidget(applyButton)
                
            else:
                distanceLabel = QLabel("Distance Strategy: " + self.mLayer.mGraph.distanceStrategy + ": " + str(self.mLayer.mGraph.costOfEdge(edgeId)))
                distanceLabel.setWordWrap(False)
                distanceLabel.setVisible(True)
                distanceLabel.setStyleSheet("border: 1px solid black;")
                layout.addWidget(distanceLabel)

            deleteEdgeButton = QPushButton("Delete")
            deleteEdgeButton.clicked.connect(lambda: self._deleteEdge(edgeId))
            deleteEdgeButton.clicked.connect(win.done)
            deleteEdgeButton.setVisible(True)
            layout.addWidget(deleteEdgeButton)

            win.setLayout(layout)
            win.adjustSize()

        else:
            # advancedCosts prevent user from adding edges

            if self.mLayer.mGraph.edgeCount() == 0:
                # now edges exist
                self.mLayer.mDataProvider.setGeometryToPoint(False)
            
            # add new edge
            if len(self.mLayer.mGraph.availableEdgeIndices) > 0:
                edgeId = self.mLayer.mGraph.availableEdgeIndices[0]
            else:
                edgeId = self.mLayer.mGraph.edgeCount()

            edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeId, p1, p2, False)
            self.mLayer.mUndoStack.push(edgeUndoCommand)
            
            edge = self.mLayer.mGraph.edge(edgeId)

            feat = QgsFeature()
            fromVertex = self.mLayer.mGraph.vertex(edge.fromVertex()).point()
            toVertex = self.mLayer.mGraph.vertex(edge.toVertex()).point()
            feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

            feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex(), self.mLayer.mGraph.costOfEdge(edgeId)])

            self.mLayer.mDataProvider.addFeature(feat, False)

    def _deleteVertex(self, idx):
        """
        Deletes a vertex and its outgoing and incoming edges from the Graphlayers graph.
        Also deletes the corresponding features from the layers DataProvider.

        :type idx: Integer
        """
        oldPos = self.mLayer.mGraph.vertex(idx).point()

        vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), idx, oldPos, "Delete")
        self.mLayer.mUndoStack.push(vertexUndoCommand)
        
        self.mLayer.mDataProvider.deleteFeature(idx, True)
        
        # TODO: move deleteFeatures for edges in UndoCommands
        # for edgeId in deletedEdges:
        #     self.mLayer.mDataProvider.deleteFeature(edgeId, False)


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
        self.converter = iface.mapCanvas().getCoordinateTransform()
        clickPosition = self.converter.toMapCoordinates(clickPosition)
        clickPosition = self.mLayer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        if event.button() == Qt.LeftButton: # LeftClick

            if not self.ctrlPressed:
                if not self.firstFound: # addVertex
                    self._addVertex(clickPosition)
                
                else: # move firstFoundVertex to new position
                    self._addVertex(clickPosition, True)
                    
                    self.__removeFirstFound()

            else: # CTRL + LeftClick
                if not self.advancedCosts:
                    print("addVertexWithEdges")
                    if not self.firstFound:
                        # use addVertex from GraphBuilder to also add edges
                        addedEdges = self.mLayer.mGraph.addVertexWithEdges([clickPosition.x(), clickPosition.y()])
                        self.__removeFirstFound()
                    elif self.firstFound:
                        # deleteVertex firstFoundVertex, addVertex (with edges) on clicked position
                        self._deleteVertex(self.firstFoundVertex)
                        
                        # use addVertex from GraphBuilder to also add edges
                        addedEdges = self.mLayer.mGraph.addVertexWithEdges([clickPosition.x(), clickPosition.y()])
                        self.__removeFirstFound()
                    
                    # add Features from added vertices and lines from GraphBuilder
                    feat = QgsFeature()
                    feat.setGeometry(QgsGeometry.fromPointXY(clickPosition))

                    feat.setAttributes([self.mLayer.mGraph.vertexCount(), clickPosition.x(), clickPosition.y()])
                    self.mLayer.dataProvider().addFeature(feat, True)

                    for edge in addedEdges:
                        edge = self.mLayer.mGraph.edge(edge[0])

                        feat = QgsFeature()
                        fromVertex = self.mLayer.mGraph.vertex(edge.fromVertex()).point()
                        toVertex = self.mLayer.mGraph.vertex(edge.toVertex()).point()
                        feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                        feat.setAttributes([edge[0], edge.fromVertex(), edge.toVertex(), self.mLayer.mGraph.costOfEdge(edge[0])], False)

                        self.mLayer.mDataProvider.addFeature(feat, False)

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
            
            # elif vertexId < 0 and self.firstFound or self.advancedCosts and self.firstFound: # second RightClick (no vertex found)
            #     self.__removeFirstFound()

            elif vertexId > 0 and self.firstFound and not self.ctrlPressed:# and not self.advancedCosts: # second RightClick
                # add edge between firstFoundVertex and vertexId
                # deletes edge if it already exits
                self._addEdge(self.firstFoundVertex, vertexId)                
                
                self.__removeFirstFound()

            elif vertexId > 0 and self.firstFound and self.ctrlPressed: # second CTRL + RightClick
                # remove vertex if found on click
                self._deleteVertex(vertexId)

                self.__removeFirstFound()
        
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