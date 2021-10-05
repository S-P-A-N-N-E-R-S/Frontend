from qgis.core import *
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand
from qgis.utils import iface

from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtWidgets import QDialog, QPushButton, QBoxLayout, QLabel, QDoubleSpinBox, QGroupBox
from qgis.PyQt.QtGui import QColor

from .QgsGraphUndoCommands import ExtVertexUndoCommand, ExtEdgeUndoCommand

class QgsGraphMapTool(QgsMapTool):
    """
    QgsGraphMapTool enables the user to edit an ExtGraph in a QgsGraphLayer
    """

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.mCanvas = canvas

        self.mLayer = layer

        self.firstFound = False
        self.ctrlPressed = False
        self.shiftPressed = False
        self.leftPressed = False

        self.rubberBand = None

    def activate(self):
        self.advancedCosts = self.mLayer.mGraph.distanceStrategy == "Advanced"
        # emit self.activated()
        pass

    def deactivate(self):
        # emit self.deactivated()
        pass

    def _addVertex(self, point, movePoint=False):
        """
        Adds a vertex to the Graphlayers graph.

        :type point: QgsPointXY
        :type movePoint: Bool instead of adding new vertex, move fristFoundVertex
        """
        # add new vertex
        if not movePoint:  
            vertexIdx = self.mLayer.mGraph.vertexCount()

            vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), vertexIdx, point, "Add")

        # move vertex
        else:
            oldPos = self.mLayer.mGraph.vertex(self.firstFoundVertexIdx).point()
            
            vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), self.firstFoundVertexIdx, oldPos, "Move", point)
        
        self.mLayer.mUndoStack.push(vertexUndoCommand)

    def _addVertexWithEdges(self, point):
        """
        Adds a vertex to the Graphlayers graph.
        Also adds edges according to the chosen GraphBuilder settings.

        :type point: QgsPointXY
        """
        vertexIdx = self.mLayer.mGraph.vertexCount()
        vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), vertexIdx, point, "AddWithEdges")
        self.mLayer.mUndoStack.push(vertexUndoCommand)

    def _deleteEdge(self, edgeIdx, commandID=-1):
        """
        Deletes an edge from the Graphlayers graph.

        :type idx: Integer
        :type commandID: Integer, to possibly force merge of commands
        """
        if edgeIdx >= 0:
            edge = self.mLayer.mGraph.edge(edgeIdx)

            # delete possibly existing edge
            edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeIdx, edge.fromVertex(), edge.toVertex(), True)
            if commandID >= 0:
                edgeUndoCommand.setID(commandID)
            
            self.mLayer.mUndoStack.push(edgeUndoCommand)

            if self.mLayer.mGraph.edgeCount() == 0:
                # no edges exist anymore
                self.mLayer.mDataProvider.setGeometryToPoint(True)

    def _addEdge(self, p1Idx, p2Idx):
        """
        Adds an edge to the Graphlayers graph.

        For existing edges, a new Dialog for this edge will be opened.

        :type p1: Integer
        :type p2: Integer
        """
        if p1Idx == p2Idx:
            return

        edgeIdx = self.mLayer.mGraph.hasEdge(p1Idx, p2Idx)
        if edgeIdx < 0:
            if self.mLayer.mGraph.edgeCount() == 0:
                # now edges exist
                self.mLayer.mDataProvider.setGeometryToPoint(False)
            
            # add new edge
            edgeIdx = self.mLayer.mGraph.edgeCount()

            edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeIdx, self.mLayer.mGraph.vertex(p1Idx).id(), self.mLayer.mGraph.vertex(p2Idx).id(), False)
            self.mLayer.mUndoStack.push(edgeUndoCommand)

        # open edge window on found edge (possibility to set costs for newly added edges)
        win = QDialog(iface.mainWindow())
        win.setVisible(True)

        # QBoxLayout to add widgets to
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # QLabel with information about the GraphLayer
        edge = self.mLayer.mGraph.edge(edgeIdx)
        informationLabel = QLabel(self.tr("Edge ") +  str(edge.id()))
        informationLabel.setWordWrap(True)
        informationLabel.setVisible(True)
        informationLabel.setStyleSheet("border: 1px solid black;")
        layout.addWidget(informationLabel)

        if self.mLayer.mGraph.distanceStrategy == "Advanced":
            costs = []
            costGroupBox = QGroupBox(self.tr("Edge Cost per Advanced Cost Function"))
            costLayout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

            def _updateCosts():
                count = 0
                for child in costGroupBox.findChildren(QDoubleSpinBox):
                    costs[count] = child.value()
                    count += 1

                edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeIdx, -1, -1, False)
                edgeUndoCommand.setNewCosts(costs)
                self.mLayer.mUndoStack.push(edgeUndoCommand)

            applyButton = QPushButton(self.tr("Apply"))
            applyButton.setVisible(True)
            applyButton.setEnabled(False)
            applyButton.clicked.connect(_updateCosts)

            for i in range(self.mLayer.mGraph.amountOfEdgeCostFunctions()):
                costSpinBox = QDoubleSpinBox()
                costSpinBox.setMaximum(2147483647)
                costs.append(self.mLayer.mGraph.costOfEdge(edgeIdx, i))
                costSpinBox.setValue(costs[i])
                costSpinBox.setVisible(True)
                costSpinBox.valueChanged.connect(lambda: applyButton.setEnabled(True))
                costLayout.addWidget(costSpinBox)

            costGroupBox.setLayout(costLayout)
            costGroupBox.setVisible(True)
            layout.addWidget(costGroupBox)

            layout.addWidget(applyButton)
            
        else:
            distanceLabel = QLabel(self.tr("Distance Strategy: ") + self.mLayer.mGraph.distanceStrategy + ": " + str(self.mLayer.mGraph.costOfEdge(edgeIdx)))
            distanceLabel.setWordWrap(False)
            distanceLabel.setVisible(True)
            distanceLabel.setStyleSheet("border: 1px solid black;")
            layout.addWidget(distanceLabel)

        highlightEdgeButton = QPushButton(self.tr("Toggle Highlight"))
        highlightEdgeButton.clicked.connect(self.mLayer.mGraph.edge(edgeIdx).toggleHighlight)
        highlightEdgeButton.clicked.connect(self.mLayer.triggerRepaint)
        highlightEdgeButton.setVisible(True)
        layout.addWidget(highlightEdgeButton)

        deleteEdgeButton = QPushButton(self.tr("Delete"))
        deleteEdgeButton.clicked.connect(lambda: self._deleteEdge(edgeIdx))
        deleteEdgeButton.clicked.connect(win.done)
        deleteEdgeButton.setVisible(True)
        layout.addWidget(deleteEdgeButton)

        win.setLayout(layout)
        win.adjustSize()

    def _deleteVertex(self, idx, commandID=-1):
        """
        Deletes a vertex and its outgoing and incoming edges from the Graphlayers graph.

        :type idx: Integer
        :type commandID: Integer, to possibly force merge of commands
        """
        oldPos = self.mLayer.mGraph.vertex(idx).point()

        vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), idx, oldPos, "Delete")
        if commandID >= 0:
            vertexUndoCommand.setID(commandID)
        
        self.mLayer.mUndoStack.push(vertexUndoCommand)

    def _showRect(self):
        if hasattr(self, "rubberBand") and self.rubberBand and self.leftPressed and self.shiftPressed:

            self.rubberBand.setToGeometry(QgsGeometry.fromRect(QgsRectangle(self.topLeft, self.bottomRight)), None)

            self.rubberBand.show()

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
            self.leftPressed = True

            if self.shiftPressed: # select vertices by rectangle
                self.topLeft = clickPosition
                self.bottomRight = clickPosition
                self.drawRect = True

            elif not self.ctrlPressed:
                if not self.firstFound: # addVertex
                    self._addVertex(clickPosition)
                
                else: # move firstFoundVertex to new position
                    self._addVertex(clickPosition, True)
                    
                    self.__removeFirstFound()

            else: # CTRL + LeftClick
                if not self.advancedCosts:
                    if not self.firstFound:
                        # use addVertex from GraphBuilder to also add edges
                        self._addVertexWithEdges(clickPosition)

                        self.__removeFirstFound()
                    elif self.firstFound:
                        # deleteVertex firstFoundVertex, addVertex (with edges) on clicked position
                        self._deleteVertex(self.firstFoundVertexIdx)
                        
                        # use addVertex from GraphBuilder to also add edges
                        self._addVertexWithEdges(clickPosition)

                        self.__removeFirstFound()
                else:
                    iface.messageBar().pushMessage("Error", self.tr("Add Vertex with Edges is disabled for advanced costs"), level=Qgis.Critical)

        elif event.button() == Qt.RightButton: # RightClick

            vertexIdx = self.mLayer.mGraph.findVertex(clickPosition, iface.mapCanvas().mapUnitsPerPixel() * 8)
            
            if vertexIdx >= 0 and not self.firstFound and not self.ctrlPressed: # first RightClick
                # mark first found vertex
                self.firstFound = True
                self.firstFoundVertexIdx = vertexIdx
                self.firstFoundVertexID = self.mLayer.mGraph.vertex(vertexIdx).id()
                self.firstMarker = QgsVertexMarker(iface.mapCanvas())
                self.firstMarker.setIconType(QgsVertexMarker.ICON_CROSS)
                self.firstMarker.setCenter(clickPosition)
            
            elif vertexIdx < 0 and self.firstFound: # second RightClick (no vertex found)
                self.__removeFirstFound()

            elif vertexIdx > 0 and self.firstFound and not self.ctrlPressed: # second RightClick
                # add edge between firstFoundVertexID and vertexID
                # shows edge edit window if it already exits
                self._addEdge(self.firstFoundVertexIdx, vertexIdx)
                
                self.__removeFirstFound()

            elif vertexIdx > 0 and self.firstFound and self.ctrlPressed: # second CTRL + RightClick
                # remove vertex if found on click
                self._deleteVertex(vertexIdx)

                self.__removeFirstFound()
        
        self.mLayer.triggerRepaint()
        # self.mCanvas.refresh()

    def canvasMoveEvent(self, event):
        if hasattr(self, "drawRect") and self.drawRect:
            clickPosition = QPoint(event.pos().x(), event.pos().y())

            # used to convert canvas coordinates to map coordinates
            self.converter = iface.mapCanvas().getCoordinateTransform()
            clickPosition = self.converter.toMapCoordinates(clickPosition)
            clickPosition = self.mLayer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform) 

            self.bottomRight = clickPosition

            self._showRect()

    def canvasReleaseEvent(self, event):
        if self.shiftPressed and event.button() == Qt.LeftButton:
            foundVertexIndices = self.mLayer.mGraph.findVertices(self.topLeft, self.bottomRight)

            self.rubberBand.reset()
            del self.rubberBand

            # if vertices are found
            if len(foundVertexIndices) > 0:

                # open window for found vertices (possibility to delete vertices)
                win = QDialog(iface.mainWindow())
                win.setVisible(True)

                # QBoxLayout to add widgets to
                layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

                markers = []
                foundVerticesString = str(len(foundVertexIndices)) + self.tr(" vertices found.")
                foundVerticesIDString = ""
                for i in range(len(foundVertexIndices)):
                    vertex = self.mLayer.mGraph.vertex(foundVertexIndices[i])
                    markers.append(QgsVertexMarker(iface.mapCanvas()))
                    markers[i].setIconType(QgsVertexMarker.ICON_CROSS)
                    markers[i].setCenter(vertex.point())

                    foundVerticesIDString += str(vertex.id())
                    if i + 1 < len(foundVertexIndices):
                        foundVerticesIDString += ", "
                    if i % 5 == 0 and i > 0:
                        foundVerticesIDString += "\n"

                # QLabel with information about the found vertices
                informationLabel = QLabel(foundVerticesString)
                informationLabel.setVisible(True)
                informationLabel.setStyleSheet("border: 1px solid black;")
                layout.addWidget(informationLabel)

                foundIDLabel = QLabel(foundVerticesIDString)
                foundIDLabel.setVisible(False)
                foundIDLabel.setStyleSheet("border: 1px solid black;")
                layout.addWidget(foundIDLabel)

                # TODO: informationLabel stays big after Vertex ID are hidden again
                showVertexIDButton = QPushButton(self.tr("Show Vertex IDs"))
                showVertexIDButton.clicked.connect(lambda: showVertexIDButton.setText(self.tr("Show Vertex IDs") if foundIDLabel.isVisible() else self.tr("Hide Vertex IDs")))
                showVertexIDButton.clicked.connect(lambda: foundIDLabel.setVisible(not foundIDLabel.isVisible()))
                showVertexIDButton.setVisible(True)
                layout.addWidget(showVertexIDButton)

                def _deleteFoundVertices():
                    commandID = self.mLayer.mUndoStack.index()
                    self.mLayer.mUndoStack.beginMacro("Delete Selected Vertices")
                    
                    for i in range(len(foundVertexIndices) - 1, -1, -1):
                        self._deleteVertex(foundVertexIndices[i], commandID)
                    
                    self.mLayer.mUndoStack.endMacro() 

                deleteVerticesButton = QPushButton(self.tr("Delete Vertices"))
                deleteVerticesButton.clicked.connect(_deleteFoundVertices)
                deleteVerticesButton.clicked.connect(win.done)
                deleteVerticesButton.setVisible(True)
                layout.addWidget(deleteVerticesButton)

                def _deleteAttachedEdges():
                    commandID = self.mLayer.mUndoStack.index()

                    self.mLayer.mUndoStack.beginMacro("Delete Attached Edges")
                    
                    for idx in foundVertexIndices:
                        vertex = self.mLayer.mGraph.vertex(idx)

                        # delete outgoing edges
                        for outgoingIdx in range(len(vertex.outgoingEdges()) - 1, -1, -1):
                            edgeID = vertex.outgoingEdges()[outgoingIdx]
                            self._deleteEdge(self.mLayer.mGraph.findEdgeByID(edgeID), commandID)

                        # delete incoming edges
                        for incomingIdx in range(len(vertex.incomingEdges()) - 1, -1, -1):
                            edgeID = vertex.incomingEdges()[incomingIdx]
                            self._deleteEdge(self.mLayer.mGraph.findEdgeByID(edgeID), commandID)
                    
                    self.mLayer.mUndoStack.endMacro()

                deleteEdgesButton = QPushButton(self.tr("Delete Attached Edges"))
                deleteEdgesButton.clicked.connect(_deleteAttachedEdges)
                deleteEdgesButton.clicked.connect(win.done)
                deleteEdgesButton.setVisible(True)
                layout.addWidget(deleteEdgesButton)

                win.setLayout(layout)
                win.adjustSize()            
                
                def _closeVerticesWindow():
                    numberFound = len(foundVertexIndices)
                    for i in range(numberFound - 1, -1, -1):
                        iface.mapCanvas().scene().removeItem(markers[i])
                        del markers[i]

                win.rejected.connect(_closeVerticesWindow)

            self.drawRect = False
            self.topLeft = None
            self.bottomRight = None
            self.leftPressed = False

    def keyPressEvent(self, event):
        """
        Additional edit options by pressing and holding keys:
        HOLD CTRL: enable new options on MouseClick, see canvasPressEvent
        ESC: quit edit mode
        HOLD SHIFT: enable multiple vertex selection

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

        elif event.key() == Qt.Key_Shift:
            self.shiftPressed = True
            self.rubberBand = QgsRubberBand(iface.mapCanvas(), True)
            self.rubberBand.setColor(QColor(232, 137, 137, 50))

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrlPressed = False

        elif event.key() == Qt.Key_Shift:
            self.shiftPressed = False
            if hasattr(self, "rubberBand") and self.rubberBand:
                self.rubberBand.reset()
                del self.rubberBand

    def __removeFirstFound(self):
        if self.firstFound:
            self.firstFound = False
            
            iface.mapCanvas().scene().removeItem(self.firstMarker)
            del self.firstMarker

    def isEditTool(self):
        return True