#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Dennis Benz, Julian Wittker
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

from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QComboBox, QToolButton, QMenu, QAction
from qgis.PyQt.QtCore import pyqtSignal, Qt, QPoint

from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.utils import iface
from qgis.core import QgsCoordinateTransform, QgsProject

from ...models.graphLayer import GraphLayer


class EdgePickerMapTool(QgsMapTool):
    """
    QgsMapTool to select an edge on a graph layer
    """

    edgeSelected = pyqtSignal(int)
    canceled = pyqtSignal()

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer

        self._firstVertex = None
        self._secondVertex = None

        self._firstVertexMarker = None

        self.selectedEdgeId = None

    def activate(self):
        super().activate()
        self._firstVertex = None
        self._secondVertex = None
        self.selectedEdgeId = None
        self._removeMarker()

    def canvasReleaseEvent(self, event):
        """
        Select a vertex on canvas
        :param event: click release event
        :return:
        """
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        converter = iface.mapCanvas().getCoordinateTransform()
        clickPosition = converter.toMapCoordinates(clickPosition)

        if QgsProject.instance().crs().authid() != self.layer.mGraph.crs.authid():
            clickPosition = self.layer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        vertexId = self.layer.mGraph.findVertex(clickPosition)

        if vertexId >= 0:
            if self._firstVertex is None:
                # select first edge vertex
                self._firstVertex = vertexId
                self._firstVertexMarker = QgsVertexMarker(iface.mapCanvas())
                self._firstVertexMarker.setIconType(QgsVertexMarker.ICON_BOX)

                foundPosition = self.layer.mGraph.vertex(self._firstVertex).point()
                if QgsProject.instance().crs().authid() != self.layer.mGraph.crs.authid():
                    self._firstVertexMarker.setCenter(self.layer.mTransform.transform(foundPosition))
                else:
                    self._firstVertexMarker.setCenter(foundPosition)
            else:
                # select second vertex
                self._secondVertex = vertexId
                edgeId = self.layer.mGraph.hasEdge(self._firstVertex, self._secondVertex)
                if edgeId >= 0:
                    self.selectedEdgeIdx = edgeId
                    self.edgeSelected.emit(edgeId)
                # remove first vertex
                self._firstVertex = None
                # remove marker from canvas
                self._removeMarker()

    def keyReleaseEvent(self, event):
        # cancel selection
        if event.key() == Qt.Key_Escape:
            # remove marker
            self._removeMarker()

            # remove vertex selections
            self._firstVertex = None
            self._secondVertex = None
            self.canceled.emit()

    def _removeMarker(self):
        """
        Removes the first vertex marker
        :return:
        """
        if self._firstVertexMarker is not None:
            iface.mapCanvas().scene().removeItem(self._firstVertexMarker)
            self._firstVertexMarker = None

    def getSelectedEdgeIdx(self):
        return self.selectedEdgeIdx


class GraphEdgePickerWidget(QWidget):
    """
    Shows a combobox with all available graph edges.
    """

    edgeChanged = pyqtSignal()
    graphLayerChanged = pyqtSignal()
    graphChanged = pyqtSignal()
    toggleDialogVisibility = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.graph = None
        self.graphLayer = None

        self.mapTool = None
        self.oldMapTool = None

        # add a combobox
        layout = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.comboBox.currentIndexChanged.connect(self.edgeChanged)
        layout.addWidget(self.comboBox)

        # set up tool button menu
        self.toolButton = QToolButton()
        self.toolButton.setText("...")
        self.selectOnCanvasAction = QAction(self.tr("Select edge on canvas"))
        self.selectOnCanvasAction.triggered.connect(self._selectOnCanvas)

        menu = QMenu()
        menu.addAction(self.selectOnCanvasAction)

        self.toolButton.setMenu(menu)
        self.toolButton.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(self.toolButton)

        # hide tool button
        self.toolButton.hide()

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _updateEdges(self):
        """
        Updates all combobox edge items
        :return:
        """
        self.comboBox.clear()
        # graph layer is prioritized
        graph = self.graphLayer.getGraph() if self.graphLayer is not None else self.graph
        if graph is not None:
            for edgeId in graph.edges():
                edge = graph.edge(edgeId)
                fromVertex = graph.vertex(edge.fromVertex()).point()
                toVertex = graph.vertex(edge.toVertex()).point()
                self.comboBox.addItem("Edge ID: {} [FromPoint({}), ToPoint({})]".format(
                    edgeId, fromVertex.toString(2), toVertex.toString(2)), edgeId)

    def _selectOnCanvas(self):
        """
        Enable edge select on map canvas
        :return:
        """
        self.mapTool = EdgePickerMapTool(iface.mapCanvas(), self.graphLayer)

        self.oldMapTool = iface.mapCanvas().mapTool()
        iface.mapCanvas().setMapTool(self.mapTool)

        self.mapTool.edgeSelected.connect(self._edgeSelected)
        self.mapTool.canceled.connect(self._deactivateMapTool)

        self.toggleDialogVisibility.emit(False)

    def _edgeSelected(self, edgeIdx):
        """
        Set selected edge in combobox
        :param edgeId:
        :return:
        """
        self.comboBox.setCurrentIndex(self.comboBox.findData(edgeIdx))
        self._deactivateMapTool()

    def _deactivateMapTool(self):
        """
        Removes map tool
        :return:
        """
        iface.mapCanvas().setMapTool(self.oldMapTool)
        self.oldMapTool = None
        self.mapTool = None

        self.toggleDialogVisibility.emit(True)

    def clear(self):
        """
        Removes graph, graph layer and list elements
        :return:
        """
        self.graph = None
        self.graphLayer = None
        self.comboBox.clear()
        self.toolButton.hide()

    def setGraph(self, graph):
        """
        Sets graph without possibility to select an edge on canvas
        :param graph:
        :return:
        """
        self.graph = graph
        self._updateEdges()
        self.graphChanged.emit()

    def getGraph(self):
        return self.graph

    def setGraphLayer(self, graphLayer):
        """
        Sets a graph layer. It allows to select an edge on the canvas.
        If graph is also set, the graph layer will be prioritized.
        :param graphLayer:
        :return:
        """
        if graphLayer is not None and graphLayer.pluginLayerType() != GraphLayer.LAYER_TYPE:
            raise TypeError("Not a graph layer")
        self.graphLayer = graphLayer
        self._updateEdges()

        # show tool button
        self.toolButton.setVisible(self.graphLayer is not None)
        self.graphLayerChanged.emit()

    def getGraphLayer(self):
        return self.graphLayer

    def getEdge(self):
        """
        :return: Returns edge id of selected edge in graph
        """
        return self.comboBox.currentData()
