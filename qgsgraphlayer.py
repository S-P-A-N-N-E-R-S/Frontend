from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import (QgsMapLayerRenderer, QgsPluginLayer,
                       QgsPluginLayerType, QgsPointXY,
                       QgsVectorDataProvider, QgsCoordinateReferenceSystem,
                       QgsField, QgsFeature, QgsFields,
                       QgsPoint, QgsGeometry,
                       QgsFeatureSink, QgsFeatureSource)
from qgis.gui import QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtXml import *

class QgsGraphDataProvider(QgsVectorDataProvider):

    def __init__(self):
        super().__init__()

        self.mName = "memory"
        self.mCrs = None

    def name(self):
        return self.mName

    def description(self):
        return "DataProvider for QgsGraphLayer"

    def isValid(self):
        return True
    
    def setCrs(self, crs):
        self.mCrs = crs

    def crs(self):
        if self.mCrs == None:
            return QgsCoordinateReferenceSystem()

        return self.mCrs

    # def fields(self):
    #     return self.getFeatures()

    def featureCount(self):
        return 0

class QgsGraphLayerRenderer(QgsMapLayerRenderer):

    def __init__(self, layerId, rendererContext, graph):
        super().__init__(layerId, rendererContext)

        try:
            self.layerId = layerId
            self.rendererContext = rendererContext
            
            self.mGraph = graph

        except Exception as err:
            print(err)
    
    def render(self):
        return self.__drawGraph()

    def __drawGraph(self):

        painter = self.renderContext().painter()
        painter.setPen(QColor('black'))

        if isinstance(self.mGraph, QgsGraph):
            try:
                # used to convert map coordinates to canvas coordinates
                converter = QgsVertexMarker(iface.mapCanvas())

                if self.mGraph.edgeCount() == 0:
                    # draw only points if no edges exist in graph
                    for vertexId in range(self.mGraph.vertexCount()):

                        point = converter.toCanvasCoordinates(self.mGraph.vertex(vertexId).point())

                        painter.drawPoint(point)

                else:      
                    # draw points and edges of graph  
                    for edgeId in range(self.mGraph.edgeCount()):
                        # get edge and its vertices
                        edge = self.mGraph.edge(edgeId)
                        toPoint = converter.toCanvasCoordinates(self.mGraph.vertex(edge.toVertex()).point())
                        fromPoint = converter.toCanvasCoordinates(self.mGraph.vertex(edge.fromVertex()).point())

                        # draw vertices (TODO: probably drawn multiple times in this loop)
                        painter.setPen(QColor('black'))
                        painter.drawPoint(toPoint)
                        painter.drawPoint(fromPoint)

                        # draw edges
                        painter.setPen(QColor('green'))
                        painter.drawLine(toPoint, fromPoint)

                iface.mapCanvas().scene().removeItem(converter)
            except Exception as err:
                print(err)
        else:
            print("mGraph NOT found")

        painter.restore()

        return True

class QgsGraphLayer(QgsPluginLayer, QgsFeatureSink, QgsFeatureSource):
    """Subclass of PluginLayer to render a QgsGraph (and its subclasses) 
        and to save a QgsGraph (and its subclasses) to the project file.

    Args:
        QgsPluginLayer ([type]): [description]
    """

    LAYER_TYPE="graph"
    LAYER_PROPERTY = "graph_layer_type"

    def __init__(self, name="QgsGraphLayer"):
        super().__init__(QgsGraphLayer.LAYER_TYPE, name)
        self.setValid(True)
        self.mGraph = QgsGraph()

        self.mLayerType = QgsGraphLayerType()

        self.mDataProvider = QgsGraphDataProvider()
        self.mFields = QgsFields()

    def dataProvider(self):
        return self.mDataProvider

    def fields(self):
        return self.mFields

    def setCrs(self, crs):
        self.mDataProvider.setCrs(crs)

    def createMapRenderer(self, rendererContext):
        return QgsGraphLayerRenderer(self.id(), rendererContext, self.mGraph)

    def setTransformContext(self, ct):
        pass 

    def setGraph(self, graph):
        if isinstance(graph, QgsGraph):
            self.mGraph = graph

            if self.mGraph.edgeCount() != 0:
                
                edgeIdField = QgsField("EdgeId", QVariant.Int)
                fromVertexField = QgsField("fromVertex", QVariant.Double)
                toVertexField = QgsField("toVertex", QVariant.Double)
                
                self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField])
                
                # self.updateFields()
                self.mFields.append(edgeIdField)
                self.mFields.append(fromVertexField)
                self.mFields.append(toVertexField)
                
                for edgeId in range(self.mGraph.edgeCount()):
                    edge = self.mGraph.edge(edgeId)

                    feat = QgsFeature()
                    fromVertex = edge.fromVertex().point()
                    toVertex = edge.toVertex().point()
                    feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                    feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex()])
                    self.mDataProvider.addFeature(feat)

            else:
                vertexIdField = QgsField("VertexId", QVariant.Int)
                xField = QgsField("x", QVariant.Double)
                yField = QgsField("y", QVariant.Double)

                self.mDataProvider.addAttributes([vertexIdField, xField, yField])
                
                # self.updateFields()
                self.mFields.append(vertexIdField)
                self.mFields.append(xField)
                self.mFields.append(yField)

                for vertexId in range(self.mGraph.vertexCount()):
                    vertex = self.mGraph.vertex(vertexId).point()

                    feat = QgsFeature()
                    feat.setGeometry(QgsGeometry.fromPointXY(vertex))

                    feat.setAttributes([vertexId, vertex.x(), vertex.y()])
                    self.mDataProvider.addFeature(feat)


    def getGraph(self):
        return self.mGraph

    def readXml(self, node, context):
        """Read QgsGraph (and its subclasses) from the project file.

        Args:
            node (QDomNode): XML Node for layer
            context ([type]): [description]
        """
        self.setLayerType(QgsGraphLayer.LAYER_TYPE)

        # start with empty QgsGraph
        self.mGraph = QgsGraph()

        # find graph node in xml
        graphNode = node.firstChild()
        while graphNode.nodeName() != "graphData":
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
            node.toElement().setAttribute("name", QgsGraphLayer.LAYER_TYPE)

        # graphNode saves all graphData
        graphNode = doc.createElement("graphData")
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

    def setLayerType(self, layerType):
        self.mLayerType = layerType
        self.setCustomProperty(QgsGraphLayer.LAYER_PROPERTY, self.mLayerType)

class QgsGraphLayerType(QgsPluginLayerType):
    """When loading a project containing a QgsGraphLayer, a factory class is needed.

    Args:
        QgsPluginLayerType ([type]): [description]
    """
    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE)

    def createLayer(self):
        return QgsGraphLayer()
