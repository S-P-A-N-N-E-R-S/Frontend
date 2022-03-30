#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Julian Wittker
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

from qgis.core import Qgis, QgsGeometry, QgsRectangle, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand
from qgis.utils import iface

from qgis.PyQt.QtCore import QPoint, Qt, QObject
from qgis.PyQt.QtWidgets import QDialog, QPushButton, QBoxLayout, QLabel, QDoubleSpinBox, QGroupBox
from qgis.PyQt.QtGui import QColor

from .GraphUndoCommands import ExtVertexUndoCommand, ExtEdgeUndoCommand

import enum

class Operations(enum.Enum):
    DEFAULT = -1

    # left clicks
    ADD_VERTEX_WITH_EDGES = 1

    # right clicks
    SELECT_VERTEX = 2

class GraphMapTool(QgsMapTool, QObject):
    """
    GraphMapTool enables the user to edit an ExtGraph in a GraphLayer
    """

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.mCanvas = canvas

        self.mLayer = layer

        self.firstFound = False
        self.ctrlPressed = False
        self.shiftPressed = False
        self.leftPressed = False
        self.rightPressed = False

        self.rubberBand = None

        # states which operation got triggered
        self.operation = Operations.DEFAULT
        self.triggeredAction = None

    def activate(self):
        self.advancedCosts = self.mLayer.mGraph.distanceStrategy == "Advanced"
        iface.mapCanvas().grabKeyboard()

        # enable actions in edit toolbar and listen to them
        toolbar = self.mLayer.graphToolBar
        toolbar.actionTriggered.connect(self.__toolBarActionTriggered)

        for action in toolbar.actions():
            if not "Delete Vertex" in action.whatsThis():
                action.setEnabled(True)
            if "Toggle Edit" in action.whatsThis():
                action.setChecked(True)

        self.operation = Operations.DEFAULT

    def deactivate(self):
        if hasattr(self, "win") and self.win:
            self.win.done(0)
        iface.mapCanvas().releaseKeyboard()

        # enable all actions in edit toolbar and listen to them
        toolbar = self.mLayer.graphToolBar
        toolbar.actionTriggered.disconnect(self.__toolBarActionTriggered)

        for action in toolbar.actions():
            whatsThis = action.whatsThis()
            if "Vertex" in whatsThis or "Undo" in whatsThis or "Redo" in whatsThis:
                action.setEnabled(False)
            action.setChecked(False)

        self.mLayer = None

    def __toolBarActionTriggered(self, action):
        whatsThis = action.whatsThis()
        self.triggeredAction = action

        if "Select Vertex" in whatsThis:
            if self.operation == Operations.SELECT_VERTEX:
                self.operation = Operations.DEFAULT
                self.triggeredAction.setChecked(False)
            else:
                self.operation = Operations.SELECT_VERTEX
                self.triggeredAction.setChecked(True)

        elif "Delete Vertex" in whatsThis:
            # remove vertex if found
            self._deleteVertex(self.firstFoundVertexID)

            self.__removeFirstFound()

        elif "Add Vertex With Edges" in whatsThis:
            if self.operation == Operations.ADD_VERTEX_WITH_EDGES:
                self.operation = Operations.DEFAULT
                self.triggeredAction.setChecked(False)
            else:
                self.operation = Operations.ADD_VERTEX_WITH_EDGES
                self.triggeredAction.setChecked(True)

        elif action.tr("Undo") in whatsThis:
            self.mLayer.mUndoStack.undo()

        elif action.tr("Redo") in whatsThis:
            self.mLayer.mUndoStack.redo()

    def _addVertex(self, point, movePoint=False):
        """
        Adds a vertex to the Graphlayers graph.

        :type point: QgsPointXY
        :type movePoint: Bool instead of adding new vertex, move fristFoundVertex
        """
        # add new vertex
        if not movePoint:
            vertexId = self.mLayer.mGraph.nextVertexID()

            vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), vertexId, point, "Add")

        # move vertex
        else:
            # prevent moving vertices if costs are advanced since they can't be adapted yet
            if self.advancedCosts:
                iface.messageBar().pushMessage("Error", self.tr("Moving vertices is disabled for advanced costs"),
                                               level=Qgis.Critical)
                return

            oldPos = self.mLayer.mGraph.vertex(self.firstFoundVertexID).point()

            vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), self.firstFoundVertexID, oldPos, "Move", point)

        self.mLayer.mUndoStack.push(vertexUndoCommand)

    def _addVertexWithEdges(self, point):
        """
        Adds a vertex to the Graphlayers graph.
        Also adds edges according to the chosen GraphBuilder settings.

        :type point: QgsPointXY
        """
        vertexId = self.mLayer.mGraph.nextVertexID()
        vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), vertexId, point, "AddWithEdges")
        self.mLayer.mUndoStack.push(vertexUndoCommand)

    def _deleteEdge(self, edgeId):
        """
        Deletes an edge from the Graphlayers graph.

        :type edgeId: Integer, edge id to delete
        """
        if edgeId >= 0:
            edge = self.mLayer.mGraph.edge(edgeId)

            # delete possibly existing edge
            edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeId, edge.fromVertex(), edge.toVertex(), True)

            self.mLayer.mUndoStack.push(edgeUndoCommand)

            if self.mLayer.mGraph.edgeCount() == 0:
                # no edges exist anymore
                self.mLayer.mDataProvider.setGeometryToPoint(True)

    def _addEdge(self, p1Id, p2Id):
        """
        Adds an edge to the Graphlayers graph.

        For existing edges, a new Dialog for this edge will be opened.

        :type p1Id: Integer, first vertex id
        :type p2Id: Integer, second vertex id
        """
        if p1Id == p2Id:
            return

        edgeId = self.mLayer.mGraph.hasEdge(p1Id, p2Id)
        if edgeId < 0:
            if self.mLayer.mGraph.edgeCount() == 0:
                # now edges exist
                self.mLayer.mDataProvider.setGeometryToPoint(False)

            # add new edge
            edgeId = self.mLayer.mGraph.nextEdgeID()

            edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeId, p1Id, p2Id, False)
            self.mLayer.mUndoStack.push(edgeUndoCommand)

        # open edge window on found edge (possibility to set costs for newly added edges)
        if hasattr(self, "win"):
            self.win.done(0)
        self.win = QDialog(iface.mainWindow())
        self.win.setVisible(True)

        # QBoxLayout to add widgets to
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # QLabel with information about the GraphLayer
        edge = self.mLayer.mGraph.edge(edgeId)
        informationLabel = QLabel(self.tr("Edge ") +  str(edgeId))
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

                edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeId, -1, -1, False)
                edgeUndoCommand.setNewCosts(costs)
                self.mLayer.mUndoStack.push(edgeUndoCommand)

            applyButton = QPushButton(self.tr("Apply"))
            applyButton.setVisible(True)
            applyButton.setEnabled(False)
            applyButton.clicked.connect(_updateCosts)

            for i in range(self.mLayer.mGraph.amountOfEdgeCostFunctions()):
                costSpinBox = QDoubleSpinBox()
                costSpinBox.setMaximum(2147483647)
                costs.append(self.mLayer.mGraph.costOfEdge(edgeId, i))
                costSpinBox.setValue(costs[i])
                costSpinBox.setVisible(True)
                costSpinBox.valueChanged.connect(lambda: applyButton.setEnabled(True))
                costLayout.addWidget(costSpinBox)

            costGroupBox.setLayout(costLayout)
            costGroupBox.setVisible(True)
            layout.addWidget(costGroupBox)

            layout.addWidget(applyButton)

        else:
            distanceLabel = QLabel(self.tr("Distance Strategy: ") + self.mLayer.mGraph.distanceStrategy + ": " +\
                                   str(self.mLayer.mGraph.costOfEdge(edgeId)))
            distanceLabel.setWordWrap(False)
            distanceLabel.setVisible(True)
            distanceLabel.setStyleSheet("border: 1px solid black;")
            layout.addWidget(distanceLabel)

        highlightEdgeButton = QPushButton(self.tr("Toggle Highlight"))
        highlightEdgeButton.clicked.connect(self.mLayer.mGraph.edge(edgeId).toggleHighlight)
        highlightEdgeButton.clicked.connect(self.mLayer.triggerRepaint)
        highlightEdgeButton.setVisible(True)
        layout.addWidget(highlightEdgeButton)

        deleteEdgeButton = QPushButton(self.tr("Delete"))
        deleteEdgeButton.clicked.connect(lambda: self._deleteEdge(edgeId))
        deleteEdgeButton.clicked.connect(self.win.done)
        deleteEdgeButton.setVisible(True)
        layout.addWidget(deleteEdgeButton)

        self.win.setLayout(layout)
        self.win.adjustSize()

    def _deleteVertex(self, id):
        """
        Deletes a vertex and its outgoing and incoming edges from the Graphlayers graph.

        :type id: Integer, vertex id to be removed
        :type commandID: Integer, to possibly force merge of commands
        """
        oldPos = self.mLayer.mGraph.vertex(id).point()

        vertexUndoCommand = ExtVertexUndoCommand(self.mLayer.id(), id, oldPos, "Delete")

        self.mLayer.mUndoStack.push(vertexUndoCommand)

    def _showRect(self):
        if hasattr(self, "rubberBand") and self.rubberBand and (self.leftPressed or self.rightPressed) and\
           self.shiftPressed:

            self.rubberBand.setToGeometry(QgsGeometry.fromRect(QgsRectangle(self.topLeft, self.bottomRight)), None)

            self.rubberBand.show()

    def canvasPressEvent(self, event):
        """
        Contains graph editing functions on MouseClick:
        LeftClick: AddVertex without Edges on clicked position
        CTRL + LeftClick: AddVertex with Edges (according to GraphBuilder options) on clicked position
        RightClick: 1) Mark Vertex, 2) Move Vertex (with edges) on LeftClick OR Add Edge to Vertex on RightClick
        CTRL + RightClick: deleteVertex if found on clicked position
        SHIFT + LeftClick + Drag: select multiple vertices at once
        SHIFT + RightClick + Drag: zoom to selected area

        R: removes the existing single vertex selection

        :type event: QgsMapMouseEvent
        """
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        self.converter = iface.mapCanvas().getCoordinateTransform()
        clickPosition = self.converter.toMapCoordinates(clickPosition)

        if QgsProject.instance().crs().authid() != self.mLayer.mGraph.crs.authid():
            clickPosition = self.mLayer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        # left click or left click Operations
        if event.button() == Qt.LeftButton and self.operation == Operations.DEFAULT or\
           self.operation == Operations.ADD_VERTEX_WITH_EDGES: # LeftClick
            self.leftPressed = True

            if self.shiftPressed: # select vertices by rectangle
                self.topLeft = clickPosition
                self.bottomRight = clickPosition
                self.drawRect = True

            elif not self.ctrlPressed and not self.operation == Operations.ADD_VERTEX_WITH_EDGES:
                if not self.firstFound: # addVertex
                    self._addVertex(clickPosition)

                elif self.firstFound: # move firstFoundVertex to new position
                    self._addVertex(clickPosition, True)

                    self.__removeFirstFound()

            elif self.ctrlPressed or self.operation == Operations.ADD_VERTEX_WITH_EDGES: # CTRL + LeftClick
                if not self.advancedCosts:
                    if not self.firstFound:
                        # use addVertex from GraphBuilder to also add edges
                        self._addVertexWithEdges(clickPosition)

                        self.__removeFirstFound()

                    elif self.firstFound:
                        # deleteVertex firstFoundVertex, addVertex (with edges) on clicked position
                        self._deleteVertex(self.firstFoundVertexID)

                        # use addVertex from GraphBuilder to also add edges
                        self._addVertexWithEdges(clickPosition)

                        self.__removeFirstFound()

                    self.operation = Operations.DEFAULT
                else:
                    iface.messageBar().pushMessage("Error",
                                                   self.tr("Add Vertex with Edges is disabled for advanced costs"),
                                                   level=Qgis.Critical)

        # right click or right click Operations
        if not self.operation == Operations.DEFAULT or event.button() == Qt.RightButton: # RightClick
            self.rightPressed = True

            vertexId = self.mLayer.mGraph.findVertex(clickPosition)

            if self.shiftPressed: # select area to zoom in by rectangle
                self.topLeft = clickPosition
                self.bottomRight = clickPosition
                self.drawRect = True

            elif vertexId >= 0 and (self.operation == Operations.SELECT_VERTEX or not self.ctrlPressed) and\
                 not self.firstFound: # first RightClick
                # mark first found vertex
                self.firstFound = True
                self.firstFoundVertexID = vertexId
                self.firstMarker = QgsVertexMarker(iface.mapCanvas())
                self.firstMarker.setIconType(QgsVertexMarker.ICON_CROSS)

                foundPosition = self.mLayer.mGraph.vertex(self.firstFoundVertexID).point()
                if QgsProject.instance().crs().authid() != self.mLayer.mGraph.crs.authid():
                    self.firstMarker.setCenter(self.mLayer.mTransform.transform(foundPosition))
                else:
                    self.firstMarker.setCenter(foundPosition)

                for action in self.mLayer.graphToolBar.actions():
                    if "Delete Vertex" in action.whatsThis():
                        action.setEnabled(True)

            elif vertexId < 0 and self.firstFound: # second RightClick (no vertex found)
                self.__removeFirstFound()

            elif vertexId > 0 and self.firstFound and (not self.ctrlPressed or\
                                                       self.operation == Operations.SELECT_VERTEX): # second RightClick
                # add edge between firstFoundVertexID and vertexID
                # shows edge edit window if it already exits
                self._addEdge(self.firstFoundVertexID, vertexId)

                self.__removeFirstFound()

            elif vertexId > 0 and self.ctrlPressed and self.firstFound: # second CTRL + RightClick
                # remove vertex if found on click
                self._deleteVertex(vertexId)

                self.__removeFirstFound()

        self.operation = Operations.DEFAULT
        if self.triggeredAction:
            self.triggeredAction.setChecked(False)
        self.mLayer.triggerRepaint()

    def canvasMoveEvent(self, event):
        if hasattr(self, "drawRect") and self.drawRect:
            clickPosition = QPoint(event.pos().x(), event.pos().y())

            # used to convert canvas coordinates to map coordinates
            self.converter = iface.mapCanvas().getCoordinateTransform()
            clickPosition = self.converter.toMapCoordinates(clickPosition)

            self.bottomRight = clickPosition

            self._showRect()

    def canvasReleaseEvent(self, event):
        if self.shiftPressed and event.button() == Qt.LeftButton:
            foundVertexIds = self.mLayer.mGraph.findVertices(self.topLeft, self.bottomRight)

            self.rubberBand.reset()
            del self.rubberBand

            # if vertices are found
            if len(foundVertexIds) > 0:

                # open window for found vertices (possibility to delete vertices)
                if hasattr(self, "win"):
                    self.win.done(0)
                self.win = QDialog(iface.mainWindow())
                self.win.setVisible(True)

                # QBoxLayout to add widgets to
                layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

                markers = []
                foundVerticesString = str(len(foundVertexIds)) + self.tr(" vertices found.")
                foundVerticesIDString = ""
                for i in range(len(foundVertexIds)):
                    vertex = self.mLayer.mGraph.vertex(foundVertexIds[i])
                    markers.append(QgsVertexMarker(iface.mapCanvas()))
                    markers[i].setIconType(QgsVertexMarker.ICON_CROSS)

                    foundPosition = vertex.point()
                    if QgsProject.instance().crs().authid() != self.mLayer.mGraph.crs.authid():
                        markers[i].setCenter(self.mLayer.mTransform.transform(foundPosition))
                    else:
                        markers[i].setCenter(foundPosition)

                    foundVerticesIDString += str(foundVertexIds[i])
                    if i + 1 < len(foundVertexIds):
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
                showVertexIDButton.clicked.connect(lambda: showVertexIDButton.setText(self.tr("Show Vertex IDs")\
                                                           if foundIDLabel.isVisible() else self.tr("Hide Vertex IDs")))
                showVertexIDButton.clicked.connect(lambda: foundIDLabel.setVisible(not foundIDLabel.isVisible()))
                showVertexIDButton.setVisible(True)
                layout.addWidget(showVertexIDButton)

                def _deleteFoundVertices():
                    self.mLayer.mUndoStack.beginMacro("Delete Selected Vertices")

                    for i in range(len(foundVertexIds) - 1, -1, -1):
                        self._deleteVertex(foundVertexIds[i])

                    self.mLayer.mUndoStack.endMacro()

                deleteVerticesButton = QPushButton(self.tr("Delete Vertices"))
                deleteVerticesButton.clicked.connect(_deleteFoundVertices)
                deleteVerticesButton.clicked.connect(self.win.done)
                deleteVerticesButton.setVisible(True)
                layout.addWidget(deleteVerticesButton)

                def _deleteAttachedEdges():
                    self.mLayer.mUndoStack.beginMacro("Delete Attached Edges")

                    for id in foundVertexIds:
                        vertex = self.mLayer.mGraph.vertex(id)

                        # delete outgoing edges
                        for outgoingIdx in range(len(vertex.outgoingEdges()) - 1, -1, -1):
                            edgeID = vertex.outgoingEdges()[outgoingIdx]
                            self._deleteEdge(edgeID)

                        # delete incoming edges
                        for incomingIdx in range(len(vertex.incomingEdges()) - 1, -1, -1):
                            edgeID = vertex.incomingEdges()[incomingIdx]
                            self._deleteEdge(edgeID)

                    self.mLayer.mUndoStack.endMacro()

                deleteEdgesButton = QPushButton(self.tr("Delete Attached Edges"))
                deleteEdgesButton.clicked.connect(_deleteAttachedEdges)
                deleteEdgesButton.clicked.connect(self.win.done)
                deleteEdgesButton.setVisible(True)
                layout.addWidget(deleteEdgesButton)

                self.win.setLayout(layout)
                self.win.adjustSize()

                def _closeVerticesWindow():
                    numberFound = len(foundVertexIds)
                    for i in range(numberFound - 1, -1, -1):
                        iface.mapCanvas().scene().removeItem(markers[i])
                        del markers[i]

                self.win.rejected.connect(_closeVerticesWindow)

            self.drawRect = False
            self.topLeft = None
            self.bottomRight = None
            self.leftPressed = False

        elif self.shiftPressed and event.button() == Qt.RightButton:
            iface.mapCanvas().setExtent(QgsRectangle(self.topLeft, self.bottomRight))

            self.drawRect = False
            self.topLeft = None
            self.bottomRight = None
            self.rightPressed = False

            self.mLayer.triggerRepaint()

    def keyPressEvent(self, event):
        """
        Additional edit options by pressing and holding keys:
        HOLD CTRL: enable new options on MouseClick, see canvasPressEvent
        ESC: quit edit mode
        HOLD SHIFT: enable multiple vertex selection
        R: removes the existing single vertex selection

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

        elif event.key() == Qt.Key_R:
            if self.firstFound:
                self.__removeFirstFound()

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

            for action in self.mLayer.graphToolBar.actions():
                if "Delete Vertex" in action.whatsThis():
                    action.setEnabled(False)

            iface.mapCanvas().scene().removeItem(self.firstMarker)
            del self.firstMarker

    def isEditTool(self):
        return True
