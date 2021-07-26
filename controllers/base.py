from qgis.PyQt.QtCore import QObject


class BaseController(QObject):

    def __init__(self, view):
        super(BaseController, self).__init__()
        
        self.view = view
