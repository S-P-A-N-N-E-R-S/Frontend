from .baseContentView import BaseContentView


class OGDFAnalysisView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "ogdf analysis"

    def setupWindow(self):
        pass
