from .baseContentView import BaseContentView


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"

    def setupWindow(self):
        pass
