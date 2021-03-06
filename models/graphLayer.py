#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Julian Wittker
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

import math
import random

from qgis.core import (QgsMapLayerRenderer, QgsProject, QgsPluginLayer, QgsFields, QgsRectangle, QgsField, QgsFeature,
                       QgsGeometry, QgsPoint, QgsVectorFileWriter, QgsWkbTypes, QgsVectorLayer, QgsPointXY,
                       QgsPluginLayerType, QgsCoordinateTransform)
from qgis.utils import iface

from qgis.PyQt.QtCore import QVariant, QPointF, Qt, QLineF
from qgis.PyQt.QtGui import QColor, QFont, QPainterPath, QPen
from qgis.PyQt.QtWidgets import (QDialog, QPushButton, QBoxLayout, QLabel,
                                 QFileDialog, QFrame, QApplication, QHBoxLayout,
                                 QRadioButton, QGroupBox, QUndoStack, QToolButton, QSpinBox,
                                 QToolBar)

from .graphDataProvider import GraphDataProvider
from .graphMapTool import GraphMapTool
from .extGraph import ExtGraph
from ..helperFunctions import tr


class GraphLayerRenderer(QgsMapLayerRenderer):
    """
    Renderer to render the graph of a GraphLayer
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

        self.mShowEdgeText = self.mLayer.mShowEdgeText
        self.mShowVertexText = self.mLayer.mShowVertexText
        self.mShowDirection = self.mLayer.mShowDirection
        self.mShowLines = self.mLayer.mShowLines

        self.mRenderedEdgeCostFunction = self.mLayer.mRenderedEdgeCostFunction
        self.mRenderedVertexCostFunction = self.mLayer.mRenderedVertexCostFunction

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

        if QgsProject.instance().crs().authid() != self.mLayer.mGraph.crs.authid():
            mTransform = self.rendererContext.coordinateTransform()

        # lines and points to render
        lines = []
        highlightedLines = []
        if isinstance(self.mGraph, ExtGraph):
            try:
                # used to convert map coordinates to canvas coordinates
                converter = self.renderContext().mapToPixel()

                for vertexId in self.mGraph.mVertices:
                    vertex = self.mGraph.vertex(vertexId)

                    # draw vertex
                    point = vertex.point()

                    if QgsProject.instance().crs().authid() != self.mLayer.mGraph.crs.authid() and mTransform.isValid():
                        point = mTransform.transform(point)

                    point = converter.transform(point).toQPointF()

                    painter.setPen(QColor('black'))
                    # don't draw border of vertices if graph has edges
                    if self.mGraph.edgeCount() != 0:
                        painter.setPen(self.mRandomColor)
                    painter.drawEllipse(point, 3.0, 3.0)

                    # draw vertex costs
                    if self.mShowVertexText:
                        painter.setPen(QColor('black'))
                        vertexCost = self.mGraph.costOfVertex(vertexId, self.mRenderedVertexCostFunction)
                        if not vertexCost and not vertexCost == 0:
                            painter.drawText(point, "None")
                        elif vertexCost % 1 == 0:
                            painter.drawText(point, str(vertexCost))
                        else:
                            painter.drawTest(point, str("%.f" % vertexCost))

                    # draw outgoing edges
                    if self.mGraph.edgeCount() != 0 and self.mShowLines:
                        outgoing = vertex.outgoingEdges()
                        for outgoingEdgeId in outgoing:

                            edge = self.mGraph.edge(outgoingEdgeId)

                            toPoint = self.mGraph.vertex(edge.toVertex()).point()
                            fromPoint = point

                            if QgsProject.instance().crs().authid() != self.mLayer.mGraph.crs.authid() and mTransform.isValid():
                                toPoint = mTransform.transform(toPoint)

                            toPoint = converter.transform(toPoint).toQPointF()

                            if edge.highlighted():
                                highlightedLines.append(QLineF(toPoint.x(), toPoint.y(), fromPoint.x(), fromPoint.y()))
                            else:
                                lines.append(QLineF(toPoint.x(), toPoint.y(), fromPoint.x(), fromPoint.y()))

                            painter.setPen(QColor('black'))
                            if self.mShowDirection:
                                arrowHead = self.__createArrowHead(toPoint, fromPoint)
                                painter.setPen(QColor('red'))
                                painter.drawPath(arrowHead)
                                painter.setPen(QColor('black'))

                            # add text with edgeCost at line mid point
                            if self.mShowEdgeText:
                                midPoint = QPointF(0.5 * toPoint.x() + 0.5 * fromPoint.x(), 0.5 * toPoint.y() +
                                                   0.5 * fromPoint.y())
                                edgeCost = self.mGraph.costOfEdge(outgoingEdgeId, self.mRenderedEdgeCostFunction)
                                if not edgeCost and not edgeCost == 0:
                                    painter.drawText(midPoint, "None")
                                elif edgeCost % 1 == 0:
                                    painter.drawText(midPoint, str(edgeCost))
                                else:
                                    painter.drawText(midPoint, str("%.3f" % edgeCost))

                if len(lines) != 0:
                    painter.setPen(QColor('black'))
                    painter.drawLines(lines)

                if len(highlightedLines) != 0:
                    highlightPen = QPen(QColor('red'))
                    highlightPen.setWidth(2)
                    painter.setPen(highlightPen)
                    painter.drawLines(highlightedLines)

            except Exception as err:
                print(err)
        else:
            print("mGraph NOT found")

        painter.restore()

        return True

    def __createArrowHead(self, toPoint, fromPoint):
        """
        Creates an arrowHead for an edge to indicate its direction

        :type toPoint: QgsPointXY
        :type fromPoint: QgsPointXY

        :return QPainterPath
        """
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


class GraphLayer(QgsPluginLayer):
    """
    Represent a graph in a layer and make that graph saveable and editable.
    """

    LAYER_TYPE = "graph"
    LAYER_PROPERTY = "graph_layer_type"

    def __init__(self, name="GraphLayer"):
        super().__init__(GraphLayer.LAYER_TYPE, name)

        self.setValid(True)

        self.mGraph = ExtGraph()

        self.hasEdges = False

        self.mDataProvider = GraphDataProvider("Point")
        self.mPointFields = QgsFields()
        self.mLineFields = QgsFields()

        if not self.crs().isValid():
            self.setCrs(QgsProject.instance().crs())

        self.__crsUri = "crs=" + self.crs().authid()
        self.mDataProvider.setCrs(self.crs())

        self.mShowEdgeText = False
        self.mShowVertexText = False
        self.mShowDirection = False
        self.mShowLines = True

        self.exportPoints = True
        self.exportLines = True

        self.mRandomColor = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        self.mRenderedEdgeCostFunction = 0
        self.mRenderedVertexCostFunction = 0

        self.crsChanged.connect(self.updateCrs)

        self.isEditing = False

        self.mTransform = QgsCoordinateTransform()
        self._extent = QgsRectangle()

        self.willBeDeleted.connect(lambda: self.deleteLater("debug"))

        self.doRender = True

        self.mUndoStack = QUndoStack()

        self.nameChanged.connect(self.activateUniqueName)

        if not iface is None:
            self.enableEditToolBar()

    def deleteLater(self, _dummy):
        self.toggleEdit(True)

        del self.mDataProvider

        del self._extent

        del self.mPointFields
        del self.mLineFields

        del self.mGraph

        if self.graphToolBar:
            self.graphToolBar.actionTriggered.disconnect(self.__toolBarActionTriggered)

        try:
            del self.mUndoStack
        except Exception as e:
            print(e)

    def __del__(self):
        pass

    def dataProvider(self):
        return self.mDataProvider

    def fields(self, point):
        if point:
            return self.mPointFields
        else:
            return self.mLineFields

    def createMapRenderer(self, rendererContext):
        # print("CreateRenderer")
        if QgsProject.instance().crs().authid() != self.mGraph.crs.authid():
            self.mTransform = rendererContext.coordinateTransform()
        return GraphLayerRenderer(self.id(), rendererContext)

    def setTransformContext(self, ct):
        pass

    def setGraph(self, graph):
        """
        Set the graph of the GraphLayer and prepare the GraphDataProvider.

        :type graph: ExtGraph
        """
        if isinstance(graph, ExtGraph):

            # TODO: does this shallow copy work after all?
            self.mGraph = graph

            if self.mGraph.crs:
                self.setCrs(self.mGraph.crs)
            else:
                self.mGraph.updateCrs(self.crs())

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

            self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField], False)

            # update line fields
            self.mLineFields.append(edgeIdField)
            self.mLineFields.append(fromVertexField)
            self.mLineFields.append(toVertexField)

            # self.mGraph.calculateSize()

    def getGraph(self):
        return self.mGraph

    def __buildFeatures(self):
        """
        Builds vector features based on the graph of the layer
        """
        if self.exportPoints:
            # build point features
            for vertexId in self.mGraph.mVertices:
                vertex = self.mGraph.vertex(vertexId)
                vertexPoint = vertex.point()

                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(vertexPoint))

                feat.setAttributes([vertexId, vertexPoint.x(), vertexPoint.y()])
                self.mDataProvider.addFeature(feat, True, vertexId)

        if self.exportLines:
            # add fields for advanced costs
            if self.mGraph.distanceStrategy == "Advanced":
                for costIdx in range(self.mGraph.amountOfEdgeCostFunctions()):
                    fieldName = "cost_" + str(costIdx)
                    costField = QgsField(fieldName, QVariant.Double, "double")

                    self.mDataProvider.addAttributes([costField], False)

                    self.mLineFields.append(costField)

            # only use one field for one cost function
            else:
                costField = QgsField("edgeCost", QVariant.Double, "double")
                self.mDataProvider.addAttributes([costField], False)
                self.mLineFields.append(costField)

            # build line features
            for edgeId in self.mGraph.mEdges:
                edge = self.mGraph.edge(edgeId)

                feat = QgsFeature()
                fromVertex = self.mGraph.vertex(edge.fromVertex()).point()
                toVertex = self.mGraph.vertex(edge.toVertex()).point()
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

                attr = [edgeId, edge.fromVertex(), edge.toVertex()]

                if self.mGraph.distanceStrategy == "Advanced":

                    for costIdx in range(self.mGraph.amountOfEdgeCostFunctions()):
                        attr.append(self.mGraph.costOfEdge(edgeId, costIdx))

                else:
                    attr.append(self.mGraph.costOfEdge(edgeId))

                feat.setAttributes(attr)
                self.mDataProvider.addFeature(feat, False, edgeId)

    def __destroyFeatures(self):
        if self.exportPoints:
            # destroy point features (to maybe save space)
            for vertexId in self.mGraph.mVertices:
                self.mDataProvider.deleteFeature(vertexId, True)

        if self.exportLines:
            # destroy line features (to maybe save space)
            for edgeId in self.mGraph.mEdges:
                self.mDataProvider.deleteFeature(edgeId, False)

    def exportToFile(self):
        """
        Function to export GraphLayers features (either points or linestrings) to a file.
        DataTypes to export to are: .shp, .gpkg, .csv, .graphml, .geojson

        :return Boolean if export was successful
        """

        # get saveFileName and datatype to export to
        saveFileName = QFileDialog.getSaveFileName(None, "Export To File", "/home", "Shapefile (*.shp);;" +
                                                   "Geopackage (*.gpkg);;CSV (*.csv);; GraphML (*.graphml);;" +
                                                   "GeoJSON (*.geojson)")
        pointFileName = saveFileName[0]
        lineFileName = saveFileName[0]

        driver = ""

        if saveFileName[1] == "Shapefile (*.shp)":  # Shapefile
            pointFileName += "Points.shp" if not "Points.shp" in pointFileName else ""
            lineFileName += "Lines.shp" if not "Lines.shp" in lineFileName else ""
            driver = "ESRI Shapefile"

        elif saveFileName[1] == "Geopackage (*.gpkg)":  # Geopackage
            pointFileName += "Points.gpkg" if not "Points.gpkg" in pointFileName else ""
            lineFileName += "Lines.gpkg" if not "Lines.gpkg" in lineFileName else ""
            driver = "GPKG"

        elif saveFileName[1] == "CSV (*.csv)":  # CSV
            pointFileName += "Points.csv" if not "Points.csv" in pointFileName else ""
            lineFileName += "Lines.csv"if not "Lines.csv" in lineFileName else ""
            driver = "CSV"

        elif saveFileName[1] == "GraphML (*.graphml)":
            # GraphML can store both points and lines
            pointFileName += ".graphml" if not ".graphml" in pointFileName else ""
            self.mGraph.writeGraphML(pointFileName)
            return True

        elif saveFileName[1] == "GeoJSON (*.geojson)":
            pointFileName += "Points.geojson" if not "Points.geojson" in pointFileName else ""
            lineFileName += "Lines.geojson" if not "Lines.geojson" in lineFileName else ""
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
        vLineLayer = QgsVectorLayer("LineString", self.name() + "_Edges", "memory")
        vPointLayer = QgsVectorLayer("Point", self.name() + "_Vertices", "memory")

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

    def readXml(self, node, _context):
        """
        Reads the layer and the graph from a QGIS project file
        """

        self.setLayerType(GraphLayer.LAYER_TYPE)

        # start with empty ExtGraph
        self.mGraph = ExtGraph()

        # find srs node in xml
        srsNode = node.firstChild()
        while srsNode.nodeName() != "srs":
            srsNode = srsNode.nextSibling()

        self.crs().readXml(srsNode)
        # here no updateCrs since coordinates and crs are read from XML and therefore need no coordinate projection
        self.mGraph.crs = self.crs()

        # find graph node in xml
        graphNode = srsNode
        while graphNode.nodeName() != "graphData":
            graphNode = graphNode.nextSibling()

        graphElem = graphNode.toElement()
        vertexCostFunctions = 0
        if graphElem.hasAttribute("connectionType"):
            self.mGraph.setConnectionType(graphElem.attribute("connectionType"))
            self.mGraph.numberNeighbours = int(graphElem.attribute("numberNeighbours"))
            self.mGraph.edgeDirection = graphElem.attribute("edgeDirection")
            self.mGraph.clusterNumber = int(graphElem.attribute("clusterNumber"))
            self.mGraph.nnAllowDoubleEdges = graphElem.attribute("nnAllowDoubleEdges") == "True"
            self.mGraph.distance = float(graphElem.attribute("distance")), int(graphElem.attribute("distanceUnit"))
            self.mGraph.setDistanceStrategy(graphElem.attribute("distanceStrategy"))

            # random seed only found in randomly created graphs
            if graphElem.hasAttribute("randomSeed"):
                self.mGraph.setRandomSeed(int(graphElem.attribute("randomSeed")))

            if graphElem.hasAttribute("vertexCostFunctions"):
                vertexCostFunctions = int(graphElem.attribute("vertexCostFunctions"))

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

        # self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField])
        self.mDataProvider.addAttributes([edgeIdField, fromVertexField, toVertexField], False)

        # update line fields
        self.mLineFields.append(edgeIdField)
        self.mLineFields.append(fromVertexField)
        self.mLineFields.append(toVertexField)

        # get vertex information and add them to graph
        for vertexIdx in range(vertexNodes.length()):
            if vertexNodes.at(vertexIdx).isElement():
                elem = vertexNodes.at(vertexIdx).toElement()
                vertex = QgsPointXY(float(elem.attribute("x")), float(elem.attribute("y")))
                vID = int(elem.attribute("id"))

                addedVertexId = self.mGraph.addVertex(vertex, vID)

                if elem.hasAttribute("clusterID"):
                    self.mGraph.vertex(addedVertexId).setClusterID(int(elem.attribute("clusterID")))
                    if self.mGraph.nextClusterID() <= int(elem.attribute("clusterID")):
                        self.mGraph.setNextClusterID(int(elem.attribute("clusterID")) + 1)

                if vertexCostFunctions >= 0:
                    costNodes = vertexNodes.at(vertexIdx).childNodes()
                    for costIdx in range(costNodes.length()):
                        costElem = costNodes.at(costIdx).toElement()
                        functionIndex = int(costElem.attribute("functionIndex"))
                        costValue = float(costElem.attribute("value"))
                        self.mGraph.setCostOfVertex(addedVertexId, functionIndex, costValue)

        # get edge information and add them to graph
        for edgeIdx in range(edgeNodes.length()):
            if edgeNodes.at(edgeIdx).isElement():
                elem = edgeNodes.at(edgeIdx).toElement()
                fromVertexID = int(elem.attribute("fromVertex"))
                toVertexID = int(elem.attribute("toVertex"))
                eID = int(elem.attribute("id"))

                highlighted = elem.attribute("highlighted") == "True"

                addedId = self.mGraph.addEdge(fromVertexID, toVertexID, eID)

                if highlighted:
                    self.mGraph.edge(addedId).toggleHighlight()

                if self.mGraph.distanceStrategy != "Advanced":
                    # TODO: is this necessary? this maybe even does not lead to anything
                    if not elem.attribute("edgeCost") == "None":
                        self.mGraph.setCostOfEdge(addedId, 0, float(elem.attribute("edgeCost")))
                else:
                    costNodes = edgeNodes.at(edgeIdx).childNodes()
                    for costIdx in range(costNodes.length()):
                        costElem = costNodes.at(costIdx).toElement()
                        functionIndex = int(costElem.attribute("functionIndex"))
                        costValue = float(costElem.attribute("value"))
                        self.mGraph.setCostOfEdge(addedId, functionIndex, costValue)

        return True

    def writeXml(self, node, doc, _context):
        """
        Writes the layer and the graph to a QGIS project file
        """

        if node.isElement():
            node.toElement().setAttribute("type", "plugin")
            node.toElement().setAttribute("name", GraphLayer.LAYER_TYPE)

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
        if hasattr(self.mGraph, "advancedVertexWeights") and self.mGraph.advancedVertexWeights:
            graphNode.setAttribute("vertexCostFunctions", len(self.mGraph.vertexWeights))

        # don't add 'None' as randomSeed for not randomly created graphs
        if self.mGraph.randomSeed:
            graphNode.setAttribute("randomSeed", str(self.mGraph.randomSeed))
        node.appendChild(graphNode)

        # vertexNode saves all vertices with tis coordinates
        verticesNode = doc.createElement("vertices")
        graphNode.appendChild(verticesNode)

        # edgeNode saves all edges with its vertices ids
        edgesNode = doc.createElement("edges")
        graphNode.appendChild(edgesNode)

        # store vertices
        for vertexId in self.mGraph.mVertices:
            # QgsPointXY TODO: support for QgsPointZ?
            vertex = self.mGraph.vertex(vertexId)
            point = vertex.point()

            # store vertex information (coordinates have to be string to avoid implicit conversion to int)
            vertexNode = self.__writeVertexXML(doc, vertexId, point.x(), point.y(),
                                               vertex.clusterID() if vertex.clusterID() >= 0 else -1)

            if hasattr(self.mGraph, "advancedVertexWeights") and self.mGraph.advancedVertexWeights:
                for functionIndex in range(len(self.mGraph.vertexWeights)):
                    costNode = doc.createElement("cost")
                    costNode.setAttribute("functionIndex", functionIndex)
                    costNode.setAttribute("value", str(self.mGraph.costOfVertex(vertexId, functionIndex)))
                    vertexNode.appendChild(costNode)

            verticesNode.appendChild(vertexNode)

        if self.mGraph.edgeCount() != 0:
            # store only edges if available

            for edgeId in self.mGraph.mEdges:
                edge = self.mGraph.edge(edgeId)

                fromVertex = edge.fromVertex()
                toVertex = edge.toVertex()

                # store edge information
                edgeNode = doc.createElement("edge")
                edgeNode.setAttribute("id", edgeId)
                edgeNode.setAttribute("toVertex", toVertex)
                edgeNode.setAttribute("fromVertex", fromVertex)
                edgeNode.setAttribute("highlighted", str(edge.highlighted()))

                # store edge costs
                if self.mGraph.distanceStrategy != "Advanced":
                    edgeNode.setAttribute("edgeCost", str(self.mGraph.costOfEdge(edgeId)))
                else:
                    for functionIndex in range(self.mGraph.amountOfEdgeCostFunctions()):
                        costNode = doc.createElement("cost")
                        costNode.setAttribute("functionIndex", functionIndex)
                        costNode.setAttribute("value", str(self.mGraph.costOfEdge(edgeId, functionIndex)))
                        edgeNode.appendChild(costNode)

                edgesNode.appendChild(edgeNode)

        return True

    def __writeVertexXML(self, doc, vertexID, x, y, clusterID=-1):
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
        return vertexNode

    def setLayerType(self, layerType):
        self.mLayerType = layerType
        self.setCustomProperty(GraphLayer.LAYER_PROPERTY, self.mLayerType)

    def extent(self):
        """
        Calculates and returns the layers extent based on the graphs bounding box

        :return QgsRectangle
        """
        self._extent = QgsRectangle()
        for vertexId in self.mGraph.mVertices:
            self._extent.combineExtentWith(self.mGraph.vertex(vertexId).point())

        if QgsProject.instance().crs().authid() != self.mGraph.crs.authid() and self.mTransform.isValid():
            self._extent = self.mTransform.transform(self._extent)

        return self._extent

    def zoomToExtent(self):
        canvas = iface.mapCanvas()
        extent = self.extent()

        canvas.setExtent(extent)
        canvas.refresh()

    def toggleEdgeText(self):
        self.mShowEdgeText = not self.mShowEdgeText

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def toggleVertexText(self):
        self.mShowVertexText = not self.mShowVertexText

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def updateCrs(self):
        self.__crsUri = "crs=" + self.crs().authid()
        self.mDataProvider.setCrs(self.crs())

        # update crs and project coordinates in graph accordingly
        self.mGraph.updateCrs(self.crs())

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

            self.mMapTool = GraphMapTool(iface.mapCanvas(), self)
            iface.mapCanvas().setMapTool(self.mMapTool)

        elif not self.isEditing:
            QApplication.restoreOverrideCursor()
            iface.mapCanvas().setMapTool(self.oldMapTool)

            del self.mMapTool

        if willBeDeleted:
            self.isEditing = False

    def enableEditToolBar(self):
        self.graphToolBar = None
        toolbars = iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            if toolbar.objectName() == "Graph ToolBar":
                self.graphToolBar = toolbar
                break
        if self.graphToolBar:
            self.graphToolBar.actionTriggered.connect(self.__toolBarActionTriggered)

    def __toolBarActionTriggered(self, action):
        if iface.activeLayer().id() == self.id():
            if "Toggle Edit" in action.whatsThis():
                self.toggleEdit()
            elif "Zoom to Layer" in action.whatsThis():
                self.zoomToExtent()

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

    def changeRenderedEdgeCostFunction(self, idx):
        self.mRenderedEdgeCostFunction = idx

    def nextRenderedEdgeCostFunction(self):
        self.mRenderedEdgeCostFunction = (self.mRenderedEdgeCostFunction + 1) % self.mGraph.amountOfEdgeCostFunctions()

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def changeRenderedVertexCostFunction(self, idx):
        self.mRenderedVertexCostFunction = idx

    def nextRenderedVertexCostFunction(self):
        self.mRenderedVertexCostFunction = (self.mRenderedVertexCostFunction + 1) % len(self.mGraph.vertexWeights)

        self.triggerRepaint()
        iface.mapCanvas().refresh()

    def activateUniqueName(self):
        """
        Creates a unique name for the layer based on graph information
        """
        # sets the layers name to a combination of graph information
        if self.name() == "RandomGraphLayer" or self.name() == "NewGraphLayer":
            constructName = self.mGraph.connectionType() if self.mGraph.connectionType() != "Nearest neighbor" else "NN"
            constructName += "_" + self.mGraph.distanceStrategy + "_" + self.mGraph.edgeDirection

            mapLayers = QgsProject.instance().mapLayers()
            currHighestNr = 0
            for layer in mapLayers.values():
                if constructName == layer.name() and currHighestNr == 0:
                    currHighestNr = 1
                elif constructName in layer.name():
                    nameNr = layer.name().split(constructName)[1]
                    if nameNr != "" and nameNr.isnumeric():
                        nameNr = int(nameNr)
                        if currHighestNr <= nameNr:
                            currHighestNr = nameNr + 1
                    else:
                        if currHighestNr <= 0:
                            currHighestNr = 1

            self.setName(constructName + (str(currHighestNr) if currHighestNr > 0 else ""))


class GraphLayerType(QgsPluginLayerType):
    """
    When loading a project containing a GraphLayer, a factory class is needed.
    """
    TOOLTIPTEXT = tr("List of Options") + ":"\
        + "\n " + tr("LeftClick: Add Vertex without Edges")\
        + "\n " + tr("CTRL + LeftClick: Add Vertex with Edges")\
        + "\n " + tr("RightClick: Select Vertex")\
        + "\n " + tr(" 1) Select Vertex")\
        + "\n " + tr(" 2) Move Vertex (without Edges) on LeftClick")\
        + "\n " + tr(" 3) Move Vertex (with Edges) on CTRL+LeftClick")\
        + "\n " + tr(" 4) Add Edge to 2nd Vertex on RightClick (removes already existing edge)")\
        + "\n " + tr(" 5) Remove Vertex on CTRL+RightClick")\
        + "\n " + tr(" 6) 2nd RightClick not on Vertex removes Selection")\
        + "\n " + tr("SHIFT + LeftClick + Drag: Select multiple vertices at once")\
        + "\n " + tr("SHIFT + RightClick + Drag: Zoom to selected area")\
        + "\n " + tr("R: Removes the existing single vertex selection")

    def __init__(self):
        super().__init__(GraphLayer.LAYER_TYPE)

    def __del__(self):
        pass

    def createLayer(self):
        return GraphLayer()

    def showLayerProperties(self, layer):
        """
        Show a QDialog with options for the GraphLayer for the user

        :type layer: GraphLayer
        :return Boolean
        """

        self.layerID = layer.id()

        self.win = QDialog(iface.mainWindow())
        self.win.setVisible(True)

        # QBoxLayout to add widgets to
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # QLabel with information about the GraphLayer
        informationLabel = QLabel(
            layer.name() + "\n " + ((tr("Seed: ") + str(layer.mGraph.randomSeed)) if layer.mGraph.randomSeed else "") +
            "\n " + tr("Vertices") + ": " + str(layer.getGraph().vertexCount()) + "\n " + tr("Edges") + ": " +
            str(layer.getGraph().edgeCount()) + "\n " + tr("CRS") + ": " + layer.crs().authid())
        informationLabel.setWordWrap(True)
        informationLabel.setVisible(True)
        informationLabel.setStyleSheet("border: 1px solid black;")
        layout.addWidget(informationLabel)

        # QLabel with information about the graphs information
        graphInformationText = tr("DistanceStrategy: ") + layer.mGraph.distanceStrategy + ("(" + str(layer.mGraph.amountOfEdgeCostFunctions()) + ")" if layer.mGraph.distanceStrategy ==
                                                                                           "Advanced" else "") + "\n" + tr("Edge Direction: ") + layer.mGraph.edgeDirection + "\n" + tr("Connection Type: ") + layer.mGraph.mConnectionType

        if layer.mGraph.mConnectionType == "Nearest neighbor" or layer.mGraph.mConnectionType == "DistanceNN" or\
           layer.mGraph.mConnectionType == "ClusterNN":
            graphInformationText += "\n" + tr("Number Neighbors: ") + str(layer.mGraph.numberNeighbours)

        if layer.mGraph.mConnectionType == "DistanceNN":
            graphInformationText += "\n" + tr("Distance: ") + str(layer.mGraph.distance[0])

        if layer.mGraph.mConnectionType == "ClusterComplete" or layer.mGraph.mConnectionType == "ClusterNN":
            graphInformationText += "\n" + tr("Number Clusters: ") + str(layer.mGraph.clusterNumber)

        graphInformationText += "\n" + tr("Allow Double Edges: ") + str(layer.mGraph.nnAllowDoubleEdges)

        amountVertexWeightFunctions = 0
        if hasattr(layer.mGraph, "advancedVertexWeights") and layer.mGraph.advancedVertexWeights:
            amountVertexWeightFunctions = len(layer.mGraph.vertexWeights)
            graphInformationText += "\n" + tr("Vertex Cost Functions: ") + str(amountVertexWeightFunctions)

        graphLabel = QLabel(graphInformationText)
        graphLabel.setWordWrap(True)
        graphLabel.setVisible(True)
        graphLabel.setStyleSheet("border: 1px solid black;")
        layout.addWidget(graphLabel)

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

        toggleBox = QGroupBox()
        toggleLayout = QBoxLayout(QBoxLayout.Direction.LeftToRight)

        # button to toggle rendered edge text
        toggleEdgeTextButton = QPushButton(tr("Toggle Edge Text"))
        toggleEdgeTextButton.setVisible(hasEdges)  # don't show this button when graph has no edges
        toggleEdgeTextButton.clicked.connect(layer.toggleEdgeText)
        toggleLayout.addWidget(toggleEdgeTextButton)

        # button to toggle rendered vertex text
        toggleVertexTextButton = QPushButton(tr("Toggle Vertex Text"))
        toggleVertexTextButton.setVisible(hasEdges)  # don't show this button when graph has no edges
        toggleVertexTextButton.clicked.connect(layer.toggleVertexText)
        toggleLayout.addWidget(toggleVertexTextButton)

        toggleBox.setLayout(toggleLayout)
        layout.addWidget(toggleBox)

        # spinbox to choose which advanced values to render for edges
        if layer.mGraph.distanceStrategy == "Advanced" and layer.mGraph.amountOfEdgeCostFunctions() <= 1:
            layer.changeRenderedEdgeCostFunction(0)

        elif layer.mGraph.distanceStrategy == "Advanced":
            costFunctionBox = QGroupBox()
            costFunctionLayout = QBoxLayout(QBoxLayout.Direction.LeftToRight)

            costFunctionLabel = QLabel(tr("Choose Edge Cost Function"))
            costFunctionLabel.setVisible(True)
            costFunctionSpinBox = QSpinBox()
            costFunctionSpinBox.setMinimum(0)
            costFunctionSpinBox.setMaximum(layer.mGraph.amountOfEdgeCostFunctions() - 1)
            costFunctionSpinBox.valueChanged.connect(layer.changeRenderedEdgeCostFunction)
            costFunctionSpinBox.setVisible(True)
            costFunctionLayout.addWidget(costFunctionLabel)
            costFunctionLayout.addWidget(costFunctionSpinBox)

            nextButton = QPushButton(tr("Next"))
            nextButton.setMaximumWidth(50)
            nextButton.clicked.connect(layer.nextRenderedEdgeCostFunction)
            nextButton.clicked.connect(lambda: costFunctionSpinBox.setValue(layer.mRenderedEdgeCostFunction))
            costFunctionLayout.addWidget(nextButton)

            costFunctionBox.setLayout(costFunctionLayout)
            layout.addWidget(costFunctionBox)

        # spinbox to choose which advanced values to render for vertices
        if amountVertexWeightFunctions == 1:
            layer.changeRenderedVertexCostFunction(0)

        elif amountVertexWeightFunctions >= 2:
            vertexCostFunctionBox = QGroupBox()
            vertexCostFunctionLayout = QBoxLayout(QBoxLayout.Direction.LeftToRight)

            vertexCostFunctionLabel = QLabel(tr("Choose Vertex Cost Function"))
            vertexCostFunctionLabel.setVisible(True)
            vertexCostFunctionSpinBox = QSpinBox()
            vertexCostFunctionSpinBox.setMinimum(0)
            vertexCostFunctionSpinBox.setMaximum(amountVertexWeightFunctions - 1)
            vertexCostFunctionSpinBox.valueChanged.connect(layer.changeRenderedVertexCostFunction)
            vertexCostFunctionSpinBox.setVisible(True)
            vertexCostFunctionLayout.addWidget(vertexCostFunctionLabel)
            vertexCostFunctionLayout.addWidget(vertexCostFunctionSpinBox)

            nextVButton = QPushButton(tr("Next"))
            nextVButton.setMaximumWidth(50)
            nextVButton.clicked.connect(layer.nextRenderedVertexCostFunction)
            nextVButton.clicked.connect(lambda: vertexCostFunctionSpinBox.setValue(layer.mRenderedVertexCostFunction))
            vertexCostFunctionLayout.addWidget(nextVButton)

            vertexCostFunctionBox.setLayout(vertexCostFunctionLayout)
            layout.addWidget(vertexCostFunctionBox)

        # button to toggle drawing of arrowHead to show edge direction
        toggleDirectionButton = QPushButton(tr("Toggle Direction"))
        toggleDirectionButton.setVisible(hasEdges and layer.mGraph.edgeDirection == "Directed")
        toggleDirectionButton.clicked.connect(layer.toggleDirection)
        layout.addWidget(toggleDirectionButton)

        # button to randomize vertex color
        randomColorButton = QPushButton(tr("Random Vertex Color"))
        randomColorButton.clicked.connect(layer.newRandomColor)
        randomColorButton.setVisible(True)
        layout.addWidget(randomColorButton)

        fileSeparator = QFrame()
        fileSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        fileSeparator.setLineWidth(1)
        layout.addWidget(fileSeparator)

        selectExportTypeGroup = QGroupBox(tr("Export Type"))
        onlyPointsRadio = QRadioButton(tr("Only Points"))
        onlyPointsRadio.toggled.connect(lambda: layer.toggleExportType(onlyPointsRadio))
        onlyLinesRadio = QRadioButton(tr("Only Lines"))
        onlyLinesRadio.toggled.connect(lambda: layer.toggleExportType(onlyLinesRadio))
        bothRadio = QRadioButton(tr("Both"))
        bothRadio.toggled.connect(lambda: layer.toggleExportType(bothRadio))
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

        editSeparator = QFrame()
        editSeparator.setFrameShape(QFrame.HLine | QFrame.Plain)
        editSeparator.setLineWidth(1)
        layout.addWidget(editSeparator)

        # button to enable editing
        editBox = QGroupBox()
        editBoxLayout = QBoxLayout(QBoxLayout.Direction.LeftToRight)

        editButton = QPushButton(tr("Toggle Editing"))
        editButton.clicked.connect(layer.toggleEdit)
        editButton.setVisible(True)
        editButton.setToolTip(self.TOOLTIPTEXT)
        editBoxLayout.addWidget(editButton)

        def __toolTip():
            toolTipWin = QDialog(iface.mainWindow())
            toolTipWin.setVisible(True)
            toolTipLayout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
            toolTipLabel = QLabel(self.TOOLTIPTEXT)
            toolTipLayout.addWidget(toolTipLabel)
            toolTipWin.setLayout(toolTipLayout)
            toolTipWin.adjustSize()

        # add button for tool tip window
        toolTipButton = QPushButton("?")
        toolTipButton.setMaximumWidth(25)
        toolTipButton.clicked.connect(__toolTip)
        editBoxLayout.addWidget(toolTipButton)

        editBox.setLayout(editBoxLayout)
        layout.addWidget(editBox)

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
