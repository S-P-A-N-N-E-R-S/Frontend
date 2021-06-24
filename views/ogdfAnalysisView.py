from .baseContentView import BaseContentView
from ..controllers.ogdfAnalysis import OGDFAnalysisController

from qgis.core import QgsMapLayerProxyModel


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

        self.dialog.ogdf_analysis_run_btn.clicked.connect(self.controller.runJob)

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

    def getAnalysis(self):
        return self.dialog.ogdf_analysis_analysis_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def addAnalysis(self, analysis, userData=None):
        self.dialog.ogdf_analysis_analysis_input.addItem(analysis, userData)

    # advanced parameters

    def getCRS(self):
        return self.dialog.ogdf_analysis_crs_input.crs()

    def getStretch(self):
        return self.dialog.ogdf_analysis_stretch_input.value()

    def getStartNode(self):
        return self.dialog.ogdf_analysis_start_input.value()

    def getEndNode(self):
        return self.dialog.ogdf_analysis_end_input.value()

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

