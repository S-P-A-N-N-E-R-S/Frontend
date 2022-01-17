# This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz
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

import os
from enum import Enum

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices

from qgis.gui import QgsMessageBar

from .. import helperFunctions as helper

from .resourceView import ResourceView
from .graphView import GraphView
from .ogdfAnalysisView import OGDFAnalysisView
from .jobsView import JobsView
from .optionsView import OptionsView
from .benchmarkView import BenchmarkView



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'PluginDialog.ui'))


class PluginDialog(QDialog, FORM_CLASS):

    class Views(Enum):
        ResourceView = 0
        GraphView = 1
        OGDFAnalysisView = 2
        BenchmarkView = 3
        JobsView = 4
        OptionsView = 5

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # left navigation
        self.menu_list.currentRowChanged.connect(self.changeViewIndex)

        # setup message bar
        self.bar = QgsMessageBar()
        self.content_widget.layout().insertWidget(1, self.bar)

        # set up help button
        self.footer_buttonbox.helpRequested.connect(self.showHelp)

        # display dialog as window with minimize and maximize buttons
        self.setWindowFlags(Qt.Window)

        # setup each content view
        self.resourceView = ResourceView(self)
        self.graphView = GraphView(self)
        self.analysisView = OGDFAnalysisView(self)
        self.benchmarkView = BenchmarkView(self)
        self.jobsView = JobsView(self)
        self.optionsView = OptionsView(self)

        # create example data as default
        self.menu_list.setCurrentRow(0)

    def showHelp(self):
        """ Opens help website in web browser """
        QDesktopServices.openUrl(QUrl(helper.getHelpUrl()))

    def setView(self, View):
        self.menu_list.setCurrentRow(View.value)
        self.activateWindow()

    def changeViewIndex(self, index):
        if index == self.Views.JobsView.value:
            self.jobsView.controller.refreshJobs()
        self.stacked_content_views.setCurrentIndex(index)
