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

        self.dialog.ogdf_analysis_run_btn.clicked.connect(self.controller.runJob)

    def getJobName(self):
        return self.dialog.ogdf_analysis_job_input.text()

    def getGraph(self):
        return self.dialog.ogdf_analysis_graph_input.currentLayer()

    def getAnalysis(self):
        return self.dialog.ogdf_analysis_analysis_input.currentText(), self.dialog.create_graph_distance_input.currentData()

    def addAnalysis(self, analysis, userData=None):
        self.dialog.ogdf_analysis_analysis_input.addItem(analysis, userData)

    # advanced parameters

    def getCRS(self):
        return self.dialog.ogdf_analysis_crs_input.crs()

    def getStretch(self):
        return self.dialog.ogdf_analysis_stretch_input.int()

    def getStartNode(self):
        return self.dialog.ogdf_analysis_start_input.currentText(), self.dialog.ogdf_analysis_start_input.currentData()

    def addStartNode(self, startNode, userData=None):
        self.dialog.ogdf_analysis_start_input.addItem(startNode, userData)

    def addStartNodes(self, startNodes):
        self.dialog.ogdf_analysis_start_input.addItems(startNodes)

    def getEndNode(self):
        return self.dialog.ogdf_analysis_end_input.currentText(), self.dialog.ogdf_analysis_end_input.currentData()

    def addEndNode(self, endNode, userData=None):
        self.dialog.ogdf_analysis_end_input.addItem(endNode, userData)

    def addEndNodes(self, endNodes):
        self.dialog.ogdf_analysis_end_input.addItems(endNodes)

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

