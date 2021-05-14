from .baseContentView import BaseContentView


class ExampleDataView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "example data"

    def setupWindow(self):
        pass
