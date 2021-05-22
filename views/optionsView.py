from .baseContentView import BaseContentView
from ..controllers.options import OptionsController


class OptionsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"
        self.controller = OptionsController(self)
