#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz, Timo Glane, Leon Nienhüser
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

from qgis.core import QgsSettings, QgsApplication, QgsTask

from .base import BaseController
from ..models.QgsGraphLayer import QgsGraphLayer
from .. import helperFunctions as helper

# client imports
from ..network.client import Client
from ..network import statusManager
from ..network.exceptions import NetworkClientError, ParseError, ServerError


class JobsController(BaseController):

    activeTask = None

    def __init__(self, view):
        """
        Constructor
        :type view: JobsView
        """
        super().__init__(view)

        self.settings = QgsSettings()

        self.lastJobId = -1

        self.view.setResultVisible(False)

    def fetchResult(self):
        if JobsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous result fetch is finished!"))
            return

        self.view.setResultHtml("")
        self.view.setResultVisible(False)

        if self.view.getCurrentJob() is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        job = self.view.getCurrentJob()
        if not job.isSuccessful():
            self.view.showWarning(self.tr("Selected job status is not successful."))
            return

        self.view.setNetworkButtonsEnabled(False)

        # fetch result in background task
        task = QgsTask.fromFunction(
            "Fetching job result...",
            self.createResultFetchTask,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            job=job,
            on_finished=self.resultFetchCompleted
        )
        QgsApplication.taskManager().addTask(task)
        JobsController.activeTask = task
        self.view.showInfo(task.description())

    def createResultFetchTask(self, _task, host, port, tlsOption, job):
        # Get result from finished job
        try:
            with Client(host, port, tlsOption) as client:
                response = client.getJobResult(job.jobId)
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

        try:
            graph = response.getGraph()
        except AttributeError:
            graph = None

        try:
            resultString = response.getResultString()
        except AttributeError:
            resultString = ""

        return {
            "success": self.tr("Result fetched!"),
            "resultString": resultString,
            "graph": graph,
            "job": job,
        }

    def resultFetchCompleted(self, exception, result=None):
        """
        Processes the results of the result fetch task.
        """
        # first remove active task to allow a new request.
        JobsController.activeTask = None

        self.view.setNetworkButtonsEnabled(True)

        if exception is None:
            if result is None:
                # no result returned (probably manually canceled by the user)
                return

            if "success" in result:
                self.view.showSuccess(result["success"])

                # show text results of response
                self.view.setResultHtml(result["resultString"])
                self.view.setResultVisible(result["resultString"] != "")

                # if response contains a graph: show it in qgis
                if "graph" in result and result["graph"]:
                    graphLayer = QgsGraphLayer()
                    graphLayer.setGraph(result["graph"])
                    jobName = result["job"].getJobName()
                    success, errorMsg = helper.saveGraph(result["graph"], graphLayer, f"{jobName} - {self.tr('Result')}", self.view.getDestinationFilePath())
                    if not success:
                        self.view.showError(str(errorMsg))
                self.view.showSuccess(result["success"])

            if "error" in result:
                self.view.showError(str(result["error"]), self.tr("Network Error"))
        else:
            raise exception

    def fetchOriginGraph(self):
        pass

    def refreshJobs(self):
        if JobsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous refresh is finished!"))
            return

        self.view.setNetworkButtonsEnabled(False)
        self.view.clearStatus()
        self.view.clearResult()
        self.view.clearJobs()
        self.view.setFetchStatusText()
        
        sortingOption = self.view.getSortingOption()
        sortingDirection = self.view.getSortingDirection()

        # fetch result in background task
        task = QgsTask.fromFunction(
            "Refreshing job list...",
            self.createRefreshJobsTask,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            sortingOption=sortingOption,
            sortingDirection=sortingDirection,
            on_finished=self.refreshJobsCompleted
        )
        QgsApplication.taskManager().addTask(task)
        JobsController.activeTask = task
        self.view.showInfo(task.description())

    def createRefreshJobsTask(self, _task, host, port, tlsOption, sortingOption, sortingDirection):
        # get refreshed job states
        try:
            with Client(host, port, tlsOption) as client:
                client.getJobStatus()
                states = statusManager.getSortedJobStates(sortingOption, sortingDirection)
                # return jobs
                return {
                    "success": self.tr("Job list refreshed!"),
                    "states": states,
                }
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

    def refreshJobsCompleted(self, exception, result=None):
        """
        Processes the results of the refresh jobs task.
        """
        # first remove active task to allow a new request.
        JobsController.activeTask = None

        self.view.setNetworkButtonsEnabled(True)

        if exception is None:
            if result is None:
                # no result returned (probably manually canceled by the user)
                return

            if "success" in result:
                for job in result["states"]:
                    self.view.addJob(job)
                self.view.refreshStatusText()
                self.view.showSuccess(result["success"])

            if "error" in result:
                self.view.resetStatusText()
                self.view.showError(str(result["error"]), self.tr("Network Error"))
        else:
            raise exception

    def abortJob(self):
        pass

    def restartJob(self):
        pass
