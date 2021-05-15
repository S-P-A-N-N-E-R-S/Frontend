from qgis.core import QgsVectorLayer


class QgsGraphLayer(QgsVectorLayer):
    # this class only exists to add a graph to the vector layer

    def setGraph(self, graph):
        self.graph = graph

    def getGraph(self):
        return self.graph