from .baseContentView import BaseContentView
from ..controllers.graph import CreateGraphController


class CreateGraphView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "create graph"
        self.controller = CreateGraphController(self)

    def setupWindow(self):
        pass
