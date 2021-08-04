from .baseContentView import BaseContentView
from ..controllers.ogdfAnalysis import OGDFAnalysisController
from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer
from .widgets.QgsGraphEdgePickerWidget import QgsGraphEdgePickerWidget
from .widgets.QgsGraphVertexPickerWidget import QgsGraphVertexPickerWidget

from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QLabel

import os


class OGDFAnalysisView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "ogdf analysis"
        self.controller = OGDFAnalysisController(self)

        # setup graph input
        self.dialog.ogdf_analysis_graph_input.setFilters(QgsMapLayerProxyModel.PluginLayer)

        # set up graph file upload
        self.dialog.ogdf_analysis_graph_input_tools.clicked.connect(
            lambda: self._browseFile("ogdf_analysis_graph_input", "GraphML (*.graphml)")
        )

        # set up analysis parameters
        layout = self.dialog.ogdf_analysis_parameters_groupbox.layout()
        self.startNodeLabel = QLabel(self.tr("Start node"))
        self.startNodePicker = QgsGraphVertexPickerWidget()

        self.endNodeLabel = QLabel(self.tr("End node"))
        self.endNodePicker = QgsGraphVertexPickerWidget()
        layout.addWidget(self.startNodeLabel)
        layout.addWidget(self.startNodePicker)
        layout.addWidget(self.endNodeLabel)
        layout.addWidget(self.endNodePicker)

        # add graph to picker widgets
        self.dialog.ogdf_analysis_graph_input.currentIndexChanged.connect(self._inputChanged)
        self._inputChanged()

        self.dialog.ogdf_analysis_run_btn.clicked.connect(self.controller.runJob)

    def _inputChanged(self):
        """
        Sets the graph into the parameter widgets
        :return:
        """
        self.startNodePicker.clear()
        self.endNodePicker.clear()

        graphLayer = self.getInputLayer()
        if graphLayer is not None:
            self.startNodePicker.setGraphLayer(graphLayer)
            self.endNodePicker.setGraphLayer(graphLayer)
        else:
            graph = self.getGraph()
            self.startNodePicker.setGraph(graph)
            self.endNodePicker.setGraph(graph)

    def getJobName(self):
        return self.dialog.ogdf_analysis_job_input.text()

    def hasInput(self):
        return self.dialog.ogdf_analysis_graph_input.count() > 0

    def isInputLayer(self):
        """
        True: if input is layer
        False: if input is path
        :return:
        """
        if self.dialog.ogdf_analysis_graph_input.currentLayer():
            return True
        return False

    def getInputLayer(self):
        """
        Returns the current selected layer or none if path is selected
        :return: Layer or None if path is selected
        """
        return self.dialog.ogdf_analysis_graph_input.currentLayer()

    def getInputPath(self):
        """
        Returns input path of selected file path in layer combobox
        :return: Path to file or None if layer is selected
        """
        # assumed that only one additional item is inserted
        if self.hasInput() and not self.isInputLayer():
            return self.dialog.ogdf_analysis_graph_input.additionalItems()[0]
        return None

    def getGraph(self):
        """
        Gets the graph containing in input. Return none if input has no graph
        :return:
        """
        if self.hasInput():
            if self.isInputLayer():
                # return graph from graph layer
                graphLayer = self.getInputLayer()
                if isinstance(graphLayer, QgsGraphLayer) and graphLayer.isValid():
                    return graphLayer.getGraph()
            else:
                # if file path as input
                path = self.getInputPath()
                fileName, extension = os.path.splitext(path)
                if extension == ".graphml":
                    graph = ExtGraph()
                    graph.readGraphML(path)
                    return graph
        return None

    def getAnalysis(self):
        return self.dialog.ogdf_analysis_analysis_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def addAnalysis(self, analysis, userData=None):
        self.dialog.ogdf_analysis_analysis_input.addItem(analysis, userData)

    # analysis parameters

    def getStartNode(self):
        """
        Returns vertex id
        :return:
        """
        return self.startNodePicker.getVertex()

    def getEndNode(self):
        """
        Returns vertex id
        :return:
        """
        return self.endNodePicker.getVertex()

    # log

    def setLogText(self, text):
        self.dialog.ogdf_analysis_log.setPlainText(text)

    def insertLogText(self, text):
        self.dialog.ogdf_analysis_log.insertPlainText(text)

    def setLogHtml(self, text):
        self.dialog.ogdf_analysis_log.setHtml(text)

    def insertLogHtml(self, text):
        self.dialog.ogdf_analysis_log.insertHtml(text)

    def clearLog(self):
        self.dialog.ogdf_analysis_log.clear()

    def getLogText(self):
        return self.dialog.ogdf_analysis_log.toPlainText()

    def getLogHtml(self):
        return self.dialog.ogdf_analysis_log.toHtml()

