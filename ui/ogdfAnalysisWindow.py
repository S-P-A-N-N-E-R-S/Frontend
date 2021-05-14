from .baseContentWindow import BaseContentWindow


class OGDFAnalysisWindow(BaseContentWindow):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "ogdf analysis"

    def setupWindow(self):
        pass
