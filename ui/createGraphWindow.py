from .baseContentWindow import BaseContentWindow


class CreateGraphWindow(BaseContentWindow):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"

    def setupWindow(self):
        pass
