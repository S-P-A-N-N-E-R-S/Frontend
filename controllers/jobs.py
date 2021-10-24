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
from ..network.exceptions import NetworkClientError, ParseError
from ..network.protocol.build.available_handlers_pb2 import ResultInformation


class JobsController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: JobsView
        """
        super().__init__(view)

        self.settings = QgsSettings()

        self.view.setResultVisible(False)

    def fetchResult(self):
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
        except (NetworkClientError, ParseError) as error:
            self.view.showError(str(error), self.tr("Network Error"))
            return

        # show graph in qgis
        graphLayer = QgsGraphLayer()
        graphLayer.setGraph(response.getGraph())
        success, errorMsg = helper.saveGraph(response.getGraph(), graphLayer, f"{job.getJobName()} - {self.tr('Result')}", self.view.getDestinationFilePath())
        if not success:
            self.view.showError(errorMsg)

        # show text results in response
        resultString = ""
        for resultKey, resultData in response.data.items():
            result = response.results[resultKey]
            if result.type in [ResultInformation.HandlerReturnType.INT, ResultInformation.HandlerReturnType.DOUBLE,
                               ResultInformation.HandlerReturnType.STRING]:
                resultString += result.label + ": " + str(resultData) + "\n"
        self.view.setResultHtml(resultString)
        self.view.setResultVisible(resultString != "")

        self.view.showSuccess(self.tr("Result fetched!"))

    def fetchOriginGraph(self):
        pass

    def refreshJobs(self):
        self.view.clearJobs()

        # get response
        try:
            with Client(helper.getHost(), helper.getPort(), 1) as client:
                states = client.getJobStatus()
                # add jobs
                for job in states.values():
                    self.view.addJob(job)
        except (NetworkClientError, ParseError) as error:
            self.view.showError(str(error), self.tr("Network Error"))

    def abortJob(self):
        pass

    def restartJob(self):
        pass
