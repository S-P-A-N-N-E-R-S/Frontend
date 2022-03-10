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

from qgis.PyQt.QtWidgets import QSizePolicy

from .baseView import BaseView
from ..controllers.ogdfAnalysis import OGDFAnalysisController
from ..network import handlerManager
from .widgets.ogdfParametersWidget import OGDFParametersWidget
from .widgets.analysisTreeView import AnalysisTreeView


class OGDFAnalysisView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "ogdf analysis"

        # # setup graph input
        # self.dialog.ogdf_analysis_graph_input.setFilters(QgsMapLayerProxyModel.PluginLayer)
        #
        # # set null layer as default
        # self.dialog.ogdf_analysis_graph_input.setCurrentIndex(0)

        # # set up graph file upload
        # self.dialog.ogdf_analysis_graph_input_tools.clicked.connect(
        #     lambda: self._browseFile("ogdf_analysis_graph_input", "GraphML (*.graphml)")
        # )

        # set up analysis tree view
        self.analysisTreeView = AnalysisTreeView()
        self.analysisTreeView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.analysisTreeView.setToolTip(self.tr("Select an analysis"))
        self.dialog.ogdf_analysis_analysis_analysis_tree_widget.layout().addWidget(self.analysisTreeView)

        # set up analysis parameter widget
        layout = self.dialog.ogdf_analysis_parameters_box.layout()
        self.ogdfParametersWidget = OGDFParametersWidget()
        self.ogdfParametersWidget.toggleDialogVisibility.connect(lambda visible: self.setMinimized(not visible))
        layout.addWidget(self.ogdfParametersWidget)
        self.dialog.ogdf_analysis_parameters_box.hide()

        # change analysis parameters
        self.analysisTreeView.analysisSelected.connect(self._analysisChanged)
        self.analysisTreeView.analysisDeselected.connect(self.dialog.ogdf_analysis_parameters_box.hide)

        self.controller = OGDFAnalysisController(self)
        self.dialog.ogdf_analysis_refresh_btn.clicked.connect(self.controller.refreshAnalysisList)
        self.dialog.ogdf_analysis_run_btn.clicked.connect(self.controller.runJob)

    def _analysisChanged(self):
        request = self.getAnalysis()
        if request:
            self.setParameterFields(request)
            # show description
            self.setDescriptionHtml(request.description)
            self.setDescriptionVisible(request.description != "")
            # show parameters
            self.dialog.ogdf_analysis_parameters_box.show()

    def getJobName(self):
        return self.dialog.ogdf_analysis_job_input.text()

    def getAnalysis(self):
        _requestName, requestKey = self.analysisTreeView.getAnalysis()
        return handlerManager.getRequestHandler(requestKey)

    def analysisListEmpty(self):
        return handlerManager.handlerListEmpty()

    def addAnalysis(self, analysis, userData=None):
        self.analysisTreeView.addAnalysis(analysis, userData)

    def clearAnalysisList(self):
        self.dialog.ogdf_analysis_parameters_box.hide()
        self.analysisTreeView.removeAllAnalysis()

    # analysis parameters

    def setParameterFields(self, request):
        """
        Sets parameter fields which should be shown as input widgets
        :param request: request instance
        """
        self.ogdfParametersWidget.setParameterFields(request)

    def getParameterFieldsData(self):
        """
        Returns ogdf parameter inputs data
        :exception FieldRequiredError if required field is not set
        :return: dictionary with field key and corresponding value
        """
        return self.ogdfParametersWidget.getParameterFieldsData()

    # description text

    def setDescriptionVisible(self, visible):
        self.dialog.ogdf_analysis_description_textbrowser.setVisible(visible)

    def isDescriptionVisible(self):
        self.dialog.ogdf_analysis_description_textbrowser.isVisible()

    def setDescriptionText(self, text):
        self.dialog.ogdf_analysis_description_textbrowser.setPlainText(text)

    def setDescriptionHtml(self, text):
        self.dialog.ogdf_analysis_description_textbrowser.setHtml(text)

    def clearDescription(self):
        self.dialog.ogdf_analysis_description_textbrowser.clear()

    def getDescriptionText(self):
        return self.dialog.ogdf_analysis_description_textbrowser.toPlainText()

    def getDescriptionHtml(self):
        return self.dialog.ogdf_analysis_description_textbrowser.toHtml()

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

    def setNetworkButtonsEnabled(self, enabled):
        self.dialog.ogdf_analysis_run_btn.setEnabled(enabled)
        self.dialog.ogdf_analysis_refresh_btn.setEnabled(enabled)
