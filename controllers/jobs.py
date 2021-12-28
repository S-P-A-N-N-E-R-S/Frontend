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

from qgis.core import QgsSettings

from .base import BaseController
from ..models.QgsGraphLayer import QgsGraphLayer
from .. import helperFunctions as helper

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError, ServerError


class JobsController(BaseController):

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
        self.view.setResultHtml("")
        self.view.setResultVisible(False)

        if self.view.getCurrentJob() is None:
            self.view.showWarning(self.tr("Please select a job."))
            return

        job = self.view.getCurrentJob()
        if not job.isSuccessful():
            self.view.showWarning(self.tr("Selected job status is not successful."))
            return

        # Get result from finished job
        try:
            with Client(helper.getHost(), helper.getPort()) as client:
                response = client.getJobResult(job.jobId)
        except (NetworkClientError, ParseError, ServerError) as error:
            self.view.showError(str(error), self.tr("Network Error"))
            return

        # if response contains a graph: show it in qgis
        try:
            graph = response.getGraph()
            graphLayer = QgsGraphLayer()
            graphLayer.setGraph(graph)
            success, errorMsg = helper.saveGraph(graph, graphLayer, f"{job.getJobName()} - {self.tr('Result')}", self.view.getDestinationFilePath())
            if not success:
                self.view.showError(errorMsg)
        except AttributeError:
            pass

        # show text results in response
        try:
            resultString = response.getResultString()
        except AttributeError:
            resultString = ""
        self.view.setResultHtml(resultString)
        self.view.setResultVisible(resultString != "")

        self.view.showSuccess(self.tr("Result fetched!"))

    def fetchOriginGraph(self):
        pass

    def refreshJobs(self):
        self.view.clearStatus()
        self.view.clearResult()
        self.view.clearJobs()
        self.view.setFetchStatusText()

        # get response
        try:
            with Client(helper.getHost(), helper.getPort()) as client:
                states = client.getJobStatus()
                # add jobs
                for job in states.values():
                    self.view.addJob(job)
                self.view.refreshStatusText()
        except (NetworkClientError, ParseError, ServerError) as error:
            self.view.resetStatusText()
            self.view.showError(str(error), self.tr("Network Error"))

    def abortJob(self):
        pass

    def restartJob(self):
        pass
