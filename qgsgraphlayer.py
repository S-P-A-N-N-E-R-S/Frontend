from qgis.analysis import QgsGraph
from qgis.core import (QgsMapLayerRenderer, QgsPluginLayer,
                       QgsPluginLayerType, QgsSymbol, QgsWkbTypes)

from qgis.PyQt.QtGui import QColor, QPen
from qgis.PyQt.QtCore import QPointF, QPoint


class QgsGraphLayerRenderer(QgsMapLayerRenderer):

    def __init__(self, layerId, rendererContext, graph):
        super().__init__(layerId, rendererContext)

        try:
            self.layerId = layerId
            self.rendererContext = rendererContext
            
            self.mGraph = graph
            
            self.pen = QPen()
            self.pen.setColor(QColor('black'))
            self.pen.setWidth(3)
            self.pen.setCosmetic(True)

        except Exception as err:
            print(err)
    
    def render(self):
        return self.__drawGraph()

    def __drawGraph(self):
        painter = self.renderContext().painter()
        painter.setPen(self.pen)
        painter.save()

        if isinstance(self.mGraph, QgsGraph):
            try:
                for edgeId in range(self.mGraph.edgeCount()):
                    # get edge and its vertices
                    edge = self.mGraph.edge(edgeId)
                    toPoint = self.mGraph.vertex(edge.toVertex()).point().toQPointF()
                    fromPoint = self.mGraph.vertex(edge.fromVertex()).point().toQPointF()

                    # draw vertices (TODO: probably drawn multiple times in this loop)
                    # TODO: when using QT methods to draw: 0,0 is top left, and units have to be adapted
                    painter.drawPoint(toPoint)
                    painter.drawPoint(fromPoint)

                    #draw edges
                    painter.drawLine(toPoint, fromPoint)

            except Exception as err:
                print(err)
        else:
            print("mGraph NOT found")

        painter.restore()

        return True

class QgsGraphLayer(QgsPluginLayer):
    """Subclass of PluginLayer to render a QgsGraph (and its subclasses) 
        and to save a QgsGraph (and its subclasses) to the project file.

    Args:
        QgsPluginLayer ([type]): [description]
    """

    LAYER_TYPE="graph"

    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE, "QgsGraph_Layer")
        self.setValid(True)
        self.mGraph = []

    def createMapRenderer(self, rendererContext):
        return QgsGraphLayerRenderer(self.id(), rendererContext, self.mGraph)

    def setTransformContext(self, ct):
        pass 

    def setGraph(self, graph):
        self.mGraph = graph

    def getGraph(self):
        return self.mGraph

    def readXml(self, node, context):
        """Read QgsGraph (and its subclasses) from the project file.

        Args:
            node ([type]): [description]
            context ([type]): [description]
        """
        pass

    def writeXml(self, node, doc, context):
        """Write the mGraph (QgsGraph and its subclasses) to the project file.
            To be done after mGraph has been set.

        Args:
            node ([type]): [description]
            doc ([type]): [description]
            context ([type]): [description]
        """
        pass

class QgsGraphLayerType(QgsPluginLayerType):
    """When loading a project containing a QgsGraphLayer, a factory class is needed.

    Args:
        QgsPluginLayerType ([type]): [description]
    """
    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE)

    def createLayer(self):
        return QgsGraphLayer()
