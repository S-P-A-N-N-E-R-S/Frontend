#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Dennis Benz
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

from qgis.core import Qgis

from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QObject


class BaseView(QObject):
    """ Base class of all views """

    def __init__(self, dialog):
        """
        Base constructor of a view
        :param dialog: contains all ui elements
        """
        super().__init__()

        self.name = None
        self.dialog = dialog
        self.controller = None

    def setMinimized(self, minimized=True):
        """ Minimizes the plugin dialog """
        if minimized:
            self.dialog.showMinimized()
        else:
            self.dialog.showNormal()
            self.dialog.activateWindow()

    def showError(self, msg, title="Error"):
        """ Shows an error in the notification bar """
        self.dialog.messageBar.pushMessage(title, msg, level=Qgis.Critical)

    def showWarning(self, msg, title="Warning"):
        """ Shows a warning in the notification bar """
        self.dialog.messageBar.pushMessage(title, msg, level=Qgis.Warning)

    def showSuccess(self, msg, title="Success"):
        """ Shows a success in the notification bar """
        self.dialog.messageBar.pushMessage(title, msg, level=Qgis.Success)

    def showInfo(self, msg, title="Info"):
        """ Shows an info in the notification bar """
        self.dialog.messageBar.pushMessage(title, msg, level=Qgis.Info)

    def _browseFile(self, layerComboBox, fileTypes):
        """
        Allows to browse for a file and adds it to the QGSMapLayerComboBox
        :param layerComboBox: name of the QGSMapLayerComboBox
        :param filter: supported file types
        :return:
        """
        path, _selectedFilter = QFileDialog.getOpenFileName(filter=fileTypes)
        if path:
            comboBox = getattr(self.dialog, layerComboBox)
            comboBox.setAdditionalItems([path])
            comboBox.setCurrentIndex(comboBox.count() - 1)
