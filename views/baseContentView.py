from qgis.gui import QgsMessageBar
from qgis.core import Qgis

from PyQt5.QtWidgets import QFileDialog, QAction


class BaseContentView:

    def __init__(self, dialog):
        """
        Base constuctor of a content window
        :param dialog: contains all ui elements
        """
        self.name = None
        self.dialog = dialog
        self.controller = None

        # setup message bar
        self.bar = QgsMessageBar()
        self.dialog.content_widget.layout().insertWidget(0, self.bar)

    def showError(self, msg):
        self.bar.pushMessage("Error", msg, level=Qgis.Critical)

    def showWarning(self, msg):
        self.bar.pushMessage("Warning", msg, level=Qgis.Warning)

    def showSuccess(self, msg):
        self.bar.pushMessage("Success", msg, level=Qgis.Success)

    def showInfo(self, msg):
        self.bar.pushMessage("Info", msg, level=Qgis.Info)

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
