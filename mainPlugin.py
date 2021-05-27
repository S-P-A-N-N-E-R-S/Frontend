from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import QVariant

from .GraphBuilder import GraphBuilder
from qgis.core import *
from qgis.gui import *
from qgis.analysis import *
from .PGGraph import PGGraph
from . import resources

from .views.pluginDialog import PluginDialog
from .helperFunctions import getImagePath, getPluginPath


class ProtoPlugin:

    def __init__(self, iface):
        """
        Constructor
        :type iface: QgisInterface
        """
        self.iface = iface
        self.initActions()

    def initActions(self):
        self.exampleAction = QAction("Create example data", self.iface.mainWindow())
        self.exampleAction.triggered.connect(lambda: self.openView(PluginDialog.Views.ExampleDataView))
        self.exampleAction.setWhatsThis("Create example data")
        self.exampleAction.setStatusTip("Create example data")

        self.graphAction = QAction("Create graph", self.iface.mainWindow())
        self.graphAction.triggered.connect(lambda: self.openView(PluginDialog.Views.CreateGraphView))
        self.graphAction.setWhatsThis("Create graph")
        self.graphAction.setStatusTip("Create graph")

        self.ogdfAnalysisAction = QAction("OGDF analysis", self.iface.mainWindow())
        self.ogdfAnalysisAction.triggered.connect(lambda: self.openView(PluginDialog.Views.OGDFAnalysisView))
        self.ogdfAnalysisAction.setWhatsThis("OGDF analysis")
        self.ogdfAnalysisAction.setStatusTip("OGDF analysis")

        self.ogdfJobsAction = QAction("OGDF jobs", self.iface.mainWindow())
        self.ogdfJobsAction.triggered.connect(lambda: self.openView(PluginDialog.Views.JobsView))
        self.ogdfJobsAction.setWhatsThis("OGDF jobs")
        self.ogdfJobsAction.setStatusTip("OGDF jobs")

        self.optionsAction = QAction("Options", self.iface.mainWindow())
        self.optionsAction.triggered.connect(lambda: self.openView(PluginDialog.Views.OptionsView))
        self.optionsAction.setWhatsThis("Options")
        self.optionsAction.setStatusTip("Options")

        self.defaultAction = QAction(QIcon(getImagePath("icon.png")), "Create example data", self.iface.mainWindow())
        self.defaultAction.triggered.connect(lambda: self.openView(PluginDialog.Views.ExampleDataView))
        self.defaultAction.setWhatsThis("Create example data")
        self.defaultAction.setStatusTip("Create example data")

    def initGui(self):
        # create menu
        menu = QMenu("Proto Plugin")
        menu.setIcon(QIcon(getImagePath("icon.png")))
        menu.addAction(self.exampleAction)
        menu.addAction(self.graphAction)
        menu.addAction(self.ogdfAnalysisAction)
        menu.addAction(self.ogdfJobsAction)
        menu.addAction(self.optionsAction)
        self.menuAction = menu.menuAction()

        # create toolbar entry
        self.toolBarButton = QToolButton()
        self.toolBarButton.setMenu(menu)
        self.toolBarButton.setDefaultAction(self.defaultAction)
        self.toolBarButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolBarAction = self.iface.addToolBarWidget(self.toolBarButton)

        # create menu entry
        plugin_menu = self.iface.pluginMenu()
        plugin_menu.addMenu(menu)

    def openView(self, view):
        dialog = PluginDialog()
        dialog.setView(view)
        dialog.exec()

    def unload(self):
        # remove toolbar entry
        self.iface.removeToolBarIcon(self.toolBarAction)

        # remove menu entry
        plugin_menu = self.iface.pluginMenu()
        plugin_menu.removeAction(self.menuAction)