from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QComboBox
from qgis.PyQt.QtCore import pyqtSignal

from ...models.QgsGraphLayer import QgsGraphLayer


class QgsGraphVertexPickerWidget(QWidget):
    """
    Shows a combobox with all available graph vertices.
    """

    vertexChanged = pyqtSignal()
    graphLayerChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(QgsGraphVertexPickerWidget, self).__init__(parent)

        self.graphLayer = None

        # add a combobox
        layout = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.comboBox.currentIndexChanged.connect(self.vertexChanged)
        layout.addWidget(self.comboBox)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _updateVertices(self):
        """
        Updates all combobox vertex items
        :return:
        """
        self.comboBox.clear()
        if self.graphLayer and self.graphLayer.getGraph():
            graph = self.graphLayer.getGraph()
            for vertexId in range(graph.vertexCount()):
                vertex = graph.vertex(vertexId).point()
                self.comboBox.addItem("Vertex ID: {} [Point({})]".format(
                    vertexId, vertex.toString(2)), vertexId)

    def setGraphLayer(self, graphLayer):
        if graphLayer is not None:
            if graphLayer.pluginLayerType() != QgsGraphLayer.LAYER_TYPE:
                raise TypeError("Not a graph layer")
            self.graphLayer = graphLayer
            self._updateVertices()
            self.graphLayerChanged.emit()

    def getGraphLayer(self):
        return self.graphLayer

    def getVertex(self):
        """
        :return: Returns vertex id of selected vertex in graph
        """
        return self.comboBox.currentData()

