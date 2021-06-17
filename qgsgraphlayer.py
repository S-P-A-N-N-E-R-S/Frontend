from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import *
from qgis.gui import QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QVariant, QPointF
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtXml import *

import traceback
from collections import defaultdict

class QgsGraphFeatureIterator(QgsAbstractFeatureIterator):

    def __init__(self, source, request=QgsFeatureRequest()):
        super().__init__(request)

        self._request = request
        self._source = source
        self._index = 0

        # TODO: possible crs transformation

    def fetchFeature(self, feat):
        """Gets actually looked at feature. Increases feature index for next fetchFeature.

        Args:
            feat ([type]): Feature to be filled with information from fetched feature.

        Returns:
            [type]: True if successfull
        """
        # TODO this is a very simplified version of fetchFeature (e.g. request completely ignored -> necessary?)
        if self._index == len(self._source._features):
            return False
        
        try:
            _feat = self._source._features[self._index]
            feat.setGeometry(_feat.geometry())
            feat.setFields(_feat.fields())
            feat.setAttributes(_feat.attributes())
            feat.setValid(_feat.isValid())
            feat.setId(_feat.id())

            self._index += 1

            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):        
        if self._index + 1 < len(self._source._features):
            self._index += 1
        
        return self._source._features[self._index]

    def rewind(self):
        self._index = 0
        return True

    def close(self):
        self._index = -1
        return True


class QgsGraphFeatureSource(QgsAbstractFeatureSource):

    def __init__(self, provider):
        super(QgsGraphFeatureSource).__init__()

        self._provider = provider
        self._features = provider._features

    def getFeatures(self, request):
        return QgsFeatureIterator(QgsGraphFeatureIterator(self, request))


