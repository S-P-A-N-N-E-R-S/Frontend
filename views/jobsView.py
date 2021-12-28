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

from PyQt5.QtWidgets import QStyle
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtWidgets import QListWidgetItem, QStyledItemDelegate, QStyleOptionViewItem

from .baseView import BaseView
from ..controllers.jobs import JobsController
from ..network import statusManager
from ..network.exceptions import NetworkClientError
from ..helperFunctions import getVectorFileFilter


class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Right
        option.decorationSize = QSize(20, 20)
        super().paint(painter, option, index)


class JobsView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "jobs"
        self.controller = JobsController(self)

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

        # enable mousetracking to enable hints on hover and align icons to the right
        self.dialog.ogdf_jobs_list.setMouseTracking(True)
        self.dialog.ogdf_jobs_list.setItemDelegate(ItemDelegate())

        # change job status text
        self.dialog.ogdf_jobs_list.currentItemChanged.connect(self._changeStatusText)

        # initial refresh jobs
        self.controller.refreshJobs()

    def setFetchStatusText(self):
        self.setStatusText("...")

    def resetStatusText(self):
        self.setStatusText("")

    def refreshStatusText(self):
        self._changeStatusText()

    def _changeStatusText(self):
        self.setResultHtml("")
        self.setResultVisible(False)

        job = self.getCurrentJob()
        if job is None:
            self.resetStatusText()
        else:
            self.setStatusText(job.getStatusText())

    def addJob(self, job):
        jobName = job.getJobName()
        jobItem = QListWidgetItem(jobName)
        jobItem.setData(Qt.UserRole, job.jobId)
        icon = self.dialog.ogdf_jobs_list.style().standardIcon(getattr(QStyle,job.getIconName()))
        jobItem.setIcon(icon)
        jobItem.setToolTip(f"Status: {job.getStatus()}")
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
            # If no items selected: Try getting the last selected job
            try:
                lastJob = statusManager.getJobState(self.controller.lastJobId)
            except NetworkClientError:
                return None
            try:
                item = self.dialog.ogdf_jobs_list.findItems(lastJob.getJobName(), Qt.MatchExactly)[0]
            except IndexError as error:
                self.controller.lastJobId = -1
                raise NetworkClientError("Can't refresh the status of the last selected job") from error
            self.dialog.ogdf_jobs_list.setCurrentItem(item)
            return lastJob

        jobId = item.data(Qt.UserRole)
        self.controller.lastJobId = jobId
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
