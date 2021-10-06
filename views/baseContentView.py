from qgis.gui import QgsMessageBar
from qgis.core import Qgis

from PyQt5.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QObject


class BaseContentView(QObject):

    def __init__(self, dialog):
        """
        Base constuctor of a content window
        :param dialog: contains all ui elements
        """
        super(BaseContentView, self).__init__()

        self.name = None
        self.dialog = dialog
        self.controller = None

        # setup message bar
        self.bar = QgsMessageBar()
        self.dialog.content_widget.layout().insertWidget(-1, self.bar)

    def setMinimized(self, minimized=True):
        """ Minimizes the plugin dialog """
        self.dialog.activateWindow() if minimized else self.dialog.showMinimized()

    def showError(self, msg, title="Error"):
        self.bar.pushMessage(title, msg, level=Qgis.Critical)

    def showWarning(self, msg, title="Warning"):
        self.bar.pushMessage(title, msg, level=Qgis.Warning)

    def showSuccess(self, msg, title="Success"):
        self.bar.pushMessage(title, msg, level=Qgis.Success)

    def showInfo(self, msg, title="Info"):
        self.bar.pushMessage(title, msg, level=Qgis.Info)

    def _browseFile(self, layerComboBox, filter):
        """
        Allows to browse for a file and adds it to the QGSMapLayerComboBox
        :param layerComboBox: name of the QGSMapLayerComboBox
        :param filter: supported file types
        :return:
        """
        path, selectedFilter = QFileDialog.getOpenFileName(filter=filter)
        if path:
            comboBox = getattr(self.dialog, layerComboBox)
            comboBox.setAdditionalItems([path])
            comboBox.setCurrentIndex(comboBox.count() - 1)
