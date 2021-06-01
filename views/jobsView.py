from .baseContentView import BaseContentView
from ..controllers.jobs import JobsController

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialogButtonBox


class JobsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "jobs"
        self.controller = JobsController(self)

        # reset progress
        self.resetProgress()

        # connect buttons to functions
        self.dialog.ogdf_jobs_refresh_btn.clicked.connect(self.controller.refreshJobs)
        self.dialog.ogdf_jobs_buttons.clicked.connect(self.__handleButtonBox)

        # initial refresh jobs
        self.controller.refreshJobs()

    def __handleButtonBox(self, btn):
        buttonBox = self.dialog.ogdf_jobs_buttons
        buttonRole = buttonBox.standardButton(btn)
        if buttonRole == QDialogButtonBox.Save:
            self.controller.saveResults()
        elif buttonRole == QDialogButtonBox.Abort:
            self.controller.abortJob()
        elif buttonRole == QDialogButtonBox.Retry:
            self.controller.restartJob()

    def addJob(self, jobName):
        self.dialog.ogdf_jobs_list.addItem(jobName)

    def addJobs(self, jobs):
        """
        :param jobs: job names
        :type jobs: list of strings
        :return:
        """
        self.dialog.ogdf_jobs_list.addItems(jobs)

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
        return item.text()

    # status text

    def setLogText(self, text):
        self.dialog.ogdf_jobs_status_text.setPlainText(text)

    def insertLogText(self, text):
        self.dialog.ogdf_jobs_status_text.insertPlainText(text)

    def setLogHtml(self, text):
        self.dialog.ogdf_jobs_status_text.setHtml(text)

    def insertLogHtml(self, text):
        self.dialog.ogdf_jobs_status_text.insertHtml(text)

    def clearLog(self):
        self.dialog.ogdf_jobs_status_text.clear()

    def getLogText(self):
        return self.dialog.ogdf_jobs_status_text.toPlainText()

    def getLogHtml(self):
        return self.dialog.ogdf_jobs_status_text.toHtml()

    # progressBar

    def setProgressMinimum(self, min):
        self.dialog.ogdf_jobs_progressbar.setMinimum(min)

    def setProgressMaximum(self, max):
        self.dialog.ogdf_jobs_progressbar.setMaximum(max)

    def getProgressMaximum(self):
        return self.dialog.ogdf_jobs_progressbar.maximum()

    def getProgressMinimum(self, max):
        return self.dialog.ogdf_jobs_progressbar.minimum()

    def setProgress(self, value):
        self.dialog.ogdf_jobs_progressbar.setValue(value)

    def getProgress(self):
        return self.dialog.ogdf_jobs_progressbar.value()

    def resetProgress(self):
        self.dialog.ogdf_jobs_progressbar.reset()

    # destination output

    def setOutputVisible(self, visible):
        """
        :type visible: bool
        :return:
        """
        self.dialog.ogdf_jobs_output_label.setVisible(visible)
        self.dialog.ogdf_jobs_output.setVisible(visible)

    def isOutputVisible(self):
        return self.dialog.ogdf_jobs_output.isVisible()

    def setOutputFilter(self, filter):
        self.dialog.ogdf_jobs_output.setFilter(filter)

    def getOutputFilePath(self):
        return self.dialog.ogdf_jobs_output.filePath()

