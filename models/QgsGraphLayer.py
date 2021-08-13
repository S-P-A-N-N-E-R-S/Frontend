from qgis.core import *
from qgis.gui import QgsVertexMarker
from qgis.utils import iface

from qgis.PyQt.QtCore import QVariant, QPointF, Qt
from qgis.PyQt.QtGui import QColor, QFont, QPainterPath
from qgis.PyQt.QtXml import *
from qgis.PyQt.QtWidgets import (QDialog, QPushButton, QBoxLayout, QLabel,
                                    QFileDialog, QFrame, QApplication, QHBoxLayout,
                                    QRadioButton, QGroupBox, QUndoStack, QToolButton)

import random, math

from .QgsGraphDataProvider import QgsGraphDataProvider
from .QgsGraphMapTool import QgsGraphMapTool
from .ExtGraph import ExtGraph
from ..helperFunctions import tr

class QgsGraphLayerRenderer(QgsMapLayerRenderer):
    """
    Renderer to render the graph of a QgsGraphLayer
    """

    def __init__(self, layerId, rendererContext):
        super().__init__(layerId, rendererContext)

        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer

        self.rendererContext = rendererContext
        
        self.mGraph = self.mLayer.getGraph()

        self.mRandomColor = self.mLayer.mRandomColor

        self.mShowText = self.mLayer.mShowEdgeText
        self.mShowDirection = self.mLayer.mShowDirection
        self.mShowLines = self.mLayer.mShowLines

    def __del__(self):
        # print("Renderer Destructor")
        pass

    def render(self):
        return self.__drawGraph()

    def __drawGraph(self):
        if not self.mLayer.doRender:
            return False

        painter = self.renderContext().painter()
        painter.save()
        painter.setPen(QColor('black'))
        painter.setBrush(self.mRandomColor)
        painter.setFont(QFont("arial", 5))
        
        mTransform = self.renderContext().coordinateTransform()

        if isinstance(self.mGraph, ExtGraph):
            try:
                # used to convert map coordinates to canvas coordinates
                converter = iface.mapCanvas().getCoordinateTransform()
                
                vertices = self.mGraph.vertices()
                for id in vertices:
                    vertex = self.mGraph.vertex(id)
                    
                    # draw vertex
                    point = vertex.point()

                    if mTransform.isValid():
                        point = mTransform.transform(point)

                    point = converter.transform(point).toQPointF()
                    
                    painter.setPen(QColor('black'))
                    # don't draw border of vertices if graph has edges
                    if self.mGraph.edgeCount() != 0:
                        painter.setPen(self.mRandomColor)
                    painter.drawEllipse(point, 3.0, 3.0)

                    # draw outgoing edges
                    if self.mGraph.edgeCount() != 0 and self.mShowLines:
                        outgoing = vertex.outgoingEdges()
                        for outgoingEdgeId in range(len(outgoing)):
                            # print("Id: ", id, ", OutgoingEdgeId: ", outgoingEdgeId)
                            edge = self.mGraph.edge(outgoing[outgoingEdgeId])

                            toPoint = self.mGraph.vertex(edge.toVertex()).point()
                            fromPoint = self.mGraph.vertex(edge.fromVertex()).point()

                            if mTransform.isValid():
                                toPoint = mTransform.transform(toPoint)
                                fromPoint = mTransform.transform(fromPoint)

                            toPoint = converter.transform(toPoint).toQPointF()
                            fromPoint = converter.transform(fromPoint).toQPointF()

                            painter.setPen(QColor('black'))
                            if edge.highlighted():
                                painter.setPen(QColor('red'))
                            painter.drawLine(toPoint, fromPoint)

                            if self.mShowDirection:
                                arrowHead = self.__createArrowHead(toPoint, fromPoint)
                                painter.setPen(QColor('red'))
                                painter.drawPath(arrowHead)
                                painter.setPen(QColor('black'))
                            
                            # add text with edgeCost at line mid point
                            if self.mShowText:
                                midPoint = QPointF(0.5 * toPoint.x() + 0.5 * fromPoint.x(), 0.5 * toPoint.y() + 0.5 * fromPoint.y())
                                painter.drawText(midPoint, str("%.3f" % self.mGraph.costOfEdge(outgoingEdgeId)))

            except Exception as err:
                print(err)
        else:
            print("mGraph NOT found")

        painter.restore()

        return True

    def __createArrowHead(self, toPoint, fromPoint):
        # create an arrowHead path (used for directed edges)
        arrowHead = QPainterPath(toPoint)

        # calculate angle of line
        dx = toPoint.x() - fromPoint.x()
        dy = toPoint.y() - fromPoint.y()
        length = math.sqrt(dx*dx + dy*dy)
        angle = math.radians(math.degrees(math.acos(dx / length)) + 45)
        
        if dy < 0:
            angle = -angle
            angle = math.radians(math.degrees(angle) + 90)
            
        # rotate first arrowHeadHalf (-10, 0)
        firstX = math.cos(angle) * (-10)
        firstY = math.sin(angle) * (-10)

        # rotate second arrowHeadHalf (0, 10)
        secondX = -math.sin(angle) * 10
        secondY = math.cos(angle) * 10

        arrowHead.lineTo(toPoint.x() + firstX, toPoint.y() + firstY)
        arrowHead.moveTo(toPoint.x(), toPoint.y())
        arrowHead.lineTo(toPoint.x() + secondX, toPoint.y() + secondY)

        return arrowHead


