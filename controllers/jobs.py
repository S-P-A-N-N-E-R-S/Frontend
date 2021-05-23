from .base import BaseController


class JobsController(BaseController):

    def __init__(self, view):
        super().__init__(view)

        self.view.setOutputVisible(False)

    def saveResults(self):
        pass

    def refreshJobs(self):
        self.view.clearJobs()

        # dummy jobs
        self.view.addJob("Job 1")
        self.view.addJob("Job 2")
        self.view.addJob("Job 3")

    def abortJob(self):
        pass

    def restartJob(self):
        pass
