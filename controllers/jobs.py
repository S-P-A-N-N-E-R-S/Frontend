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

from qgis.core import QgsSettings, QgsApplication, QgsTask, QgsMessageLog

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

    def _createTask(self, description, taskFunction, **kwargs):
        if JobsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous request is finished!"))
            return

        task = QgsTask.fromFunction(
            description,
            taskFunction,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            **kwargs,
            on_finished=self.requestCompleted
        )
        QgsApplication.taskManager().addTask(task)
        JobsController.activeTask = task
        self.view.showInfo(task.description())

    def fetchResult(self):
        if JobsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous result fetch is finished!"))
            return

        self.view.setResultHtml("")
        self.view.setResultVisible(False)

        job = self.view.getCurrentJob()
        if job is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        if not job.isSuccessful():
            self.view.showWarning(self.tr("Selected job status is not successful."))
            return

        self.view.setNetworkButtonsEnabled(False)

        # fetch result in background task
        self._createTask("Fetching job result...", self.resultFetchTask, job=job)

    def resultFetchTask(self, _task, host, port, tlsOption, job):
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
            "graphName": f"{job.getJobName()} - {self.tr('Result')}",
            "job": job,
        }

    def fetchOriginGraph(self):
        job = self.view.getCurrentJob()
        if job is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        # todo: Check if job has a graph

        self.view.setNetworkButtonsEnabled(False)

        # fetch origin graph in background task
        self._createTask(self.tr("Fetching origin graph..."), self.fetchOriginGraphTask, job=job)

    def fetchOriginGraphTask(self, _task, host, port, tlsOption, job):
        try:
            with Client(host, port, tlsOption=tlsOption) as client:
                response = client.getOriginGraph(job.jobId)
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

        # if response contains a graph: show it in qgis
        try:
            graph = response.getGraph()
        except AttributeError:
            graph = None

        return {
            "success": self.tr("Origin graph fetched!"),
            "graph": graph,
            "graphName": f"{job.getJobName()} - {self.tr('Origin')}",
            "job": job,
        }

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
        self._createTask("Refreshing job list...", self.refreshJobsTask, sortingOption=sortingOption,
                         sortingDirection=sortingDirection,)

    def refreshJobsTask(self, _task, host, port, tlsOption, sortingOption, sortingDirection):
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
            return {
                "error": str(error),
                "resetStatusText": True,
            }

    def abortJob(self):
        if JobsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous request is finished!"))
            return

        job = self.view.getCurrentJob()

        if job is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        if not job.isRunning():
            self.view.showWarning(self.tr("Selected job status is terminated."))
            return

        self.view.setNetworkButtonsEnabled(False)

        # abort job in background task
        self._createTask("Aborting job...", self.abortJobTask, job=job)

    def abortJobTask(self, _task, host, port, tlsOption, job):
        # get refreshed job states
        try:
            with Client(host, port, tlsOption) as client:
                client.abortJob(job.jobId)
                # return jobs
                return {
                    "success": self.tr("Job aborted!"),
                    "refreshJobs": True,
                }
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

    def deleteJob(self):
        if JobsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous request is finished!"))
            return

        job = self.view.getCurrentJob()

        if job is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        if job.isRunning():
            self.view.showWarning(self.tr("Please abort the running job first."))
            return

        self.view.setNetworkButtonsEnabled(False)

        # delete job in background task
        self._createTask("Deleting job...", self.deleteJobTask, job=job)

    def deleteJobTask(self, _task, host, port, tlsOption, job):
        # get refreshed job states
        try:
            with Client(host, port, tlsOption) as client:
                client.deleteJob(job.jobId)
                # return jobs
                return {
                    "success": self.tr("Job deleted!"),
                    "refreshJobs": True,
                }
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

    def requestCompleted(self, exception, result=None):
        """
        Processes the results of request task.
        """
        # first remove active task to allow a new request.
        JobsController.activeTask = None

        self.view.setNetworkButtonsEnabled(True)

        if exception is not None:
            QgsMessageLog.logMessage(exception)
            raise exception

        if result is None:
            # no result returned (probably manually canceled by the user)
            return

        if "success" in result:
            # refresh job list
            if "states" in result:
                for job in result["states"]:
                    self.view.addJob(job)
                self.view.refreshStatusText()

            # show result string
            if "resultString" in result:
                # show text results of response
                self.view.setResultHtml(result["resultString"])
                self.view.setResultVisible(result["resultString"] != "")

            # if response contains a graph: show it in qgis
            if "graph" in result and result["graph"]:
                graphLayer = QgsGraphLayer()
                graphLayer.setGraph(result["graph"])
                jobName = result["job"].getJobName()
                graphName = result.get("graphName", f"{jobName} - {self.tr('Result')}")
                success, errorMsg = helper.saveGraph(result["graph"], graphLayer, graphName,
                                                     self.view.getDestinationFilePath())
                if not success:
                    self.view.showError(str(errorMsg))

            if "refreshJobs" in result and result["refreshJobs"]:
                self.refreshJobs()

            self.view.showSuccess(result["success"])

        if "error" in result:
            if "resetStatusText" in result and result["resetStatusText"]:
                self.view.resetStatusText()
            self.view.showError(str(result["error"]), self.tr("Network Error"))
