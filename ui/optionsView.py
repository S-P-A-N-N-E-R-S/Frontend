from .baseContentView import BaseContentView


class OptionsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"

    def setupWindow(self):
        pass