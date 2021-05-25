from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import (QgsMapLayerRenderer, QgsPluginLayer,
                       QgsPluginLayerType, QgsPointXY)

from qgis.PyQt.QtGui import QColor, QPen
from qgis.PyQt.QtXml import *


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

        # set painter scale (and mirror at y-axis)
        pixelMap = self.renderContext().mapToPixel()
        scale = 1 / pixelMap.mapUnitsPerPixel()
        painter.scale(-scale, scale)

        # set painter rotation
        painter.rotate(180)

        # set painter to midpoint of extent
        extent = self.renderContext().extent()
        painter.translate(extent.xMaximum(), extent.yMinimum())
        
        if isinstance(self.mGraph, QgsGraph):
            try:
                if self.mGraph.edgeCount() == 0:
                    # draw only points if no edges exist in graph
                    for vertexId in range(self.mGraph.vertexCount()):
                        point = self.mGraph.vertex(vertexId).point().toQPointF()

                        painter.drawPoint(point)
                else:      
                    # draw points and edges of graph  
                    for edgeId in range(self.mGraph.edgeCount()):
                        # get edge and its vertices
                        edge = self.mGraph.edge(edgeId)
                        toPoint = self.mGraph.vertex(edge.toVertex()).point().toQPointF()
                        fromPoint = self.mGraph.vertex(edge.fromVertex()).point().toQPointF()

                        # draw vertices (TODO: probably drawn multiple times in this loop)
                        # TODO: when using QT methods to draw: 0,0 is top left, and units have to be adapted
                        painter.drawPoint(toPoint)
                        painter.drawPoint(fromPoint)

                        # draw edges
                        painter.drawLine(toPoint, fromPoint)

                        # comment as to why using QT to draw: RubberBand draws BoundingBox of Points, 
                        # QgsVertexMarker crashes my QGIS (don't know why, to be investigated)
                        # QgsFeatureRenderer can only be used when adding Features to QgsGraphLayer (seems to be too much effort/overhead for drawing?)

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

    def __init__(self, name="QgsGraphLayer"):
        super().__init__(QgsGraphLayer.LAYER_TYPE, name)
        self.setValid(True)
        self.mGraph = QgsGraph()

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
            node (QDomNode): XML Node for layer
            context ([type]): [description]
        """
        # start with empty QgsGraph
        self.mGraph = QgsGraph()

        # find graph node in xml
        graphNode = node.firstChild()
        while graphNode.nodeName() != "graph":
            graphNode = graphNode.nextSibling()
            
        verticesNode = graphNode.firstChild()
        vertexNodes = verticesNode.childNodes()

        # get vertex information and add them to mGraph
        for vertexId in range(vertexNodes.length()):
            if vertexNodes.at(vertexId).isElement():
                elem = vertexNodes.at(vertexId).toElement()
                self.mGraph.addVertex(QgsPointXY(float(elem.attribute("x")), float(elem.attribute("y"))))

        edgesNode = verticesNode.nextSibling()
        edgeNodes = edgesNode.childNodes()

        # get edge information and add them to mGraph
        strat = QgsNetworkDistanceStrategy()
        for edgeId in range(edgeNodes.length()):
            if edgeNodes.at(edgeId).isElement():
                elem = edgeNodes.at(edgeId).toElement()
                self.mGraph.addEdge(int(elem.attribute("fromVertex")), int(elem.attribute("toVertex")), [strat])

        return True


    def writeXml(self, node, doc, context):
        """Write the mGraph (QgsGraph and its subclasses) to the project file.
            To be done after mGraph has been set.

        Args:
            node (QDomNode): XML Node for layer
            doc (QDomDocument): XML Project File
            context ([type]): [description]
        """

        if node.isElement():
            node.toElement().setAttribute("type", "plugin")
            node.toElement().setAttribute("name", "graph")

        # graphNode saves all graphData
        graphNode = doc.createElement("graph")
        node.appendChild(graphNode)

        # vertexNode saves all vertices with tis coordinates
        verticesNode = doc.createElement("vertices")
        graphNode.appendChild(verticesNode)

        # edgeNode saves all edges with its vertices ids
        # TODO: also save cost information stored in PGGraph (merge necessary beforehand)
        edgesNode = doc.createElement("edges")
        graphNode.appendChild(edgesNode)

        # store vertices
        for vertexId in range(self.mGraph.vertexCount()):
            # QgsPointXY TODO: support for QgsPointZ?
            point = self.mGraph.vertex(vertexId).point()

            # store vertex information (coordinates have to be string to avoid implicit conversion to int)
            self.__writeVertexXML(doc, verticesNode, vertexId, point.x(), point.y())

        if self.mGraph.edgeCount() != 0:
            # store edges if available
            
            for edgeId in range(self.mGraph.edgeCount()):
                edge = self.mGraph.edge(edgeId)
                
                fromVertex = edge.fromVertex()
                toVertex = edge.toVertex()

                # store edge information (TODO: add cost)
                edgeNode = doc.createElement("edge")
                edgeNode.setAttribute("id", edgeId)
                edgeNode.setAttribute("toVertex", toVertex)
                edgeNode.setAttribute("fromVertex", fromVertex)
                edgesNode.appendChild(edgeNode)
                    
        return True

    def __writeVertexXML(self, doc, node, id, x, y):
        """Writes given vertex information to XML.

        Args:
            doc (QDomDocument): XML Project File
            node (QDomNode): vertices node to append new vertex node to
            id (int): vertexId
            x (float): vertex x-coordinate
            y (float): vertex y-coordinate
        """
        vertexNode = doc.createElement("vertex")
        vertexNode.setAttribute("id", id)
        # store coordinates as strings to avoid implicite conversion from float to int
        vertexNode.setAttribute("x", str(x))
        vertexNode.setAttribute("y", str(y))
        node.appendChild(vertexNode)


class QgsGraphLayerType(QgsPluginLayerType):
    """When loading a project containing a QgsGraphLayer, a factory class is needed.

    Args:
        QgsPluginLayerType ([type]): [description]
    """
    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE)

    def createLayer(self):
        return QgsGraphLayer()
