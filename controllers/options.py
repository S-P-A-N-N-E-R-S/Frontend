from .base import BaseController


class OptionsController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OptionsView
        """
        super().__init__(view)

    def saveOptions(self):
        pass
