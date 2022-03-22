#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
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


from qgis.core import QgsPointXY, QgsMapLayerProxyModel, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapLayerComboBox

from .baseField import BaseField, BaseResult
from ..exceptions import ParseError
from ..protocol.build import available_handlers_pb2


class GraphField(BaseField):
    """Handler class for graph request fields"""

    type = available_handlers_pb2.FieldInformation.FieldType.GRAPH

    def toProtoBuf(self, request, data):
        """
        Creates and returns the protobuf message for the specified request with
        the specified field data

        :param request: Request the protobuf message will be placed in
        :param data: Data for the request field
        :raises ParseError: If data does not contain the required key
        """

        try:
            data.get(self.key)
        except KeyError as error:
            if self.required:
                raise ParseError(f"Invalid data object: Field {self.label} missing but required") from error
            return

        protoField = getattr(request, self.key)
        graph = data[self.key]

        protoField.uid = 0
        for vertex in graph.vertices():
            protoVertex = protoField.vertexList.add()
            protoVertex.uid = vertex.id()

        for edge in graph.edges():
            protoEdge = protoField.edgeList.add()
            protoEdge.uid = edge.id()
            protoEdge.inVertexIndex = graph.findVertexByID(edge.fromVertex())
            protoEdge.outVertexIndex = graph.findVertexByID(edge.toVertex())

        # add static attributes to request
        request.staticAttributes["crs"] = str(graph.crs.authid())
        request.staticAttributes["distanceStrategy"] = str(graph.distanceStrategy)
        request.staticAttributes["edgeDirection"] = str(graph.edgeDirection)

    def createWidget(self, parent):
        """
        Creates a widget for the request field

        :param parent: Parent of the created widget
        """

        widget = QgsMapLayerComboBox(parent)
        widget.setFilters(QgsMapLayerProxyModel.PluginLayer)
        widget.setAllowEmptyLayer(True)
        widget.setCurrentIndex(0)
        widget.currentIndexChanged.connect(parent.graphChanged)
        return widget

    def getWidgetData(self, widget):
        """
        Returns the data of the specified widget

        :param widget: The widget containing the desired data
        :return: The widget data
        """

        layer = widget.currentLayer()
        if layer is not None and layer.isValid():
            return layer.getGraph()
        return None


class GraphResult(BaseResult):
    """Handler class for graph result fields"""

    type = available_handlers_pb2.ResultInformation.HandlerReturnType.GRAPH

    def parseProtoBuf(self, response, data):
        """
        Parses the result field from the specified response protobuf message into the specified data
        dictionairy

        :param response: Protobuf message containing the result field to be parsed
        :param data: Dictionairy the data will be placed into
        """

        protoField = self.getProtoField(response)
        graph = data[self.key]

        # parse static attributes from response
        crs = QgsCoordinateReferenceSystem(response.staticAttributes.get("crs"))
        if crs.isValid():
            graph.updateCrs(crs)
        graph.edgeDirection = response.staticAttributes.get("edgeDirection", "Directed")

        for vertex in protoField.vertexList:
            graph.addVertex(QgsPointXY(0,0), -1, vertex.uid)

        for edge in protoField.edgeList:
            inVertexId = protoField.vertexList[edge.inVertexIndex].uid
            outVertexId = protoField.vertexList[edge.outVertexIndex].uid
            graph.addEdge(inVertexId, outVertexId, -1, edge.uid)

    def getResultString(self, _data):
        """
        Returns the result string of the specified data

        :param _data: The result data
        :return: The result string
        """

        return "Result contains a graph, which will be displayed in a new layer."
