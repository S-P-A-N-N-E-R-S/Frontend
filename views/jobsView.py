from .baseContentView import BaseContentView
from ..controllers.jobs import JobsController


class JobsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "jobs"
        self.controller = JobsController(self)

