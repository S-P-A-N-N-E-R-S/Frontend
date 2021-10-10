#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz
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

from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QComboBox, QToolButton, QMenu, QAction, QApplication
from qgis.PyQt.QtCore import pyqtSignal, Qt, QPoint

from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.utils import iface
from qgis.core import QgsCoordinateTransform

from ...models.QgsGraphLayer import QgsGraphLayer


class QgsEdgePickerMapTool(QgsMapTool):
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
        :param event:
        :return:
        """
        clickPosition = QPoint(event.pos().x(), event.pos().y())

        # used to convert canvas coordinates to map coordinates
        converter = iface.mapCanvas().getCoordinateTransform()
        clickPosition = converter.toMapCoordinates(clickPosition)
        clickPosition = self.layer.mTransform.transform(clickPosition, QgsCoordinateTransform.ReverseTransform)

        vertexIdx = self.layer.mGraph.findVertex(clickPosition, iface.mapCanvas().mapUnitsPerPixel() * 4)

        if vertexIdx >= 0:
            if self._firstVertex is None:
                # select first edge vertex
                self._firstVertex = vertexIdx
                self._firstVertexMarker = QgsVertexMarker(iface.mapCanvas())
                self._firstVertexMarker.setIconType(QgsVertexMarker.ICON_BOX)
                self._firstVertexMarker.setCenter(clickPosition)
            else:
                # select second vertex
                self._secondVertex = vertexIdx
                edgeIdx = self.layer.mGraph.hasEdge(self.layer.mGraph.vertex(self._firstVertex).id(), self.layer.mGRaph.vertex(self._secondVertex).id())
                if edgeIdx >= 0:
                    self.selectedEdgeIdx = edgeIdx
                    self.edgeSelected.emit(edgeIdx)
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


class QgsGraphEdgePickerWidget(QWidget):
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
            for edgeIdx in range(graph.edgeCount()):
                edge = graph.edge(edgeIdx)
                fromVertex = graph.vertex(graph.findVertexByID(edge.fromVertex())).point()
                toVertex = graph.vertex(graph.findVertexByID(edge.toVertex())).point()
                self.comboBox.addItem("Edge ID: {} [FromPoint({}), ToPoint({})]".format(
                    graph.edge(edgeIdx).id(), fromVertex.toString(2), toVertex.toString(2)), graph.edge(edgeIdx).id())

    def _selectOnCanvas(self):
        """
        Enable edge select on map canvas
        :return:
        """
        self.mapTool = QgsEdgePickerMapTool(iface.mapCanvas(), self.graphLayer)

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
        if graphLayer is not None and graphLayer.pluginLayerType() != QgsGraphLayer.LAYER_TYPE:
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