class QgsGraphLayer(QgsPluginLayer):
    """
    Represent a graph in a layer and make that graph saveable and editable.
    """

    LAYER_TYPE = "graph"
    LAYER_PROPERTY = "graph_layer_type"

    def __init__(self, name="QgsGraphLayer"):
        super().__init__(QgsGraphLayer.LAYER_TYPE, name)
        
        self.setValid(True)
        
        self.mName = name
        self.mGraph = ExtGraph()

        self.hasEdges = False

        self.mLayerType = QgsGraphLayerType()

        self.mDataProvider = QgsGraphDataProvider("Point")
        self.mPointFields = QgsFields()
        self.mLineFields = QgsFields()

        if not self.crs().isValid():
            self.setCrs(QgsProject.instance().crs())

        self.__crsUri = "crs=" + self.crs().authid()
        self.mDataProvider.setCrs(self.crs())
        self.mGraph.crs = self.crs()

        self.mShowEdgeText = False
        self.mShowDirection = False
        self.mShowLines = True

        self.mRandomColor = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        self.nameChanged.connect(self.updateName)
        self.crsChanged.connect(self.updateCrs)

        self.mTransform = QgsCoordinateTransform() # default is invalid

        self.mMapTool = QgsGraphMapTool(iface.mapCanvas(), self)

        self.isEditing = False

        self._extent = QgsRectangle()

        self.willBeDeleted.connect(lambda: self.toggleEdit(True))

        self.doRender = True

        self.mUndoStack = QUndoStack()

    def __del__(self):
        del self.mDataProvider
        self.nameChanged.disconnect(self.updateName)
        self.crsChanged.disconnect(self.updateCrs)
        self.willBeDeleted.disconnect(self.toggleEdit)
        
        if self.isEditing:
            QApplication.restoreOverrideCursor()
            iface.mapCanvas().setMapTool(self.oldMapTool)
            del self.mMapTool
        
        del self.mTransform
        del self._extent

        del self.mPointFields
        del self.mLineFields

        del self.mGraph
        
    def dataProvider(self):
        # TODO: issue with DB Manager plugin
        return self.mDataProvider

    def fields(self, point):
        if point:
            return self.mPointFields
        else:
            return self.mLineFields

    def createMapRenderer(self, rendererContext):
        # print("CreateRenderer")
        self.mTransform = rendererContext.coordinateTransform()
        return QgsGraphLayerRenderer(self.id(), rendererContext)

    def setTransformContext(self, ct):
        pass 

    def setGraph(self, graph):
        """
        Set the graph of the QgsGraphLayer and add features accordingly.
        
        :type graph: ExtGraph
        """
        if isinstance(graph, ExtGraph):
            # create an actual new ExtGraph from graph
            self.mGraph = ExtGraph()
            self.mGraph.setConnectionType(graph.mConnectionType)
            self.mGraph.setDistanceStrategy(graph.distanceStrategy)

            advanced = False
            if self.mGraph.distanceStrategy == "Advanced":
                advanced = True

            if graph.edgeCount() != 0:
                self.hasEdges = True
                
                self.mDataProvider.setGeometryToPoint(False)
            else:
                self.hasEdges = False
                self.mDataProvider.setGeometryToPoint(True)

            self.mDataProvider.setDataSourceUri("Point?" + self.__crsUri, True)
            self.mDataProvider.setDataSourceUri("LineString?" + self.__crsUri, False)

            # point attributes
            vertexIdField = QgsField("vertexId", QVariant.Int, "integer")
            xField = QgsField("x", QVariant.Double, "double")
            yField = QgsField("y", QVariant.Double, "double")

            self.mDataProvider.addAttributes([vertexIdField, xField, yField], True)
            
            # update point fields
            self.mPointFields.append(vertexIdField)
            self.mPointFields.append(xField)
            self.mPointFields.append(yField)

            # line attributes
            edgeIdField = QgsField("edgeId", QVariant.Int, "integer")
            fromVertexField = QgsField("fromVertex", QVariant.Double, "double")
            toVertexField = QgsField("toVertex", QVariant.Double, "double")
            costField = QgsField("edgeCost", QVariant.Double, "double")
            
            self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField, costField], False)
                
            # update line fields
            self.mLineFields.append(edgeIdField)
            self.mLineFields.append(fromVertexField)
            self.mLineFields.append(toVertexField)
            self.mLineFields.append(costField)
                
            # add vertices to new ExtGraph (have to be added to ExtGraph before edges do -> inefficient)
            for vertexId in graph.vertices():
                vertex = graph.vertex(vertexId)
                vertexPoint = vertex.point()
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(vertexPoint))

                feat.setAttributes([vertexId, vertexPoint.x(), vertexPoint.y()])
                self.mDataProvider.addFeature(feat, True)
                
                self.mGraph.addVertex(vertex.point(), vertexId)

            # add edges to new ExtGraph and create corresponding features
            amountEdgeCostFunctions = graph.amountOfEdgeCostFunctions()
            for edgeId in graph.edges():
                edge = graph.edge(edgeId)

                feat = QgsFeature()
                fromVertex = graph.vertex(edge.fromVertex()).point()
                toVertex = graph.vertex(edge.toVertex()).point()
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                feat.setAttributes([edgeId, edge.fromVertex(), edge.toVertex(), graph.costOfEdge(edgeId)])

                self.mDataProvider.addFeature(feat, False)

                self.mGraph.addEdge(edge.fromVertex(), edge.toVertex(), edgeId)

                # set all cost functions
                # for functionIdx in range(amountEdgeCostFunctions):
                #     cost = edge.costOfEdge(edgeId, functionIdx)
                #     self.mGraph.setCostOfEdge(edgeId, functionIdx, cost)
        
    def getGraph(self):
        return self.mGraph

    def exportToFile(self):
        """
        Function to export GraphLayers features (either points or linestrings) to a file.
        DataTypes to export to are: .shp, .gpkg, .csv, .graphML, .geojson

        :return Boolean if export was successful
        """

        # get saveFileName and datatype to export to
        saveFileName = QFileDialog.getSaveFileName(None, "Export To File", "/home", "Shapefile (*.shp);;Geopackage (*.gpkg);;CSV (*.csv);; graphML (*.graphML);;GeoJSON (*.geojson)")
        pointFileName = saveFileName[0]
        lineFileName = saveFileName[0]
        
        driver = ""

        if saveFileName[1] == "Shapefile (*.shp)": # Shapefile
            pointFileName += "Points.shp"
            lineFileName += "Lines.shp"
            driver = "ESRI Shapefile"

        elif saveFileName[1] == "Geopackage (*.gpkg)": # Geopackage
            pointFileName += "Points.gpkg"
            lineFileName += "Lines.gpkg"
            driver = "GPKG"

        elif saveFileName[1] == "CSV (*.csv)": # CSV
            pointFileName += "Points.csv"
            lineFileName += "Lines.csv"
            driver = "CSV"
        
        elif saveFileName[1] == "graphML (*.graphML)":
            pointFileName += "Points.graphML"
            lineFileName += "Lines.graphML"
            self.mGraph.writeGraphML(fileName)
            return True

        elif saveFileName[1] == "GeoJSON (*.geojson)":
            pointFileName += "Points.geojson"
            lineFileName += "Lines.geojson"
            driver = "GeoJSON"
        else:
            return False

        if self.exportPoints:
            # write point features in QgsVectorFileWriter (save features in selected file)
            pointWriter = QgsVectorFileWriter(pointFileName, "utf-8", self.fields(True),
                                            QgsWkbTypes.Point, self.crs(), driver)

            if pointWriter.hasError() != QgsVectorFileWriter.NoError:
                print("ERROR QgsVectorFileWriter", pointWriter.errorMessage())
                return False

            for feat in self.mDataProvider.getFeatures(True):
                pointWriter.addFeature(feat)

            del pointWriter

        if self.exportLines:
            # write line features in QgsVectorFileWriter (save features in selected file)
            lineWriter = QgsVectorFileWriter(lineFileName, "utf-8", self.fields(False),
                                            QgsWkbTypes.LineString, self.crs(), driver)

            if lineWriter.hasError() != QgsVectorFileWriter.NoError:
                print("ERROR QgsVectorFileWriter", lineWriter.errorMessage())
                return False
            
            for feat in self.mDataProvider.getFeatures(False):
                    lineWriter.addFeature(feat)
            
            del lineWriter

        return True

    def createVectorLayer(self):
        vLineLayer = QgsVectorLayer("LineString", "GraphEdges", "memory")
        vPointLayer = QgsVectorLayer("Point", "GraphVertices", "memory")

        vPDp = vPointLayer.dataProvider()
        vLDp = vLineLayer.dataProvider()

        # add attributes to pointLayer
        vPointLayer.startEditing()
        for field in self.mPointFields:
            vPointLayer.addAttribute(field)
        vPointLayer.commitChanges()

        # add attributes to lineLayer
        vLineLayer.startEditing()
        for field in self.mLineFields:
            vLineLayer.addAttribute(field)
        vLineLayer.commitChanges()

        for feat in self.mDataProvider.getFeatures(True):
            vPDp.addFeature(feat)

        for feat in self.mDataProvider.getFeatures(False):
            vLDp.addFeature(feat)

        vPointLayer.setCrs(self.crs())
        vLineLayer.setCrs(self.crs())

        return [vPointLayer, vLineLayer]

    def exportToVectorLayer(self):
        [vPointLayer, vLineLayer] = self.createVectorLayer()
        
        QgsProject.instance().addMapLayer(vPointLayer)
        QgsProject.instance().addMapLayer(vLineLayer)

        return True

    def readXml(self, node, context):

        self.setLayerType(QgsGraphLayer.LAYER_TYPE)

        # start with empty ExtGraph
        self.mGraph = ExtGraph()

        # find srs node in xml
        srsNode = node.firstChild()
        while srsNode.nodeName() != "srs":
            srsNode = srsNode.nextSibling()

        self.crs().readXml(srsNode)

        # find graph node in xml
        graphNode = srsNode
        while graphNode.nodeName() != "graphData":
            graphNode = graphNode.nextSibling()
            
        graphElem = graphNode.toElement()
        if graphElem.hasAttribute("connectionType"):
            self.mGraph.setConnectionType(graphElem.attribute("connectionType"))
            self.mGraph.numberNeighbours = int(graphElem.attribute("numberNeighbours"))
            self.mGraph.edgeDirection = graphElem.attribute("edgeDirection")
            self.mGraph.clusterNumber = int(graphElem.attribute("clusterNumber"))
            self.mGraph.nnAllowDoubleEdges = graphElem.attribute("nnAllowDoubleEdges") == "True"
            self.mGraph.distance = float(graphElem.attribute("distance"))

        verticesNode = graphNode.firstChild()
        vertexNodes = verticesNode.childNodes()

        edgesNode = verticesNode.nextSibling()
        edgeNodes = edgesNode.childNodes()

        self.hasEdges = edgeNodes.length() != 0
        
        # prepare fields and features
        if self.hasEdges:
            self.mDataProvider.setGeometryToPoint(False)
        else:
            self.mDataProvider.setGeometryToPoint(True)
        
        self.mDataProvider.setDataSourceUri("Point?" + self.__crsUri, True)
        self.mDataProvider.setDataSourceUri("LineString?" + self.__crsUri, False)

        # point attributes
        vertexIdField = QgsField("vertexId", QVariant.Int, "integer")
        xField = QgsField("x", QVariant.Double, "double")
        yField = QgsField("y", QVariant.Double, "double")

        self.mDataProvider.addAttributes([vertexIdField, xField, yField], True)
        
        # update point fields
        self.mPointFields.append(vertexIdField)
        self.mPointFields.append(xField)
        self.mPointFields.append(yField)

        # line attributes
        edgeIdField = QgsField("edgeId", QVariant.Int, "integer")
        fromVertexField = QgsField("fromVertex", QVariant.Double, "double")
        toVertexField = QgsField("toVertex", QVariant.Double, "double")
        costField = QgsField("edgeCost", QVariant.Double, "double")
        
        # self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField])
        self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField, costField], False)
        
        # update line fields
        self.mLineFields.append(edgeIdField)
        self.mLineFields.append(fromVertexField)
        self.mLineFields.append(toVertexField)
        self.mLineFields.append(costField)


        # get vertex information and add them to graph
        for vertexId in range(vertexNodes.length()):
            if vertexNodes.at(vertexId).isElement():
                elem = vertexNodes.at(vertexId).toElement()
                vertex = QgsPointXY(float(elem.attribute("x")), float(elem.attribute("y")))
                vIdx = int(elem.attribute("id"))
                self.mGraph.addVertex(vertex, vIdx)
                
                # add feature for each vertex
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(vertex))

                feat.setAttributes([vIdx, vertex.x(), vertex.y()])
                self.mDataProvider.addFeature(feat, True)

        # get edge information and add them to graph
        for edgeId in range(edgeNodes.length()):
            if edgeNodes.at(edgeId).isElement():
                elem = edgeNodes.at(edgeId).toElement()
                fromVertexId = int(elem.attribute("fromVertex"))
                toVertexId = int(elem.attribute("toVertex"))
                eIdx = int(elem.attribute("id"))
                self.mGraph.addEdge(fromVertexId, toVertexId, eIdx) # add cost at later state
                # TODO: set correct function index
                # self.mGraph.setCostOfEdge(eIdx, 0, float(elem.attribute("cost")))

                # add feature for each edge
                feat = QgsFeature()
                fromVertex = self.mGraph.vertex(fromVertexId).point()
                toVertex = self.mGraph.vertex(toVertexId).point()
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                feat.setAttributes([eIdx, fromVertexId, toVertexId, self.mGraph.costOfEdge(eIdx)])

                self.mDataProvider.addFeature(feat, False)                

        return True

    def writeXml(self, node, doc, context):

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
        graphNode.setAttribute("connectionType", self.mGraph.connectionType())
        graphNode.setAttribute("numberNeighbours", self.mGraph.numberNeighbours)
        graphNode.setAttribute("edgeDirection", self.mGraph.edgeDirection)
        graphNode.setAttribute("clusterNumber", self.mGraph.clusterNumber)
        graphNode.setAttribute("nnAllowDoubleEdges", str(self.mGraph.nnAllowDoubleEdges))
        graphNode.setAttribute("distance", str(self.mGraph.distance))
        node.appendChild(graphNode)

        # vertexNode saves all vertices with tis coordinates
        verticesNode = doc.createElement("vertices")
        graphNode.appendChild(verticesNode)

        # edgeNode saves all edges with its vertices ids
        # TODO: also save cost information stored in ExtGraph (merge necessary beforehand)
        edgesNode = doc.createElement("edges")
        graphNode.appendChild(edgesNode)

        # store vertices
        for vertexId in self.mGraph.vertices():
            # QgsPointXY TODO: support for QgsPointZ?
            point = self.mGraph.vertex(vertexId).point()

            # store vertex information (coordinates have to be string to avoid implicit conversion to int)
            self.__writeVertexXML(doc, verticesNode, vertexId, point.x(), point.y())

        if self.mGraph.edgeCount() != 0:
            # store only edges if available
            
            for edgeId in self.mGraph.edges():
                edge = self.mGraph.edge(edgeId)
                
                fromVertex = edge.fromVertex()
                toVertex = edge.toVertex()

                # store edge information
                edgeNode = doc.createElement("edge")
                edgeNode.setAttribute("id", edgeId)
                edgeNode.setAttribute("toVertex", toVertex)
                edgeNode.setAttribute("fromVertex", fromVertex)
                edgeNode.setAttribute("edgeCost", str(self.mGraph.costOfEdge(edgeId)))
                edgesNode.appendChild(edgeNode)
                    
        return True

    def __writeVertexXML(self, doc, node, id, x, y):
        """Writes given vertex information to XML.

        :type doc: QDomDocument
        :type node: QDomNode
        :type vertexId: Integer
        :type x: Float
        :type y: Float
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

    def extent(self):
        for vertexId in self.mGraph.mVertices:
            self._extent.combineExtentWith(self.mGraph.mVertices[vertexId].point())

        return self._extent

    def zoomToExtent(self):
        canvas = iface.mapCanvas()
        extent = self.extent()

        if self.mTransform.isValid():
            extent = self.mTransform.transform(extent)

        canvas.setExtent(extent)
        canvas.refresh()

    def toggleText(self):
        self.mShowEdgeText = not self.mShowEdgeText
        
        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def updateName(self):
        self.mName = self.name()

    def updateCrs(self):
        self.__crsUri = "crs=" + self.crs().authid()
        self.mDataProvider.setCrs(self.crs())
        self.mGraph.crs = self.crs()

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def newRandomColor(self):
        self.mRandomColor = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def toggleDirection(self):
        self.mShowDirection = not self.mShowDirection

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def toggleLines(self):
        self.mShowLines = not self.mShowLines

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def toggleEdit(self, willBeDeleted=False):
        self.isEditing = not self.isEditing

        if self.isEditing and not willBeDeleted:
            QApplication.setOverrideCursor(Qt.CrossCursor)
            self.oldMapTool = iface.mapCanvas().mapTool()
            iface.mapCanvas().setMapTool(self.mMapTool)

        elif not self.isEditing:
            QApplication.restoreOverrideCursor()
            iface.mapCanvas().setMapTool(self.oldMapTool)

    def isEditable(self):
        return True

    def supportsEditing(self):
        return True

    def toggleExportType(self, sender):
        if sender.isChecked():
            if sender.text() == "Only Points":
                self.exportPoints = True
                self.exportLines = False
            elif sender.text() == "Only Lines":
                self.exportPoints = False
                self.exportLines = True
            else:
                self.exportPoints = True
                self.exportLines = True

    def toggleRendering(self):
        self.doRender = not self.doRender

        self.triggerRepaint()
        iface.mapCanvas().refresh()

class QgsGraphLayerType(QgsPluginLayerType):
    """
    When loading a project containing a QgsGraphLayer, a factory class is needed.
    """
    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE)

    def __del__(self):
        # print("QgsGraphLayerType Destructor")
        pass

    def createLayer(self):
        return QgsGraphLayer()

    def showLayerProperties(self, layer):
        """
        Show a QDialog with options for the QgsGraphLayer for the user

        :type layer: QgsGraphLayer
        :return Boolean
        """
        win = QDialog(iface.mainWindow())
        win.setVisible(True)

        # QBoxLayout to add widgets to
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # QLabel with information about the GraphLayer
        informationLabel = QLabel(layer.mName +
                        "\n Vertices: " + str(layer.getGraph().vertexCount()) +
                        "\n Edges: " + str(layer.getGraph().edgeCount()) +
                        "\n CRS: " + layer.crs().authid())
        informationLabel.setWordWrap(True)
        informationLabel.setVisible(True)
        informationLabel.setStyleSheet("border: 1px solid black;")
        layout.addWidget(informationLabel)
        
        # QLabel with information about the layers fields
        pointFieldsText = "PointFields:"
        for field in layer.fields(True):
            pointFieldsText += "\n " + field.displayName() + " (" + field.displayType() + ")"
        lineFieldsText = "LineFields:"
        for field in layer.fields(False):
            lineFieldsText += "\n " + field.displayName() + " (" + field.displayType() + ")"
        fieldsText = pointFieldsText + "\n" + lineFieldsText
        fieldsLabel = QLabel(fieldsText)
        fieldsLabel.setWordWrap(True)
        fieldsLabel.setVisible(True)
        fieldsLabel.setStyleSheet("border: 1px solid black;")
        layout.addWidget(fieldsLabel)

        # button to zoom to layers extent
        zoomExtentButton = QPushButton(tr("Zoom to Layer"))
        zoomExtentButton.setVisible(True)
        zoomExtentButton.clicked.connect(layer.zoomToExtent)
        layout.addWidget(zoomExtentButton)

        edgeSeparator = QFrame()
        edgeSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        edgeSeparator.setLineWidth(1)
        layout.addWidget(edgeSeparator)

        hasEdges = layer.getGraph().edgeCount() != 0

        # button to toggle drawing of complete layer
        toggleRenderButton = QPushButton("Toggle Rendering")
        toggleRenderButton.setVisible(True)
        toggleRenderButton.clicked.connect(layer.toggleRendering)
        layout.addWidget(toggleRenderButton)

        # button to toggle drawing of lines / edges
        toggleLinesButton = QPushButton("Toggle Lines")
        toggleLinesButton.setVisible(hasEdges)
        toggleLinesButton.clicked.connect(layer.toggleLines)
        layout.addWidget(toggleLinesButton)

        # button to toggle rendered text (mainly edge costs)
        toggleTextButton = QPushButton(tr("Toggle Edge Text"))
        toggleTextButton.setVisible(hasEdges) # don't show this button when graph has no edges
        toggleTextButton.clicked.connect(layer.toggleText)
        layout.addWidget(toggleTextButton)

        # button to toggle drawing of arrowHead to show edge direction
        toggleDirectionButton = QPushButton(tr("Toggle Direction"))
        toggleDirectionButton.setVisible(hasEdges)
        toggleDirectionButton.clicked.connect(layer.toggleDirection)
        layout.addWidget(toggleDirectionButton)

        fileSeparator = QFrame()
        fileSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        fileSeparator.setLineWidth(1)
        layout.addWidget(fileSeparator)

        selectExportTypeGroup = QGroupBox("Export Type")
        onlyPointsRadio = QRadioButton("Only Points")
        onlyPointsRadio.toggled.connect(lambda:layer.toggleExportType(onlyPointsRadio))
        onlyLinesRadio = QRadioButton("Only Lines")
        onlyLinesRadio.toggled.connect(lambda:layer.toggleExportType(onlyLinesRadio))
        bothRadio = QRadioButton("Both")
        bothRadio.toggled.connect(lambda:layer.toggleExportType(bothRadio))
        bothRadio.setChecked(True)
        
        radioLayout = QHBoxLayout()
        radioLayout.addWidget(onlyPointsRadio)
        radioLayout.addWidget(onlyLinesRadio)
        radioLayout.addWidget(bothRadio)
        selectExportTypeGroup.setLayout(radioLayout)
        layout.addWidget(selectExportTypeGroup)

        # button for exportToVectorLayer
        exportVLButton = QPushButton(tr("Export to VectorLayer"))
        exportVLButton.setVisible(True)
        exportVLButton.clicked.connect(layer.exportToVectorLayer)
        layout.addWidget(exportVLButton)

        # button for exportToFile
        exportFButton = QPushButton(tr("Export To File"))
        exportFButton.clicked.connect(layer.exportToFile)
        exportFButton.setVisible(True)
        layout.addWidget(exportFButton)

        colorSeparator = QFrame()
        colorSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        colorSeparator.setLineWidth(1)
        layout.addWidget(colorSeparator)

        # button to randomize vertex color
        randomColorButton = QPushButton(tr("Random Vertex Color"))
        randomColorButton.clicked.connect(layer.newRandomColor)
        randomColorButton.setVisible(True)
        layout.addWidget(randomColorButton)

        editSeparator = QFrame()
        editSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        editSeparator.setLineWidth(1)
        layout.addWidget(editSeparator)

        # button to enable editing
        editButton = QPushButton("Toggle Editing")
        editButton.clicked.connect(layer.toggleEdit)
        editButton.setVisible(True)
        editButton.setToolTip("List of Options:"\
                                +"\n LeftClick: Add Vertex without Edges"\
                                +"\n CTRL+LeftClick: Add Vertex with Edges"\
                                +"\n RightClick: Select Vertex"\
                                +"\n  1) Select Vertex"\
                                +"\n  2) Move Vertex (without Edges) on LeftClick"\
                                +"\n  3) Move Vertex (with Edges) on CTRL+LeftClick"\
                                +"\n  4) Add Edge to 2nd Vertex on RightClick (removes already existing edge)"\
                                +"\n  5) Remove Vertex on CTRL+RightClick"\
                                +"\n  6) 2nd RightClick not on Vertex removes Selection")
        layout.addWidget(editButton)

        # undo button
        undoButton = QToolButton()
        undoButton.setDefaultAction(layer.mUndoStack.createUndoAction(undoButton, "Undo"))
        undoButton.setVisible(True)
        layout.addWidget(undoButton)

        # redo button
        redoButton = QToolButton()
        redoButton.setDefaultAction(layer.mUndoStack.createRedoAction(redoButton, "Redo"))
        redoButton.setVisible(True)
        layout.addWidget(redoButton)

        win.setLayout(layout)
        win.adjustSize()

        return True
