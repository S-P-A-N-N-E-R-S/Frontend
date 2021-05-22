from .baseContentView import BaseContentView
from ..controllers.ogdfAnalysis import OGDFAnalysisController


class OGDFAnalysisView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "ogdf analysis"
        self.controller = OGDFAnalysisController(self)
