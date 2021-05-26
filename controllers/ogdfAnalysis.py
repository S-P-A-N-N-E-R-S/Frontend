from .base import BaseController


class OGDFAnalysisController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OGDFAnalysisView
        """
        super().__init__(view)

        self.view.addAnalysis("Spanner")

    def runJob(self):
        pass