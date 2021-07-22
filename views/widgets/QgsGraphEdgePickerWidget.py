from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QComboBox
from qgis.PyQt.QtCore import pyqtSignal

from ...models.QgsGraphLayer import QgsGraphLayer


class QgsGraphEdgePickerWidget(QWidget):
    """
    Shows a combobox with all available graph edges.
    """

    edgeChanged = pyqtSignal()
    graphLayerChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(QgsGraphEdgePickerWidget, self).__init__(parent)

        self.graphLayer = None

        # add a combobox
        layout = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.comboBox.currentIndexChanged.connect(self.edgeChanged)
        layout.addWidget(self.comboBox)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _updateEdges(self):
        """
        Updates all combobox edge items
        :return:
        """
        self.comboBox.clear()
        if self.graphLayer and self.graphLayer.getGraph():
            graph = self.graphLayer.getGraph()
            for edgeId in range(graph.edgeCount()):
                edge = graph.edge(edgeId)
                fromVertex = graph.vertex(edge.fromVertex()).point()
                toVertex = graph.vertex(edge.toVertex()).point()
                self.comboBox.addItem("Edge ID: {} [FromPoint({}), ToPoint({})]".format(
                    edgeId, fromVertex.toString(2), toVertex.toString(2)), edgeId)

    def setGraphLayer(self, graphLayer):
        if graphLayer is not None:
            if graphLayer.pluginLayerType() != QgsGraphLayer.LAYER_TYPE:
                raise TypeError("Not a graph layer")
            self.graphLayer = graphLayer
            self._updateEdges()
            self.graphLayerChanged.emit()

    def getGraphLayer(self):
        return self.graphLayer

    def getEdge(self):
        """
        :return: Returns edge id of selected edge in graph
        """
        return self.comboBox.currentData()

