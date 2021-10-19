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

from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt

from .exampleDataView import ExampleDataView
from .createGraphView import CreateGraphView
from .ogdfAnalysisView import OGDFAnalysisView
from .jobsView import JobsView
from .optionsView import OptionsView
from .benchmarkView import BenchmarkView



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'PluginDialog.ui'))


class PluginDialog(QtWidgets.QDialog, FORM_CLASS):

    class Views(Enum):
        ExampleDataView = 0
        CreateGraphView = 1
        OGDFAnalysisView = 2
        BenchmarkView = 3
        JobsView = 4
        OptionsView = 5

    def __init__(self, parent=None):
        """Constructor."""
        super(PluginDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # left navigation
        self.menu_list.currentRowChanged.connect(self.stacked_content_views.setCurrentIndex)

        # display dialog as window with minimize and maximize buttons
        self.setWindowFlags(Qt.Window)

        # setup each content view
        self.contentViews = [
            ExampleDataView(self),
            CreateGraphView(self),
            OGDFAnalysisView(self),
            BenchmarkView(self),
            JobsView(self),
            OptionsView(self),
        ]

        # create example data as default
        self.menu_list.setCurrentRow(0)

    def setView(self, View):
        self.menu_list.setCurrentRow(View.value)
        self.activateWindow()
