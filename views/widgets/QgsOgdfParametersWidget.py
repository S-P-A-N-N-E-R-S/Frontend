from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QLabel

from qgis.gui import QgsMapLayerComboBox
from qgis.core import  QgsMapLayerProxyModel

from .QgsGraphEdgePickerWidget import QgsGraphEdgePickerWidget
from .QgsGraphVertexPickerWidget import QgsGraphVertexPickerWidget
from ...exceptions import FieldRequiredError

from ...network.protocol.build.available_handlers_pb2 import FieldInformation

import sys


class QgsOGDFParametersWidget(QWidget):
    """
    Dynamically creates and shows input widgets created from parameter list
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # contains functions to create a field widget based on field type
        self.FIELD_WIDGETS = {
            FieldInformation.FieldType.BOOL: self._createBoolWidget,
            FieldInformation.FieldType.INT: self._createIntWidget,
            FieldInformation.FieldType.DOUBLE: self._createDoubleWidget,
            FieldInformation.FieldType.STRING: self._createStringWidget,
            FieldInformation.FieldType.CHOICE: self._createChoiceWidget,
            FieldInformation.FieldType.GRAPH: self._createGraphWidget,
            FieldInformation.FieldType.EDGE_COSTS: self._createEdgeCostsWidget,
            FieldInformation.FieldType.VERTEX_COSTS: self._createVertexCostWidget,
            FieldInformation.FieldType.EDGE_ID: self._createEdgeWidget,
            FieldInformation.FieldType.VERTEX_ID: self._createVertexWidget,
        }

        # contains functions to get field data based on field type
        self.FIELD_DATA = {
            FieldInformation.FieldType.BOOL: self._getBoolData,
            FieldInformation.FieldType.INT: self._getIntData,
            FieldInformation.FieldType.DOUBLE: self._getDoubleData,
            FieldInformation.FieldType.STRING: self._getStringData,
            FieldInformation.FieldType.CHOICE: self._getChoiceData,
            FieldInformation.FieldType.GRAPH: self._getGraphData,
            FieldInformation.FieldType.EDGE_COSTS: self._getEdgeCostsData,
            FieldInformation.FieldType.VERTEX_COSTS: self._getVertexCostData,
            FieldInformation.FieldType.EDGE_ID: self._getEdgeData,
            FieldInformation.FieldType.VERTEX_ID: self._getVertexData,
        }

        self.fields = {}

        # array of widget tuples (labelWidget, InputWidget)
        self.fieldWidgets = {}

        # set up layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self._createParameterWidgets()

    def setParameterFields(self, fields):
        """
        Sets parameter fields which should be shown as input widgets
        :param fields: fields dictionary
        """
        self.fields = fields
        self._createParameterWidgets()

    def getParameterFields(self):
        return self.fields

    def getParameterFieldsData(self):
        """
        Returns data of input widgets
        :exception ValueError if required field is not set
        :return: dictionary with field key and corresponding value
        """
        data = {}
        for key in self.fields:
            field = self.fields[key]

            # store default value in data if widget is not implemented (possibly intended)
            if key not in self.fieldWidgets:
                data[key] = field.get("default")
                continue

            fieldValue = None
            fieldWidget = self.fieldWidgets[key]
            inputWidget = fieldWidget.get("inputWidget", None)
            if inputWidget is not None:
                dataFunction = self.FIELD_DATA.get(field.get("type"))
                fieldValue = dataFunction(inputWidget)

            # raise exception if required value is not set
            if field.get("required", False) is True and fieldValue is None:
                raise FieldRequiredError(self.tr('Please enter a value into field "{}"').format(field.get("label")))

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
        for key in self.fields:
            field = self.fields[key]

            # skip field if widget of corresponding field type is not implemented (possibly intended)
            if field.get("type") not in self.FIELD_WIDGETS:
                continue

            widgetFunction = self.FIELD_WIDGETS.get(field.get("type"), None)

            # label exists if not checkbox widget
            labelWidget = QLabel(field.get("label")) if field.get("type") != FieldInformation.FieldType.BOOL else None
            inputWidget = widgetFunction(field)

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
        self._graphChanged()

    def _graphChanged(self):
        """
        Passes graph layer and graph to graph widgets
        :return:
        """
        # get first graph input
        graphLayer = None
        graph = None
        for key in self.fieldWidgets:
            field = self.fields[key]
            fieldWidget = self.fieldWidgets[key]
            inputWidget = fieldWidget.get("inputWidget", None)
            if inputWidget is not None:
                # vertex or edge picker widget
                if field.get("type") == FieldInformation.FieldType.GRAPH:
                    layer = inputWidget.currentLayer()
                    if layer is not None and layer.isValid():
                        graphLayer = layer
                        graph = layer.getGraph()

        # set or clear graph widgets
        for key in self.fieldWidgets:
            field = self.fields[key]
            fieldWidget = self.fieldWidgets[key]
            inputWidget = fieldWidget.get("inputWidget", None)
            if inputWidget is not None:
                # vertex or edge picker widget
                if field.get("type") in [FieldInformation.FieldType.EDGE_ID, FieldInformation.FieldType.VERTEX_ID]:
                    inputWidget.clear()
                    inputWidget.setGraphLayer(graphLayer)
                # select edge cost function index
                elif field.get("type") == FieldInformation.FieldType.EDGE_COSTS:
                    inputWidget.clear()
                    if graph is not None:
                        # todo: assumption that graph has at least one edge cost function
                        numberFunctions = len(graph.edgeWeights) if len(graph.edgeWeights) > 0 else 1
                        for index in range(numberFunctions):
                            inputWidget.addItem(self.tr("Kanten-Kostenfunktion {}").format(index + 1), index)
                # select vertex cost function index
                elif field.get("type") == FieldInformation.FieldType.VERTEX_COSTS:
                    inputWidget.clear()
                    if graph is not None:
                        for index in range(len(graph.vertexWeights)):
                            inputWidget.addItem(self.tr("Vertex-Kostenfunktion {}").format(index + 1), index)

    # functions to create field widgets

    def _createBoolWidget(self, field):
        checkBoxWidget = QCheckBox(field.get("label", ""))
        checkBoxWidget.setChecked(field.get("default", False) is True)
        return checkBoxWidget

    def _createIntWidget(self, field):
        spinBoxWidget = QSpinBox()
        # highest minimum and maximum
        spinBoxWidget.setRange(-2147483648, 2147483647)
        if field.get("default"):
            spinBoxWidget.setValue(field.get("default"))
        return spinBoxWidget

    def _createDoubleWidget(self, field):
        spinBoxWidget = QDoubleSpinBox()
        # highest minimum and maximum
        spinBoxWidget.setRange(-sys.float_info.min, sys.float_info.max)
        spinBoxWidget.setDecimals(6)
        if field.get("default"):
            spinBoxWidget.setValue(field.get("default"))
        return spinBoxWidget

    def _createStringWidget(self, field):
        lineEditWidget = QLineEdit(str(field.get("default", "")))
        return lineEditWidget

    def _createChoiceWidget(self, field):
        comboBoxWidget = QComboBox()
        choices = field.get("choices")
        for choice in choices:
            choiceData = choices[choice]
            comboBoxWidget.addItem(choice, choiceData)
        # select default item if exist
        comboBoxWidget.setCurrentIndex(comboBoxWidget.findText(field.get("default")))
        return comboBoxWidget

    def _createGraphWidget(self, field):
        graphWidget = QgsMapLayerComboBox()
        graphWidget.setFilters(QgsMapLayerProxyModel.PluginLayer)
        graphWidget.setAllowEmptyLayer(True)
        graphWidget.setCurrentIndex(0)
        graphWidget.currentIndexChanged.connect(self._graphChanged)
        return graphWidget

    def _createEdgeCostsWidget(self, field):
        return QComboBox()

    def _createVertexCostWidget(self, field):
        return QComboBox()

    def _createEdgeWidget(self, field):
        return QgsGraphEdgePickerWidget()

    def _createVertexWidget(self, field):
        return QgsGraphVertexPickerWidget()

    # functions to get field data

    def _getBoolData(self, inputWidget):
        return inputWidget.isChecked()

    def _getIntData(self, inputWidget):
        return inputWidget.value()

    def _getDoubleData(self, inputWidget):
        return inputWidget.value()

    def _getStringData(self, inputWidget):
        return inputWidget.text()

    def _getChoiceData(self, inputWidget):
        return inputWidget.currentData()

    def _getGraphData(self, inputWidget):
        layer = inputWidget.currentLayer()
        if layer is not None and layer.isValid():
            return layer.getGraph()
        return None

    def _getEdgeCostsData(self, inputWidget):
        return inputWidget.currentData()

    def _getVertexCostData(self, inputWidget):
        return inputWidget.currentData()

    def _getEdgeData(self, inputWidget):
        return inputWidget.getEdge()

    def _getVertexData(self, inputWidget):
        return inputWidget.getVertex()
