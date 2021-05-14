from .baseContentWindow import BaseContentWindow


class ExampleDataWindow(BaseContentWindow):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "example data"

    def setupWindow(self):
        pass
