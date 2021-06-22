from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import *
from qgis.gui import QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QVariant, QPointF
from qgis.PyQt.QtGui import QColor, QFont, QPainterPath
from qgis.PyQt.QtXml import *
from qgis.PyQt.QtWidgets import QDialog, QPushButton, QBoxLayout, QLabel, QFileDialog

import traceback, random, math

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
        self.mCRS = QgsProject.instance().crs()
        
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
        self.mCRS = crs

    def crs(self):
        if self.mCRS == None:
            return QgsProject.instance().crs()

        return self.mCRS

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
        for feat in self._features:
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

    def __init__(self, layerId, rendererContext, graph, crs, showEdgeText=True, showDirection=True, randomColor=QColor("red"), transform=QgsCoordinateTransform()):
        super().__init__(layerId, rendererContext)

        try:
            self.layerId = layerId
            self.rendererContext = rendererContext
            
            self.mGraph = graph

            self.mCRS = crs

            self.randomColor = randomColor

            self.mShowText = showEdgeText
            self.mShowDirection = showDirection

            self.mTransform = transform

        except Exception as err:
            print(err)

    def render(self):
        return self.__drawGraph()

    def __drawGraph(self):

        painter = self.renderContext().painter()
        painter.setPen(QColor('black'))
        painter.setBrush(self.randomColor)
        painter.setFont(QFont("arial", 5))
        # painter.setRenderHint(painter.Antialiasing)

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
                        point = self.mGraph.vertex(id).point()

                        if self.mTransform.isValid():
                            point = self.mTransform.transform(point)

                        point = converter.toCanvasCoordinates(point)
                        
                        painter.setPen(QColor('black'))
                        # don't draw border of vertices if graph has edges
                        if self.mGraph.edgeCount() != 0:
                            painter.setPen(self.randomColor)
                        painter.drawEllipse(point, 3.0, 3.0)

                    # draw edges                    
                    if id < self.mGraph.edgeCount():
                        edge = self.mGraph.edge(id)
                        toPoint = self.mGraph.vertex(edge.toVertex()).point()
                        fromPoint = self.mGraph.vertex(edge.fromVertex()).point()

                        if self.mTransform.isValid():
                            toPoint = self.mTransform.transform(toPoint)
                            fromPoint = self.mTransform.transform(fromPoint)

                        toPoint = converter.toCanvasCoordinates(toPoint)
                        fromPoint = converter.toCanvasCoordinates(fromPoint)

                        painter.setPen(QColor('black'))
                        painter.drawLine(toPoint, fromPoint)

                        if self.mShowDirection:
                            arrowHead = self.__createArrowHead(toPoint, fromPoint)
                            painter.drawPath(arrowHead)
                        
                        # add text with edgeCost at line mid point
                        if self.mShowText:
                            midPoint = QPointF(0.5 * toPoint.x() + 0.5 * fromPoint.x(), 0.5 * toPoint.y() + 0.5 * fromPoint.y())
                            painter.drawText(midPoint, "1")

                iface.mapCanvas().scene().removeItem(converter)
            except Exception as err:
                print(err)
        else:
            print("mGraph NOT found")

        painter.restore()

        return True

    def __createArrowHead(self, toPoint, fromPoint):
        # create an arrowhead path (used for directed edges)
        arrowHead = QPainterPath(toPoint)
        if toPoint.y() != fromPoint.y():
            m = (toPoint.x() - fromPoint.x()) / (toPoint.y() - fromPoint.y())
            angle = math.degrees(math.atan(m))
        else:
            angle = 0 

        # rotate first arrwHeadHalf (-10, 0)
        firstX = math.cos(0.5 * angle) * (-10)
        firstY = math.sin(0.5 * angle) * (-10)

        # rotate second arrowHeadHalf (0, 10)
        secondX = -math.sin( 0.5 * angle) * 10
        secondY = math.cos(0.5 * angle) * 10
        
        arrowHead.lineTo(toPoint.x() + firstX, toPoint.y() + firstY)
        arrowHead.moveTo(toPoint.x(), toPoint.y())
        arrowHead.lineTo(toPoint.x() + secondX, toPoint.y() + secondY)

        return arrowHead


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

        self.hasEdges = False

        self.mLayerType = QgsGraphLayerType()

        self.mDataProvider = QgsGraphDataProvider("Point")
        self.mFields = QgsFields()

        if self.crs().isValid():
            self.mCRS = self.crs()
        else:
            self.mCRS = QgsProject.instance().crs()
            self.setCrs(self.mCRS)

        self.__crsUri = "crs=" + self.mCRS.authid()
        self.mDataProvider.setCrs(self.mCRS)

        self.setDataSource(self.mDataProvider.dataSourceUri(), self.mName, self.mDataProvider.providerKey(), QgsDataProvider.ProviderOptions())

        self.mShowEdgeText = False
        self.mShowDirection = False

        self.randomColor = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        self.nameChanged.connect(self.updateName)
        self.crsChanged.connect(self.updateCrs)

        self.mTransform = QgsCoordinateTransform() # default is invalid
        
    def dataProvider(self):
        # TODO: issue with DB Manager plugin
        return self.mDataProvider

    def fields(self):
        return self.mFields

    def createMapRenderer(self, rendererContext):
        return QgsGraphLayerRenderer(self.id(), rendererContext, self.mGraph, self.mCRS,
                                    self.mShowEdgeText, self.mShowDirection, self.randomColor, self.mTransform)

    def setTransformContext(self, ct):
        pass 

    def setGraph(self, graph):
        # if isinstance(graph, PGGraph):
        if isinstance(graph, QgsGraph):
            self.mGraph = graph

            if self.mGraph.edgeCount() != 0:
                self.hasEdges = True
                
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
                self.hasEdges = False

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

    def exportToFile(self):
        """Generic function to export GraphLayers features (either points or linestrings) to a file.

        Returns:
            [boolean]: True if export was successfull.
        """
        
        if self.hasEdges:
            geomType = QgsWkbTypes.LineString
        else:
            geomType = QgsWkbTypes.Point

        # get saveFileName and datatype to export to
        saveFileName = QFileDialog.getSaveFileName(None, "Export To File", "/home", "Shapefile (*.shp);;Geopackage (*.gpkg);;CSV (*.csv)")
        fileName = saveFileName[0]
        
        driver = ""

        if saveFileName[1] == "Shapefile (*.shp)": # Shapefile
            fileName += ".shp"
            driver = "ESRI Shapefile"

        elif saveFileName[1] == "Geopackage (*.gpkg)": # Geopackage
            fileName += ".gpkg"
            driver = "GPKG"

        elif saveFileName[1] == "CSV (*.csv)": # CSV
            fileName += ".csv"
            driver = "CSV"
        
        else:
            return False

        # write features in QgsVectorFileWriter (save features in selected file)
        writer = QgsVectorFileWriter(fileName, "utf-8", self.fields(),
                                        geomType, self.mCRS, driver)

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print("ERROR: ", writer.errorMessage())
            return False
        
        for feat in self.mDataProvider.getFeatures():
            writer.addFeature(feat)
        
        del writer

        return True

    def exportToVectorLayer(self):
        if self.hasEdges:
            vLayer = QgsVectorLayer("LineString", "GraphEdges", "memory")
        else:
            vLayer = QgsVectorLayer("Point", "GraphVertices", "memory")

        vDp = vLayer.dataProvider()

        vDp.addAttributes(self.mFields)

        for feat in self.mDataProvider.getFeatures():
            vDp.addFeature(feat)

        vLayer.setCrs(self.mCRS)

        QgsProject.instance().addMapLayer(vLayer)

        return True

    def readXml(self, node, context):
        """Read QgsGraph (and its subclasses) from the project file.

        Args:
            node (QDomNode): XML Node for layer
            context ([type]): [description]
        """
        self.setLayerType(QgsGraphLayer.LAYER_TYPE)

        # start with empty QgsGraph / PGGraph
        graph = QgsGraph()
        # graph = PGGraph()

        # find srs node in xml
        srsNode = node.firstChild()
        while srsNode.nodeName() != "srs":
            srsNode = srsNode.nextSibling()

        self.mCRS.readXml(srsNode)

        # find graph node in xml
        graphNode = srsNode
        while graphNode.nodeName() != "graphData":
            graphNode = graphNode.nextSibling()
            
        verticesNode = graphNode.firstChild()
        vertexNodes = verticesNode.childNodes()

        # get vertex information and add them to graph
        for vertexId in range(vertexNodes.length()):
            if vertexNodes.at(vertexId).isElement():
                elem = vertexNodes.at(vertexId).toElement()
                graph.addVertex(QgsPointXY(float(elem.attribute("x")), float(elem.attribute("y"))))

        edgesNode = verticesNode.nextSibling()
        edgeNodes = edgesNode.childNodes()

        # get edge information and add them to graph
        strat = QgsNetworkDistanceStrategy()
        for edgeId in range(edgeNodes.length()):
            if edgeNodes.at(edgeId).isElement():
                elem = edgeNodes.at(edgeId).toElement()
                graph.addEdge(int(elem.attribute("fromVertex")), int(elem.attribute("toVertex")), [strat])
                # graph.addEdge(int(elem.attribute("fromVertex")), int(elem.attribute("toVertex"))) # add cost at later state

        # use setGraph function to also add features
        # TODO: this makes readXML go over either points or edges twice
        self.setGraph(graph)

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

        # find srs node in xml
        srsNode = node.firstChild()
        while srsNode.nodeName() != "srs":
            srsNode = srsNode.nextSibling()
        
        # store crs information in xml
        srsNode.removeChild(srsNode.firstChild())
        self.crs().writeXml(srsNode, doc)
        
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

    def zoomToExtent(self):
        canvas = iface.mapCanvas()
        extent = self.mDataProvider.extent()

        canvas.setExtent(self.mTransform.transform(self.mDataProvider.extent()))

        canvas.refresh()

    def toggleText(self):
        self.mShowEdgeText = not self.mShowEdgeText
        
        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def updateName(self):
        self.mName = self.name()

    def updateCrs(self):
        self.mCRS = self.crs()
        self.__crsUri = "crs=" + self.crs().authid()
        self.mDataProvider.setCrs(self.crs())

        # transform drawn coordinates -> coordinates stay the same in graph and features
        destCRS = iface.mapCanvas().mapSettings().destinationCrs()
        self.mTransform = QgsCoordinateTransform(self.mCRS, destCRS, QgsProject.instance())

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def newRandomColor(self):
        self.randomColor = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def toggleDirection(self):
        self.mShowDirection = not self.mShowDirection

        self.triggerRepaint()
        iface.mapCanvas().refresh()

