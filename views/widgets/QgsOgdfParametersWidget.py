#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz, Leon Nienhüser
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


from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout

from ...exceptions import FieldRequiredError
from ...network.protocol.build.available_handlers_pb2 import FieldInformation


class QgsOGDFParametersWidget(QWidget):
    """
    Dynamically creates and shows input widgets created from parameter list
    """

    toggleDialogVisibility = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.request = None

        # array of widget tuples (labelWidget, InputWidget)
        self.fieldWidgets = {}

        # set up layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # self._createParameterWidgets()

    def setParameterFields(self, request):
        """
        Sets parameter fields which should be shown as input widgets
        :param fields: fields dictionary
        """
        self.request = request
        self._createParameterWidgets()

    def getParameterFields(self):
        return self.request.fields

    def getParameterFieldsData(self):
        """
        Returns data of input widgets
        :exception ValueError if required field is not set
        :return: dictionary with field key and corresponding value
        """
        data = {}
        for key, field in self.request.fields.items():

            # store default value in data if widget is not implemented (possibly intended)
            if key not in self.fieldWidgets:
                data[key] = field.default
                continue

            fieldValue = None
            fieldWidget = self.fieldWidgets[key]
            inputWidget = fieldWidget.get("inputWidget", None)
            if inputWidget is not None:
                fieldValue = field.getWidgetData(inputWidget)

            # raise exception if required value is not set
            if field.required is True and fieldValue is None:
                raise FieldRequiredError(self.tr('Please enter a value into field "{}"').format(field.label))

            data[key] = fieldValue

        return data

    def _clearWidgets(self):
        """
        Removes all widgets from layout
        :return:
        """
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        self.fieldWidgets.clear()

    def _createParameterWidgets(self):
        """
        creates and shows all parameter fields as widgets
        :return:
        """
        self._clearWidgets()
        for key, field in self.request.fields.items():

            # label exists if not checkbox widget
            labelWidget = field.createLabel()
            try:
                inputWidget = field.createWidget(self)
            except AttributeError:
                continue

            # add widgets to layout
            if labelWidget is not None:
                self.layout.addWidget(labelWidget)
            if inputWidget is not None:
                self.layout.addWidget(inputWidget)

            self.fieldWidgets[key] = {
                "labelWidget": labelWidget,
                "inputWidget": inputWidget,
            }

        # init graph widgets
        if getattr(self.request, "graphKey", ""):
            self.graphChanged()

    def graphChanged(self):
        """
        Passes graph layer and graph to graph widgets
        :return:
        """
        # get first graph input
        graphLayer = None
        graph = None
        fieldWidget = self.fieldWidgets[self.request.graphKey]
        inputWidget = fieldWidget.get("inputWidget", None)
        layer = inputWidget.currentLayer()
        if layer is not None and layer.isValid():
            graphLayer = layer
            graph = layer.getGraph()

        # set or clear graph widgets
        for key in self.fieldWidgets:
            field = self.request.fields[key]
            fieldWidget = self.fieldWidgets[key]
            inputWidget = fieldWidget.get("inputWidget", None)
            if inputWidget is not None:
                # vertex or edge picker widget
                if field.type in [FieldInformation.FieldType.EDGE_ID, FieldInformation.FieldType.VERTEX_ID]:
                    inputWidget.clear()
                    inputWidget.setGraphLayer(graphLayer)
                # select edge cost function index
                elif field.type == FieldInformation.FieldType.EDGE_COSTS:
                    inputWidget.clear()
                    if graph is not None:
                        # todo: assumption that graph has at least one edge cost function
                        if graph.distanceStrategy == "Advanced":
                            for index in range(len(graph.edgeWeights)):
                                inputWidget.addItem(self.tr("Edge Cost Function {}").format(index + 1), index)
                        else:
                            inputWidget.addItem(self.tr("{} Costs").format(graph.distanceStrategy), 0)
                # select vertex cost function index
                elif field.type == FieldInformation.FieldType.VERTEX_COSTS:
                    inputWidget.clear()
                    if graph is not None:
                        for index in range(len(graph.vertexWeights)):
                            inputWidget.addItem(self.tr("Vertex Cost Function {}").format(index + 1), index)
