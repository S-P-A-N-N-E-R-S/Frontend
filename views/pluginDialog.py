import os
from enum import Enum

from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt

from .exampleDataView import ExampleDataView
from .createGraphView import CreateGraphView
from .ogdfAnalysisView import OGDFAnalysisView
from .jobsView import JobsView
from .optionsView import OptionsView



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'PluginDialog.ui'))


class PluginDialog(QtWidgets.QDialog, FORM_CLASS):

    class Views(Enum):
        ExampleDataView = 0
        CreateGraphView = 1
        OGDFAnalysisView = 2
        JobsView = 3
        OptionsView = 4

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
        self.exampleView = ExampleDataView(self)
        self.graphView = CreateGraphView(self)
        self.analysisView = OGDFAnalysisView(self)
        self.jobsView = JobsView(self)
        self.optionsView = OptionsView(self)

        # create example data as default
        self.menu_list.setCurrentRow(0)

    def setView(self, View):
        self.menu_list.setCurrentRow(View.value)
        self.activateWindow()
