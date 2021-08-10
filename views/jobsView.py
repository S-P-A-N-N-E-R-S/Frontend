from .baseContentView import BaseContentView
from ..controllers.jobs import JobsController
from ..helperFunctions import getVectorFileFilter

from PyQt5.QtCore import Qt


class JobsView(BaseContentView):

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

        # initial refresh jobs
        self.controller.refreshJobs()

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

    def setDestinationFilter(self, filter):
        self.dialog.ogdf_jobs_output.setFilter(filter)

    def getDestinationFilePath(self):
        return self.dialog.ogdf_jobs_output.filePath()

