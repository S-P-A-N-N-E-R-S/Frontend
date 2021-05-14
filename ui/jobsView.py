from .baseContentView import BaseContentView


class JobsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "jobs"

    def setupWindow(self):
        pass
