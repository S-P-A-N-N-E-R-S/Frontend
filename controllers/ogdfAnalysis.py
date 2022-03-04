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

import traceback

from qgis.core import QgsSettings, QgsApplication, QgsTask, QgsMessageLog, Qgis

from .base import BaseController
from .. import helperFunctions as helper
from ..exceptions import FieldRequiredError

# client imports
from ..network.client import Client
from ..network import parserManager, parserFetcher
from ..network.exceptions import NetworkClientError, ParseError, ServerError


class OGDFAnalysisController(BaseController):

    activeTask = None

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
        parserFetcher.instance().parsersRefreshed.connect(self.fetchHandlersCompleted)
        self.refreshAnalysisList()

    def runJob(self):
        if OGDFAnalysisController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous request is finished!"))
            return

        try:
            request = self.view.getAnalysis()
        except NetworkClientError:
            self.view.showError(self.tr("No analysis selected!"))
            return
        if request is None:
            self.view.showError(self.tr("No analysis selected!"))
            return

        # get user parameter fields data
        try:
            parameterFieldsData = self.view.getParameterFieldsData()
        except FieldRequiredError as error:
            self.view.showError(str(error))
            return

        self.view.setNetworkButtonsEnabled(False)

        # set field data into request
        request.resetData()

        for key in parameterFieldsData:
            fieldData = parameterFieldsData[key]
            request.setFieldData(key, fieldData)
        request.jobName = self.view.getJobName()

        # create request in background task
        task = QgsTask.fromFunction(
            "Creating job request...",
            self.createRequestTask,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            request=request,
            on_finished=self.requestCompleted
        )
        QgsApplication.taskManager().addTask(task)
        OGDFAnalysisController.activeTask = task
        self.view.showInfo(task.description())

    def createRequestTask(self, _task, host, port, tlsOption, request):
        """
        Performs a job request in a task.
        """
        try:
            with Client(host, port, tlsOption) as client:
                client.sendJobRequest(request)
                return {"success": self.tr("Job started!")}
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

    def requestCompleted(self, exception, result=None):
        """
        Processes the results of the request task.
        """
        # first remove active task to allow a new request.
        OGDFAnalysisController.activeTask = None

        self.view.setNetworkButtonsEnabled(True)

        if exception is None:
            if result is None:
                # no result returned (probably manually canceled by the user)
                return
            else:
                if "success" in result:
                    self.view.showSuccess(result["success"])
                elif "error" in result:
                    self.view.showError(str(result["error"]), self.tr("Network Error"))
        else:
            QgsMessageLog.logMessage(
                "Exception: {exception}\n Traceback (most recent call last):\n {traceback}".format(
                    exception=exception,
                    traceback="".join(traceback.format_tb(exception.__traceback__))
                ),
                level=Qgis.Critical
            )
            raise exception

    def refreshAnalysisList(self):
        self.view.clearAnalysisList()
        self.view.setNetworkButtonsEnabled(False)

        parserFetcher.instance().refreshParsers()

        self.view.showInfo("Refreshing algorithms...")

    def fetchHandlersCompleted(self, result=None):
        """
        Processes the results of the fetch handlers task.
        """
        self.view.clearAnalysisList()
        self.view.setNetworkButtonsEnabled(True)

        if not result.get("exception"):
            if result is None:
                # no result returned (probably manually canceled by the user)
                return
            else:
                if "success" in result:
                    for requestKey, request in parserManager.getRequestParsers().items():
                        self.view.addAnalysis(request.name, requestKey)
                    self.view.showSuccess(result["success"])

                elif "error" in result:
                    self.view.showError(str(result["error"]), self.tr("Network Error"))
        else:
            raise result["exception"]
