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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QListWidgetItem

from .baseView import BaseView
from ..controllers.jobs import JobsController
from ..network import statusManager
from ..network.protocol.build.status_pb2 import StatusType
from ..helperFunctions import getVectorFileFilter


class JobsView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "jobs"
        self.controller = JobsController(self)

        self.STATUS_TEXTS = {
            StatusType.UNKNOWN_STATUS: self.tr("unknown"),
            StatusType.WAITING: self.tr("waiting"),
            StatusType.RUNNING: self.tr("running"),
            StatusType.SUCCESS: self.tr("success"),
            StatusType.FAILED: self.tr("failed"),
            StatusType.ABORTED: self.tr("aborted"),
        }

        # connect buttons to functions
        self.dialog.ogdf_jobs_fetch_result_btn.clicked.connect(self.controller.fetchResult)
        self.dialog.ogdf_jobs_fetch_origin_graph_btn.clicked.connect(self.controller.fetchOriginGraph)
        self.dialog.ogdf_jobs_refresh_btn.clicked.connect(self.controller.refreshJobs)
        self.dialog.ogdf_jobs_abort_btn.clicked.connect(self.controller.abortJob)
        self.dialog.ogdf_jobs_restart_btn.clicked.connect(self.controller.restartJob)

        # show output placeholder
        self.dialog.ogdf_jobs_output.lineEdit().setPlaceholderText("[Save to temporary layer]")

        # set save path formats
        self.dialog.ogdf_jobs_output.setFilter("GraphML (*.graphml );;" + getVectorFileFilter())

        # change job status text
        self.dialog.ogdf_jobs_list.currentItemChanged.connect(self._changeStatusText)

        # initial refresh jobs
        self.controller.refreshJobs()

    def _changeStatusText(self):
        if self.getCurrentJob() is not None:
            job = self.getCurrentJob()
            status = self.STATUS_TEXTS.get(job.status, "status not supported")
            self.setStatusText('job status is "{}"'.format(status))

    def addJob(self, job):
        jobName = job.getJobName()
        jobItem = QListWidgetItem(jobName)
        jobItem.setData(Qt.UserRole, job.jobId)
        self.dialog.ogdf_jobs_list.addItem(jobItem)

    def clearJobs(self):
        self.dialog.ogdf_jobs_list.clear()

    def removeJobRow(self, row):
        self.dialog.ogdf_jobs_list.takeItem(row)

    def removeCurrentJob(self):
        self.removeJobRow(self.getCurrentJobRow())

    def removeJob(self, jobName):
        # removes first matched item
        item = self.dialog.ogdf_jobs_list.findItems(jobName, Qt.MatchExactly)[0]
        self.dialog.ogdf_jobs_list.removeItemWidget(item)

    def getCurrentJobRow(self):
        return self.dialog.ogdf_jobs_list.currentRow()

    def getCurrentJob(self):
        item = self.dialog.ogdf_jobs_list.currentItem()
        if item is None:
            return None
        jobId = item.data(Qt.UserRole)
        return statusManager.getJobState(jobId)

    # status text

    def setStatusText(self, text):
        self.dialog.ogdf_jobs_status_text.setPlainText(text)

    def insertStatusText(self, text):
        self.dialog.ogdf_jobs_status_text.insertPlainText(text)

    def setStatusHtml(self, text):
        self.dialog.ogdf_jobs_status_text.setHtml(text)

    def insertStatusHtml(self, text):
        self.dialog.ogdf_jobs_status_text.insertHtml(text)

    def clearStatus(self):
        self.dialog.ogdf_jobs_status_text.clear()

    def getStatusText(self):
        return self.dialog.ogdf_jobs_status_text.toPlainText()

    def getStatusHtml(self):
        return self.dialog.ogdf_jobs_status_text.toHtml()

    # result text

    def setResultVisible(self, visible):
        self.dialog.ogdf_jobs_result_widget.setVisible(visible)

    def isResultVisible(self):
        self.dialog.ogdf_jobs_result_widget.isVisible()

    def setResultText(self, text):
        self.dialog.ogdf_jobs_result_textbrowser.setPlainText(text)

    def setResultHtml(self, text):
        self.dialog.ogdf_jobs_result_textbrowser.setHtml(text)

    def clearResult(self):
        self.dialog.ogdf_jobs_result_textbrowser.clear()

    def getResultText(self):
        return self.dialog.ogdf_jobs_result_textbrowser.toPlainText()

    def getResultHtml(self):
        return self.dialog.ogdf_jobs_result_textbrowser.toHtml()

    # destination output

    def setDestinationVisible(self, visible):
        """
        :type visible: bool
        :return:
        """
        self.dialog.ogdf_jobs_destination_widget.setVisible(visible)

    def isDestinationVisible(self):
        return self.dialog.ogdf_jobs_output.isVisible()

    def setDestinationFilter(self, destinationFilter):
        self.dialog.ogdf_jobs_output.setFilter(destinationFilter)

    def getDestinationFilePath(self):
        return self.dialog.ogdf_jobs_output.filePath()
