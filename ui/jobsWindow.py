from .baseContentWindow import BaseContentWindow


class JobsWindow(BaseContentWindow):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "jobs"

    def setupWindow(self):
        pass
