#  This file is part of the OGDF plugin.
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

from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QComboBox, QToolButton, QMenu, QAction, QApplication
from qgis.PyQt.QtCore import pyqtSignal, Qt, QPoint

from qgis.gui import QgsMapTool
from qgis.utils import iface
from qgis.core import QgsCoordinateTransform

from ...models.QgsGraphLayer import QgsGraphLayer


class QgsVertexPickerMapTool(QgsMapTool):
    """
    QgsMapTool to select a vertex on a graph layer
    """

    vertexSelected = pyqtSignal(int)
    canceled = pyqtSignal()

    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer

        self.selectedVertexIdx = None

    def activate(self):
        super().activate()
        self.selectedVertexIdx = None

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

        vertexIdx = self.layer.mGraph.findVertex(clickPosition, iface.mapCanvas().mapUnitsPerPixel() * 4)

        if vertexIdx >= 0:
            self.selectedVertexIdx = vertexIdx
            self.vertexSelected.emit(vertexIdx)

    def keyReleaseEvent(self, event):
        # cancel selection
        if event.key() == Qt.Key_Escape:
            self.canceled.emit()

    def getSelectedVertexIdx(self):
        return self.selectedVertexIdx


class QgsGraphVertexPickerWidget(QWidget):
    """
    Shows a combobox with all available graph vertices.
    """

    vertexChanged = pyqtSignal()
    graphLayerChanged = pyqtSignal()
    graphChanged = pyqtSignal()
    toggleDialogVisibility = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(QgsGraphVertexPickerWidget, self).__init__(parent)

        self.graph = None
        self.graphLayer = None

        self.mapTool = None
        self.oldMapTool = None

        # add a combobox
        layout = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.comboBox.currentIndexChanged.connect(self.vertexChanged)
        layout.addWidget(self.comboBox)

        # set up tool button menu
        self.toolButton = QToolButton()
        self.toolButton.setText("...")
        self.selectOnCanvasAction = QAction(self.tr("Select vertex on canvas"))
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

    def _updateVertices(self):
        """
        Updates all combobox vertex items
        :return:
        """
        self.comboBox.clear()
        # graph layer is prioritized
        graph = self.graphLayer.getGraph() if self.graphLayer is not None else self.graph
        if graph is not None:
            for vertexIdx in range(graph.vertexCount()):
                vertex = graph.vertex(vertexIdx).point()
                self.comboBox.addItem("Vertex ID: {} [Point({})]".format(
                    graph.vertex(vertexIdx).id(), vertex.toString(2)), graph.vertex(vertexIdx).id())

    def _selectOnCanvas(self):
        """
        Enable vertex select on map canvas
        :return:
        """
        self.mapTool = QgsVertexPickerMapTool(iface.mapCanvas(), self.graphLayer)

        self.oldMapTool = iface.mapCanvas().mapTool()
        iface.mapCanvas().setMapTool(self.mapTool)

        self.mapTool.vertexSelected.connect(self._vertexSelected)
        self.mapTool.canceled.connect(self._deactivateMapTool)

        self.toggleDialogVisibility.emit(False)

    def _vertexSelected(self, vertexIdx):
        """
        Set selected vertex in combobox
        :param vertexId:
        :return:
        """
        self.comboBox.setCurrentIndex(self.comboBox.findData(vertexIdx))
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
        Sets graph without possibility to select vertex on canvas
        :param graph:
        :return:
        """
        self.graph = graph
        self._updateVertices()
        self.graphChanged.emit()

    def getGraph(self):
        return self.graph

    def setGraphLayer(self, graphLayer):
        """
        Sets a graph layer. It allows to select a vertex on the canvas.
        If graph is also set, the graph layer will be prioritized.
        :param graphLayer:
        :return:
        """
        if graphLayer is not None and graphLayer.pluginLayerType() != QgsGraphLayer.LAYER_TYPE:
            raise TypeError("Not a graph layer")
        self.graphLayer = graphLayer
        self._updateVertices()

        # show tool button
        self.toolButton.setVisible(self.graphLayer is not None)
        self.graphLayerChanged.emit()

    def getGraphLayer(self):
        return self.graphLayer

    def getVertex(self):
        """
        :return: Returns vertex id of selected vertex in graph
        """
        return self.comboBox.currentData()

