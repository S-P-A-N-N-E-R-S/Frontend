from .baseContentView import BaseContentView
from ..controllers.ogdfAnalysis import OGDFAnalysisController
from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer
from .widgets.QgsOgdfParametersWidget import QgsOGDFParametersWidget

from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QLabel

import os


class OGDFAnalysisView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "ogdf analysis"
        self.controller = OGDFAnalysisController(self)

        # # setup graph input
        # self.dialog.ogdf_analysis_graph_input.setFilters(QgsMapLayerProxyModel.PluginLayer)
        #
        # # set null layer as default
        # self.dialog.ogdf_analysis_graph_input.setCurrentIndex(0)

        # # set up graph file upload
        # self.dialog.ogdf_analysis_graph_input_tools.clicked.connect(
        #     lambda: self._browseFile("ogdf_analysis_graph_input", "GraphML (*.graphml)")
        # )

        # set up analysis parameter widget
        layout = self.dialog.ogdf_analysis_parameters_box.layout()
        self.ogdfParametersWidget = QgsOGDFParametersWidget()
        layout.addWidget(self.ogdfParametersWidget)

        # change analysis parameters
        self.dialog.ogdf_analysis_analysis_input.currentIndexChanged.connect(self._analysisChanged)

        self.dialog.ogdf_analysis_run_btn.clicked.connect(self.controller.runJob)

    def _analysisChanged(self):
        label, request = self.getAnalysis()
        self.setParameterFields(request.getFieldInfo())

    # def hasInput(self):
    #     """
    #     Returns true if input is not empty
    #     :return:
    #     """
    #     if self.dialog.ogdf_analysis_graph_input.currentLayer() is not None:
    #         return True
    #
    #     if len(self.dialog.ogdf_analysis_graph_input.additionalItems()) > 0:
    #         return self.dialog.ogdf_analysis_graph_input.currentText() == self.dialog.ogdf_analysis_graph_input.additionalItems()[0]
    #
    #     return False

    # def isInputLayer(self):
    #     """
    #     True: if input is layer
    #     False: if input is path or empty
    #     :return:
    #     """
    #     return self.dialog.ogdf_analysis_graph_input.currentLayer() is not None

    # def getInputLayer(self):
    #     """
    #     Returns the current selected layer or none if path or empty is selected
    #     :return: Layer or None if path or empty is selected
    #     """
    #     return self.dialog.ogdf_analysis_graph_input.currentLayer()

    # def getInputPath(self):
    #     """
    #     Returns input path of selected file path in layer combobox
    #     :return: Path to file or None if layer is selected
    #     """
    #     # assumed that only one additional item is inserted
    #     if self.hasInput() and not self.isInputLayer():
    #         return self.dialog.ogdf_analysis_graph_input.additionalItems()[0]
    #     return None

    # def getGraph(self):
    #     """
    #     Gets the graph containing in input. Return none if input has no graph
    #     :return:
    #     """
    #     if self.hasInput():
    #         if self.isInputLayer():
    #             # return graph from graph layer
    #             graphLayer = self.getInputLayer()
    #             if isinstance(graphLayer, QgsGraphLayer) and graphLayer.isValid():
    #                 return graphLayer.getGraph()
    #         else:
    #             # if file path as input
    #             path = self.getInputPath()
    #             fileName, extension = os.path.splitext(path)
    #             if extension == ".graphml":
    #                 graph = ExtGraph()
    #                 graph.readGraphML(path)
    #                 return graph
    #     return None

    def getAnalysis(self):
        return self.dialog.ogdf_analysis_analysis_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def addAnalysis(self, analysis, userData=None):
        self.dialog.ogdf_analysis_analysis_input.addItem(analysis, userData)

    # analysis parameters

    def setParameterFields(self, fields):
        """
        Sets parameter fields which should be shown as input widgets
        :param fields: fields dictionary
        """
        self.ogdfParametersWidget.setParameterFields(fields)

    def getParameterFieldsData(self):
        """
        Returns ogdf parameter inputs data
        :exception FieldRequiredError if required field is not set
        :return: dictionary with field key and corresponding value
        """
        return self.ogdfParametersWidget.getParameterFieldsData()

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
