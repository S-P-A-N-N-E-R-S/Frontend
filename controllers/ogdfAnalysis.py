#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz, Leon Nienhüser
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

from qgis.core import QgsSettings, QgsApplication

from .base import BaseController
from ..exceptions import FieldRequiredError
from .. import helperFunctions as helper

# client imports
from ..network.client import Client
from ..network import parserManager
from ..network.exceptions import NetworkClientError, ParseError


class OGDFAnalysisController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OGDFAnalysisView
        """
        super().__init__(view)

        self.settings = QgsSettings()
        self.authManager = QgsApplication.authManager()

        # initial hide description text browser
        self.view.setDescriptionVisible(False)

        # add available analysis
        for requestKey, request in parserManager.getRequestParsers().items():
            self.view.addAnalysis(request.name, requestKey)

    def runJob(self):
        # todo: pass authId to client
        _authId = self.settings.value("ogdfplugin/authId")

        request = self.view.getAnalysis()
        if request is None:
            self.view.showError(self.tr("No analysis selected!"))
            return

        # get user parameter fields data
        try:
            parameterFieldsData = self.view.getParameterFieldsData()
        except FieldRequiredError as error:
            self.view.showError(str(error))
            return

        # set field data into request
        request.resetData()

        for key in parameterFieldsData:
            fieldData = parameterFieldsData[key]
            request.setFieldData(key, fieldData)
        request.jobName = self.view.getJobName()

        try:
            with Client(helper.getHost(), helper.getPort()) as client:
                client.sendJobRequest(request)
                self.view.showSuccess("Job started!")
        except (NetworkClientError, ParseError) as error:
            self.view.showError(str(error), self.tr("Network Error"))  # show error

    # def __getGraph(self):
    #     """
    #     Loads graph from input
    #     :return:
    #     """
    #     if not self.view.hasInput():
    #         self.view.showError(self.tr("Please select a graph!"))
    #         return None
    #
    #     if self.view.isInputLayer():
    #         # return graph from graph layer
    #         graphLayer = self.view.getInputLayer()
    #         if not isinstance(graphLayer, QgsGraphLayer):
    #             self.view.showError(self.tr("The selected layer is not a graph layer!"))
    #         if graphLayer.isValid():
    #             return graphLayer.getGraph()
    #         else:
    #             self.view.showError(self.tr("The selected graph layer is invalid!"))
    #     else:
    #         # if file path as input
    #         path = self.view.getInputPath()
    #         fileName, extension = os.path.splitext(path)
    #         if extension == ".graphml":
    #             graph = ExtGraph()
    #             graph.readGraphML(path)
    #             return graph
    #     return None