class QgsGraphDataProvider(QgsVectorDataProvider):
    """Data provider for GraphLayer

    Args:
        QgsVectorDataProvider ([type]): Extends QgsVectorDataProvider to be able to store fields and features.
                                        Makes GraphLayer storeable / exportable (TODO)
    """

    nextFeatId = 1

    @classmethod
    def providerKey(self):
        return "graphprovider"

    @classmethod
    def description(self):
        return "DataProvider for QgsGraphLayer"

    @classmethod
    def createProvider(self, uri='', providerOptions=QgsDataProvider.ProviderOptions(), flags=QgsDataProvider.ReadFlags()):
        return QgsGraphDataProvider(uri, providerOptions, flags)

    
    def __init__(self, uri='', providerOptions=QgsDataProvider.ProviderOptions(), flags=QgsDataProvider.ReadFlags()):
        super().__init__(uri)

        tempLayer = QgsVectorLayer(uri, "tmp", "memory")
        self.mCrs = QgsProject.instance().crs()
        
        self._uri = uri
        self._providerOptions = providerOptions
        self._flags = flags
        self._features = []
        self._fields = tempLayer.fields()
        self._extent = QgsRectangle()
        self._subsetString = ''
        self._featureCount = 0

        self._points = True

        # if 'index=yes' in self._uri:
        #     self.createSpatialIndex()

    def isValid(self):
        return True

    def setDataSourceUri(self, uri):
        self._uri = uri

    def dataSourceUri(self, expandAuthConfig=True):
        return self._uri

    def setCrs(self, crs):
        self.mCrs = crs

    def crs(self):
        if self.mCrs == None:
            return QgsCoordinateReferenceSystem()

        return self.mCrs

    def featureSource(self):
        return QgsGraphFeatureSource(self)

    def getFeatures(self, request=QgsFeatureRequest()):
        # return self._features
        return QgsFeatureIterator(QgsGraphFeatureIterator(self.featureSource(), request))

    def featureCount(self):
        return self._featureCount

    def fields(self):
        return self._fields

    def addFeature(self, feat, flags=None):
        # TODO check for valid feature

        self._features.append(feat)
        self.nextFeatId += 1
        self._featureCount += 1

        # if self._spatialindex is not None:
        #     self._spatialindex.insertFeatue(feat)

        return True

    def deleteFeature(self, id):
        try:
            del self._features[id]
            self._featureCount -= 1
        
            return True
        except Exception as e:
            # probably index out of bound
            return False

    def addAttributes(self, attrs):
        # TODO check for valid attribute types defined by fields
        for field in attrs:
            self._fields.append(field)
            self._uri += "&field=" + field.displayName() + ":" + field.typeName()

        return True

    def createSpatialIndex(self):
        # TODO?
        pass

    def capabilities(self):
        # how many capabilities to return?
        return QgsVectorDataProvider.AddFeature | QgsVectorDataProvider.AddAttributes

    def subsetString(self):
        return self._subsetString

    
    def extent(self):
        # TODO this update of extent maybe in addFeature?
        for feat in self._features.values():
            self._extent.combineExtentWith(feat.geometry().boundingBox())

        return self._extent

    def updateExtents(self):
        # TODO understand this
        self._extent.setMinimal()

    def name(self):
        return self.providerKey()

    def setGeometryToPoint(self, points):
        self._points = points

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
        painter.setBrush(QColor('red'))
        painter.setFont(QFont("arial", 5))

        # if isinstance(self.mGraph, PGGraph):
        if isinstance(self.mGraph, QgsGraph):
            try:
                # used to convert map coordinates to canvas coordinates
                converter = QgsVertexMarker(iface.mapCanvas())
                
                max = self.mGraph.edgeCount()
                if max < self.mGraph.vertexCount():
                    max = self.mGraph.vertexCount()

                for id in range(max):
                    # draw vertices
                    if id < self.mGraph.vertexCount():
                        point = converter.toCanvasCoordinates(self.mGraph.vertex(id).point())
                        
                        painter.setPen(QColor('black'))
                        painter.drawEllipse(point, 2.0, 2.0)

                    # draw edges                    
                    if id < self.mGraph.edgeCount():
                        edge = self.mGraph.edge(id)
                        toPoint = converter.toCanvasCoordinates(self.mGraph.vertex(edge.toVertex()).point())
                        fromPoint = converter.toCanvasCoordinates(self.mGraph.vertex(edge.fromVertex()).point())

                        painter.setPen(QColor('black'))
                        painter.drawLine(toPoint, fromPoint)
                        
                        # add text with edgeCost at line mid point
                        midPoint = QPointF(0.5 * toPoint.x() + 0.5 * fromPoint.x(), 0.5 * toPoint.y() + 0.5 * fromPoint.y())
                        painter.drawText(midPoint, "1")

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
        
        self.mName = name
        self.mGraph = QgsGraph()
        # self.mGraph = PGGraph()

        self.mLayerType = QgsGraphLayerType()

        self.mDataProvider = QgsGraphDataProvider("Point")
        self.mFields = QgsFields()

        self.mCrs = QgsProject.instance().crs()
        self.__crsUri = "crs=" + self.mCrs.authid()
        self.mDataProvider.setCrs(self.mCrs)

        self.setDataSource(self.mDataProvider.dataSourceUri(), self.mName, self.mDataProvider.providerKey(), QgsDataProvider.ProviderOptions())

    def dataProvider(self):
        # TODO: issue with DB Manager plugin
        return self.mDataProvider

    def fields(self):
        return self.mFields

    def setCrs(self, crs):
        self.mCrs = crs
        self.__crsUri = "crs=" + crs.authid()
        self.mDataProvider.setCrs(crs)

    def createMapRenderer(self, rendererContext):
        return QgsGraphLayerRenderer(self.id(), rendererContext, self.mGraph)

    def setTransformContext(self, ct):
        pass 

    def setGraph(self, graph):
        # if isinstance(graph, PGGraph):
        if isinstance(graph, QgsGraph):
            self.mGraph = graph

            if self.mGraph.edgeCount() != 0:
                
                self.mDataProvider.setGeometryToPoint(False)
                self.mDataProvider.setDataSourceUri("LineString?" + self.__crsUri)

                edgeIdField = QgsField("edgeId", QVariant.Int, "integer")
                fromVertexField = QgsField("fromVertex", QVariant.Double, "double")
                toVertexField = QgsField("toVertex", QVariant.Double, "double")
                # costField = QgsField("edgeCost", QVariant.Double, "double")
                
                self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField])
                # self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField, costField])
                
                # self.updateFields()
                self.mFields.append(edgeIdField)
                self.mFields.append(fromVertexField)
                self.mFields.append(toVertexField)
                # self.mFields.append(costField)
                
                for edgeId in range(self.mGraph.edgeCount()):
                    edge = self.mGraph.edge(edgeId)

                    feat = QgsFeature()
                    fromVertex = self.mGraph.vertex(edge.fromVertex()).point()
                    toVertex = self.mGraph.vertex(edge.toVertex()).point()
                    feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                    feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex()])
                    # feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex(), self.mGraph.costOfEdge(edgeId)])

                    self.mDataProvider.addFeature(feat)

            else:
                self.mDataProvider.setGeometryToPoint(True)
                self.mDataProvider.setDataSourceUri("Point?" + self.__crsUri)

                vertexIdField = QgsField("vertexId", QVariant.Int, "integer")
                xField = QgsField("x", QVariant.Double, "double")
                yField = QgsField("y", QVariant.Double, "double")

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
        # self.mGraph = PGGraph()

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
                # self.mGraph.addEdge(int(elem.attribute("fromVertex")), int(elem.attribute("toVertex"))) # add cost at later state

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
                # edgeNode.setAttribute("edgeCost", self.mGraph.costOfEdge(edgeId))
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
