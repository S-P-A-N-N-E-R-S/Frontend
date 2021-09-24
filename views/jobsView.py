from .baseContentView import BaseContentView
from ..controllers.jobs import JobsController
from ..helperFunctions import getVectorFileFilter

from qgis.PyQt.QtCore import Qt

from qgis.PyQt.QtWidgets import QListWidgetItem


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

        # change job status text
        self.dialog.ogdf_jobs_list.currentItemChanged.connect(self._changeStatusText)

        # initial refresh jobs
        self.controller.refreshJobs()

    def _changeStatusText(self):
        if self.getCurrentJob() is not None:
            job, status = self.getCurrentJob()
            self.setStatusText('job status is "{}"'.format(status))

    def addJob(self, jobName, jobData=None):
        jobItem = QListWidgetItem(jobName)
        jobItem.setData(Qt.UserRole, jobData)
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
        return item.text(), item.data(Qt.UserRole)

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

