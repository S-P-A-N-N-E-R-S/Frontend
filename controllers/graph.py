from .base import BaseController


class CreateGraphController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: CreateGraphView
        """
        super().__init__(view)

        self.view.addDistance("euclidean")
        self.view.addDistance("shortest path")

        self.view.addRasterType("elevation")
        self.view.addRasterType("prohibited area")
        self.view.addRasterType("cost")
        self.view.addRasterType("rgb vector")

        self.view.addPolygonType("prohibited area")

    def createGraph(self):
        pass