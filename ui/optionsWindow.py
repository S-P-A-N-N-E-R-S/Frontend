from .baseContentWindow import BaseContentWindow


class OptionsWindow(BaseContentWindow):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"

    def setupWindow(self):
        pass