from qgis.core import *
from qgis.utils import iface

from qgis.PyQt.QtCore import QVariant, QPointF, Qt
from qgis.PyQt.QtGui import QColor, QFont, QPainterPath, QPen
from qgis.PyQt.QtXml import *
from qgis.PyQt.QtWidgets import (QDialog, QPushButton, QBoxLayout, QLabel,
                                    QFileDialog, QFrame, QApplication, QHBoxLayout,
                                    QRadioButton, QGroupBox, QUndoStack, QToolButton, QSpinBox)

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

        self.mRenderedCostFunction = self.mLayer.mRenderedCostFunction

    def __del__(self):
        del self.rendererContext

    def render(self):
        return self.__drawGraph()

    def __drawGraph(self):
        if not self.mLayer.doRender:
            return False

        painter = self.renderContext().painter()
        painter.save()
        painter.setPen(QColor('black'))
        painter.setBrush(self.mRandomColor)
        painter.setFont(QFont("arial", 10))
        
        mTransform = self.renderContext().coordinateTransform()

        if isinstance(self.mGraph, ExtGraph):
            try:
                # used to convert map coordinates to canvas coordinates
                converter = self.renderContext().mapToPixel()
                
                for idx in range(self.mGraph.vertexCount()):
                    vertex = self.mGraph.vertex(idx)
                    
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
                        for outgoingEdgeId in outgoing:
                            edgeIdx = self.mGraph.findEdgeByID(outgoingEdgeId)
                            if edgeIdx == -1:
                                continue

                            edge = self.mGraph.edge(edgeIdx)

                            toPoint = self.mGraph.vertex(self.mGraph.findVertexByID(edge.toVertex())).point()
                            fromPoint = vertex.point()

                            if mTransform.isValid():
                                toPoint = mTransform.transform(toPoint)
                                fromPoint = mTransform.transform(fromPoint)

                            toPoint = converter.transform(toPoint).toQPointF()
                            fromPoint = converter.transform(fromPoint).toQPointF()

                            painter.setPen(QColor('black'))
                            if edge.highlighted():
                                highlightPen = QPen(QColor('red'))
                                highlightPen.setWidth(2)
                                painter.setPen(highlightPen)
                            painter.drawLine(toPoint, fromPoint)

                            painter.setPen(QColor('black'))
                            if self.mShowDirection:
                                arrowHead = self.__createArrowHead(toPoint, fromPoint)
                                painter.setPen(QColor('red'))
                                painter.drawPath(arrowHead)
                                painter.setPen(QColor('black'))
                            
                            # add text with edgeCost at line mid point
                            if self.mShowText:
                                midPoint = QPointF(0.5 * toPoint.x() + 0.5 * fromPoint.x(), 0.5 * toPoint.y() + 0.5 * fromPoint.y())
                                edgeCost = self.mGraph.costOfEdge(edgeIdx, self.mRenderedCostFunction)
                                if edgeCost % 1 == 0:
                                    painter.drawText(midPoint, str(edgeCost))
                                else:
                                    painter.drawText(midPoint, str("%.3f" % edgeCost))

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
        if length == 0:
            return arrowHead
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
        
        self.mGraph = ExtGraph()

        self.hasEdges = False

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

        self.mRenderedCostFunction = 0

        self.crsChanged.connect(self.updateCrs)

        self.mTransform = QgsCoordinateTransform() # default is invalid

        self.isEditing = False

        self._extent = QgsRectangle()

        self.willBeDeleted.connect(lambda: self.deleteLater("debug"))

        self.doRender = True

        self.mUndoStack = QUndoStack()

    def deleteLater(self, dummy):
        self.toggleEdit(True)
        
        del self.mDataProvider
        
        del self.mTransform
        del self._extent

        del self.mPointFields
        del self.mLineFields

        del self.mGraph

        try:
            del self.mUndoStack
        except Exception as e:
            print(e)

    def __del__(self):
        pass
        
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
        Set the graph of the QgsGraphLayer and prepare the QgsGraphDataProvider.
        
        :type graph: ExtGraph
        """
        if isinstance(graph, ExtGraph):

            # TODO: does this shallow copy work after all?
            self.mGraph = graph

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

            # self.mGraph.calculateSize()
        
        
    def getGraph(self):
        return self.mGraph

    def __buildFeatures(self):
        if self.exportPoints:
            # build point features
            for vertexIdx in range(self.mGraph.vertexCount()):
                vertex = self.mGraph.vertex(vertexIdx)
                vertexPoint = vertex.point()

                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(vertexPoint))

                feat.setAttributes([vertex.id(), vertexPoint.x(), vertexPoint.y()])
                self.mDataProvider.addFeature(feat, True, vertexIdx)

        if self.exportLines:
            # build line features
            for edgeIdx in range(self.mGraph.edgeCount()):
                edge = self.mGraph.edge(edgeIdx)

                feat = QgsFeature()
                fromVertex = self.mGraph.vertex(self.mGraph.findVertexByID(edge.fromVertex())).point()
                toVertex = self.mGraph.vertex(self.mGraph.findVertexByID(edge.toVertex())).point()
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                # features only save one value for edge cost even if multiple cost functions are given
                feat.setAttributes([edge.id(), edge.fromVertex(), edge.toVertex(), self.mGraph.costOfEdge(edgeIdx)])

                self.mDataProvider.addFeature(feat, False, edgeIdx)

    def __destroyFeatures(self):
        if self.exportPoints:
            # destroy point features (to maybe save space)
            for vertexIdx in range(self.mGraph.vertexCount()):
                self.mDataProvider.deleteFeature(vertexIdx, True)
            
        if self.exportLines:
            # destroy line features (to maybe save space)
            for edgeIdx in range(self.mGraph.edgeCount()):
                self.mDataProvider.deleteFeature(edgeIdx, False)

    def exportToFile(self):
        """
        Function to export GraphLayers features (either points or linestrings) to a file.
        DataTypes to export to are: .shp, .gpkg, .csv, .graphml, .geojson

        :return Boolean if export was successful
        """

        # get saveFileName and datatype to export to
        saveFileName = QFileDialog.getSaveFileName(None, "Export To File", "/home", "Shapefile (*.shp);;Geopackage (*.gpkg);;CSV (*.csv);; GraphML (*.graphml);;GeoJSON (*.geojson)")
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
        
        elif saveFileName[1] == "GraphML (*.graphml)":
            # GraphML can store both points and lines
            pointFileName += ".graphml"
            self.mGraph.writeGraphML(pointFileName)
            return True

        elif saveFileName[1] == "GeoJSON (*.geojson)":
            pointFileName += "Points.geojson"
            lineFileName += "Lines.geojson"
            driver = "GeoJSON"
        else:
            return False

        self.__buildFeatures()

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

        self.__destroyFeatures()

        return True

    def createVectorLayer(self):
        vLineLayer = QgsVectorLayer("LineString", "GraphEdges", "memory")
        vPointLayer = QgsVectorLayer("Point", "GraphVertices", "memory")

        vPDp = vPointLayer.dataProvider()
        vLDp = vLineLayer.dataProvider()

        self.__buildFeatures()

        if self.exportPoints:
            # add attributes to pointLayer
            vPointLayer.startEditing()
            for field in self.mPointFields:
                vPointLayer.addAttribute(field)
            vPointLayer.commitChanges()

            for feat in self.mDataProvider.getFeatures(True):
                vPDp.addFeature(feat)

        if self.exportLines:
            # add attributes to lineLayer
            vLineLayer.startEditing()
            for field in self.mLineFields:
                vLineLayer.addAttribute(field)
            vLineLayer.commitChanges()

            for feat in self.mDataProvider.getFeatures(False):
                vLDp.addFeature(feat)

        vPointLayer.setCrs(self.crs())
        vLineLayer.setCrs(self.crs())

        self.__destroyFeatures()

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
            self.mGraph.distance = float(graphElem.attribute("distance")), int(graphElem.attribute("distanceUnit"))
            self.mGraph.setDistanceStrategy(graphElem.attribute("distanceStrategy"))
            self.mGraph.setRandomSeed(int(graphElem.attribute("randomSeed")))

        verticesNode = graphNode.firstChild()
        vertexNodes = verticesNode.childNodes()

        edgesNode = verticesNode.nextSibling()
        edgeNodes = edgesNode.childNodes()

        self.hasEdges = edgeNodes.length() != 0
        
        # prepare fields
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
        pastID = -1
        verticesSorted = True
        for vertexIdx in range(vertexNodes.length()):
            if vertexNodes.at(vertexIdx).isElement():
                elem = vertexNodes.at(vertexIdx).toElement()
                vertex = QgsPointXY(float(elem.attribute("x")), float(elem.attribute("y")))
                vID = int(elem.attribute("id"))
                
                # check if vertices are loaded in order
                if vID <= pastID:
                    verticesSorted = False
                pastID = vID

                addedVertexIdx = self.mGraph.addVertex(vertex, -1, vID)

                if elem.hasAttribute("clusterID"):
                    self.mGraph.vertex(addedVertexIdx).setClusterID(int(elem.attribute("clusterID")))
                    if self.mGraph.nextClusterID() <= int(elem.attribute("clusterID")):
                        self.mGraph.setNextClusterID(int(elem.attribute("clusterID")) + 1)

        # get edge information and add them to graph
        pastID = -1
        edgesSorted = True
        for edgeIdx in range(edgeNodes.length()):
            if edgeNodes.at(edgeIdx).isElement():
                elem = edgeNodes.at(edgeIdx).toElement()
                fromVertexID = int(elem.attribute("fromVertex"))
                toVertexID = int(elem.attribute("toVertex"))
                eID = int(elem.attribute("id"))

                # check if edges are loaded in order
                if eID <= pastID:
                    edgesSorted = False
                pastID = eID

                highlighted = elem.attribute("highlighted") == "True"
                
                addedIdx = self.mGraph.addEdge(fromVertexID, toVertexID, -1, eID)
                
                if highlighted:
                    self.mGraph.edge(addedIdx).toggleHighlight()
                
                if self.mGraph.distanceStrategy != "Advanced":
                    # TODO: is this necessary? this maybe even does not lead to anything
                    self.mGraph.setCostOfEdge(addedIdx, 0, float(elem.attribute("edgeCost")))
                else:
                    costNodes = edgeNodes.at(edgeIdx).childNodes()
                    for costIdx in range(costNodes.length()):
                        costElem = costNodes.at(costIdx).toElement()
                        functionIndex = int(costElem.attribute("functionIndex"))
                        costValue = float(costElem.attribute("value"))
                        self.mGraph.setCostOfEdge(addedIdx, functionIndex, costValue)

        self.mGraph.setSorted(verticesSorted and edgesSorted)
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
        graphNode.setAttribute("distance", str(self.mGraph.distance[0]))
        graphNode.setAttribute("distanceUnit", self.mGraph.distance[1])
        graphNode.setAttribute("distanceStrategy", self.mGraph.distanceStrategy)
        if self.mGraph.distanceStrategy == "Advanced":
            graphNode.setAttribute("edgeCostFunctions", self.mGraph.amountOfEdgeCostFunctions())
        graphNode.setAttribute("randomSeed", str(self.mGraph.randomSeed))
        node.appendChild(graphNode)

        # vertexNode saves all vertices with tis coordinates
        verticesNode = doc.createElement("vertices")
        graphNode.appendChild(verticesNode)

        # edgeNode saves all edges with its vertices ids
        edgesNode = doc.createElement("edges")
        graphNode.appendChild(edgesNode)

        # store vertices
        for vertexIdx in range(self.mGraph.vertexCount()):
            # QgsPointXY TODO: support for QgsPointZ?
            vertex = self.mGraph.vertex(vertexIdx)
            point = vertex.point()

            # store vertex information (coordinates have to be string to avoid implicit conversion to int)
            self.__writeVertexXML(doc, verticesNode, vertex.id(), point.x(), point.y(), vertex.clusterID() if vertex.clusterID() >= 0 else -1)

        if self.mGraph.edgeCount() != 0:
            # store only edges if available
            
            for edgeIdx in range(self.mGraph.edgeCount()):
                edge = self.mGraph.edge(edgeIdx)
                
                fromVertex = edge.fromVertex()
                toVertex = edge.toVertex()

                # store edge information
                edgeNode = doc.createElement("edge")
                edgeNode.setAttribute("id", edge.id())
                edgeNode.setAttribute("toVertex", toVertex)
                edgeNode.setAttribute("fromVertex", fromVertex)
                edgeNode.setAttribute("highlighted", str(edge.highlighted()))
                
                # store edge costs
                if self.mGraph.distanceStrategy != "Advanced":
                    edgeNode.setAttribute("edgeCost", str(self.mGraph.costOfEdge(edgeIdx)))
                else:
                    for functionIndex in range(self.mGraph.amountOfEdgeCostFunctions()):
                        costNode = doc.createElement("cost")
                        costNode.setAttribute("functionIndex", functionIndex)
                        costNode.setAttribute("value", str(self.mGraph.costOfEdge(edgeIdx, functionIndex)))
                        edgeNode.appendChild(costNode)

                edgesNode.appendChild(edgeNode)
                    
        return True

    def __writeVertexXML(self, doc, node, vertexID, x, y, clusterID=-1):
        """Writes given vertex information to XML.

        :type doc: QDomDocument
        :type node: QDomNode
        :type vertexID: Integer
        :type x: Float
        :type y: Float
        """
        vertexNode = doc.createElement("vertex")
        vertexNode.setAttribute("id", vertexID)
        # store coordinates as strings to avoid implicite conversion from float to int
        vertexNode.setAttribute("x", str(x))
        vertexNode.setAttribute("y", str(y))
        if clusterID >= 0:
            vertexNode.setAttribute("clusterID", str(clusterID))
        node.appendChild(vertexNode)

    def setLayerType(self, layerType):
        self.mLayerType = layerType
        self.setCustomProperty(QgsGraphLayer.LAYER_PROPERTY, self.mLayerType)

    def extent(self):
        # TODO: maybe improve extent in add/deleteVertex
        for vertexIdx in range(self.mGraph.vertexCount()):
            self._extent.combineExtentWith(self.mGraph.vertex(vertexIdx).point())

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
            # start edit mode
            QApplication.setOverrideCursor(Qt.CrossCursor)
            self.oldMapTool = iface.mapCanvas().mapTool()

            self.mMapTool = QgsGraphMapTool(iface.mapCanvas(), self)
            iface.mapCanvas().setMapTool(self.mMapTool)

        elif not self.isEditing:
            QApplication.restoreOverrideCursor()
            iface.mapCanvas().setMapTool(self.oldMapTool)
            
            del self.mMapTool

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

    def changeRenderedCostFunction(self, idx):
        self.mRenderedCostFunction = idx

    def activateUniqueName(self):
        # sets the layers name to its id,  'unique but not nice'
        if self.name() == "RandomGraphLayer":
            self.setName(self.id())

class QgsGraphLayerType(QgsPluginLayerType):
    """
    When loading a project containing a QgsGraphLayer, a factory class is needed.
    """
    def __init__(self):
        super().__init__(QgsGraphLayer.LAYER_TYPE)

    def __del__(self):
        pass

    def createLayer(self):
        return QgsGraphLayer()

    def showLayerProperties(self, layer):
        """
        Show a QDialog with options for the QgsGraphLayer for the user

        :type layer: QgsGraphLayer
        :return Boolean
        """
        layer.activateUniqueName()
        # if hasattr(self, "win") and self.win:
        #     self.win.setVisible(True)
        #     return True

        self.win = QDialog(iface.mainWindow())
        self.win.setVisible(True)

        # QBoxLayout to add widgets to
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # QLabel with information about the GraphLayer
        informationLabel = QLabel(layer.name() +
                        "\n " + ((tr("Seed: ") + str(layer.mGraph.randomSeed)) if layer.mGraph.randomSeed else "") +
                        "\n " + tr("Vertices") + ": " + str(layer.getGraph().vertexCount()) +
                        "\n " + tr("Edges") + ": " + str(layer.getGraph().edgeCount()) +
                        "\n " + tr("CRS") + ": " + layer.crs().authid())
        informationLabel.setWordWrap(True)
        informationLabel.setVisible(True)
        informationLabel.setStyleSheet("border: 1px solid black;")
        layout.addWidget(informationLabel)
        
        # QLabel with information about the layers fields
        pointFieldsText = tr("PointFields") + ":"
        for field in layer.fields(True):
            pointFieldsText += "\n " + field.displayName() + " (" + field.displayType() + ")"
        lineFieldsText = tr("LineFields") + ":"
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
        toggleRenderButton = QPushButton(tr("Toggle Rendering"))
        toggleRenderButton.setVisible(True)
        toggleRenderButton.clicked.connect(layer.toggleRendering)
        layout.addWidget(toggleRenderButton)

        # button to toggle drawing of lines / edges
        toggleLinesButton = QPushButton(tr("Toggle Lines"))
        toggleLinesButton.setVisible(hasEdges)
        toggleLinesButton.clicked.connect(layer.toggleLines)
        layout.addWidget(toggleLinesButton)

        # button to toggle rendered text (mainly edge costs)
        toggleTextButton = QPushButton(tr("Toggle Edge Text"))
        toggleTextButton.setVisible(hasEdges) # don't show this button when graph has no edges
        toggleTextButton.clicked.connect(layer.toggleText)
        layout.addWidget(toggleTextButton)

        # spinbox to choose which advanced values to render
        if layer.mGraph.distanceStrategy == "Advanced":
            costFunctionLabel = QLabel(tr("Choose Cost Function"))
            costFunctionLabel.setVisible(True)
            costFunctionSpinBox = QSpinBox()
            costFunctionSpinBox.setMinimum(0)
            costFunctionSpinBox.setMaximum(layer.mGraph.amountOfEdgeCostFunctions() - 1)
            costFunctionSpinBox.valueChanged.connect(layer.changeRenderedCostFunction)
            costFunctionSpinBox.setVisible(True)
            layout.addWidget(costFunctionLabel)
            layout.addWidget(costFunctionSpinBox)


        # button to toggle drawing of arrowHead to show edge direction
        toggleDirectionButton = QPushButton(tr("Toggle Direction"))
        toggleDirectionButton.setVisible(hasEdges and layer.mGraph.edgeDirection == "Directed")
        toggleDirectionButton.clicked.connect(layer.toggleDirection)
        layout.addWidget(toggleDirectionButton)

        fileSeparator = QFrame()
        fileSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        fileSeparator.setLineWidth(1)
        layout.addWidget(fileSeparator)

        selectExportTypeGroup = QGroupBox(tr("Export Type"))
        onlyPointsRadio = QRadioButton(tr("Only Points"))
        onlyPointsRadio.toggled.connect(lambda:layer.toggleExportType(onlyPointsRadio))
        onlyLinesRadio = QRadioButton(tr("Only Lines"))
        onlyLinesRadio.toggled.connect(lambda:layer.toggleExportType(onlyLinesRadio))
        bothRadio = QRadioButton(tr("Both"))
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
        editButton = QPushButton(tr("Toggle Editing"))
        editButton.clicked.connect(layer.toggleEdit)
        editButton.setVisible(True)
        editButton.setToolTip(tr("List of Options") + ":"\
                                +"\n " + tr("LeftClick: Add Vertex without Edges")\
                                +"\n " + tr("CTRL+LeftClick: Add Vertex with Edges")\
                                +"\n " + tr("RightClick: Select Vertex")\
                                +"\n " + tr(" 1) Select Vertex")\
                                +"\n " + tr(" 2) Move Vertex (without Edges) on LeftClick")\
                                +"\n " + tr(" 3) Move Vertex (with Edges) on CTRL+LeftClick")\
                                +"\n " + tr(" 4) Add Edge to 2nd Vertex on RightClick (removes already existing edge)")\
                                +"\n " + tr(" 5) Remove Vertex on CTRL+RightClick")\
                                +"\n " + tr(" 6) 2nd RightClick not on Vertex removes Selection"))
        layout.addWidget(editButton)

        # undo button
        undoButton = QToolButton()
        undoButton.setDefaultAction(layer.mUndoStack.createUndoAction(undoButton))
        undoButton.setVisible(True)
        layout.addWidget(undoButton)

        # redo button
        redoButton = QToolButton()
        redoButton.setDefaultAction(layer.mUndoStack.createRedoAction(redoButton))
        redoButton.setVisible(True)
        layout.addWidget(redoButton)

        self.win.setLayout(layout)
        self.win.adjustSize()

        layer.willBeDeleted.connect(self.win.reject)

        return True