class QgsGraphLayerType(QgsPluginLayerType):
    """When loading a project containing a QgsGraphLayer, a factory class is needed.

    Args:
        QgsPluginLayerType ([type]): [description]
    """
    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE)

    def createLayer(self):
        return QgsGraphLayer()

    def showLayerProperties(self, layer):
        win = QDialog(iface.mainWindow())
        win.setVisible(True)

        # QBoxLayout to add widgets to
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # QLabel with information about the GraphLayer
        label = QLabel(layer.mName +
                        "\n Vertices: " + str(layer.getGraph().vertexCount()) +
                        "\n Edges: " + str(layer.getGraph().edgeCount()) +
                        "\n CRS: " + layer.crs().authid())
        label.setWordWrap(True)
        label.setVisible(True)
        layout.addWidget(label)

        # button to zoom to layers extent
        zoomExtentButton = QPushButton("Zoom to Layer")
        zoomExtentButton.setVisible(True)
        zoomExtentButton.clicked.connect(layer.zoomToExtent)
        layout.addWidget(zoomExtentButton)

        # button to toggle rendered text (mainly edge costs)
        toggleTextButton = QPushButton("Toggle Edge Text")
        toggleTextButton.setVisible(layer.getGraph().edgeCount() != 0) # don't show this button when graph has no edges
        toggleTextButton.clicked.connect(layer.toggleText)
        layout.addWidget(toggleTextButton)

        # button to toggle drawing of arrowHead to show edge direction
        toggleDirectionButton = QPushButton("Toggle Direction")
        toggleDirectionButton.setVisible(layer.getGraph().edgeCount() != 0)
        toggleDirectionButton.clicked.connect(layer.toggleDirection)
        layout.addWidget(toggleDirectionButton)

        # button for exportToVectorLayer
        exportVLButton = QPushButton("Export to VectorLayer")
        exportVLButton.setVisible(True)
        exportVLButton.clicked.connect(layer.exportToVectorLayer)
        layout.addWidget(exportVLButton)

        # button for exportToFile
        exportFButton = QPushButton("Export To File")
        exportFButton.clicked.connect(layer.exportToFile)
        exportFButton.setVisible(True)
        layout.addWidget(exportFButton)

        # button to randomize vertex color
        randomColorButton = QPushButton("Random Vertex Color")
        randomColorButton.clicked.connect(layer.newRandomColor)
        randomColorButton.setVisible(True)
        layout.addWidget(randomColorButton)

        win.setLayout(layout)
        win.adjustSize()

        return True
