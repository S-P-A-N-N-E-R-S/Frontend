from .base import BaseController


class OGDFAnalysisController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OGDFAnalysisView
        """
        super().__init__(view)

        self.view.addAnalysis("t-Spanner")
        self.view.addAnalysis("minimum spanner")
        self.view.addAnalysis("shortest path")
        self.view.addAnalysis("steiner tree")
        self.view.addAnalysis("delaunay triangulation")

    def runJob(self):
        pass