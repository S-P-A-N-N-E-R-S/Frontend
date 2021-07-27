from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtXml import *
from qgis.PyQt.QtCore import *

from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

from .views.pluginDialog import PluginDialog
from .helperFunctions import getImagePath, getPluginPath

from .models.QgsGraphLayer import QgsGraphLayer, QgsGraphLayerType, QgsGraphDataProvider

import os

class ProtoPlugin:

    def __init__(self, iface):
        """
        Constructor
        :type iface: QgisInterface
        """
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.initActions()

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('ProtoPlugin', message)

    def initActions(self):
        self.exampleAction = QAction(self.tr("Create example data"), self.iface.mainWindow())
        self.exampleAction.triggered.connect(lambda: self.openView(PluginDialog.Views.ExampleDataView))
        self.exampleAction.setWhatsThis(self.tr("Create example data"))
        self.exampleAction.setStatusTip(self.tr("Create example data"))

        self.graphAction = QAction(self.tr("Create graph"), self.iface.mainWindow())
        self.graphAction.triggered.connect(lambda: self.openView(PluginDialog.Views.CreateGraphView))
        self.graphAction.setWhatsThis(self.tr("Create graph"))
        self.graphAction.setStatusTip(self.tr("Create graph"))

        self.ogdfAnalysisAction = QAction(self.tr("OGDF analysis"), self.iface.mainWindow())
        self.ogdfAnalysisAction.triggered.connect(lambda: self.openView(PluginDialog.Views.OGDFAnalysisView))
        self.ogdfAnalysisAction.setWhatsThis(self.tr("OGDF analysis"))
        self.ogdfAnalysisAction.setStatusTip(self.tr("OGDF analysis"))

        self.ogdfJobsAction = QAction(self.tr("OGDF jobs"), self.iface.mainWindow())
        self.ogdfJobsAction.triggered.connect(lambda: self.openView(PluginDialog.Views.JobsView))
        self.ogdfJobsAction.setWhatsThis(self.tr("OGDF jobs"))
        self.ogdfJobsAction.setStatusTip(self.tr("OGDF jobs"))

        self.optionsAction = QAction(self.tr("Options"), self.iface.mainWindow())
        self.optionsAction.triggered.connect(lambda: self.openView(PluginDialog.Views.OptionsView))
        self.optionsAction.setWhatsThis(self.tr("Options"))
        self.optionsAction.setStatusTip(self.tr("Options"))

        self.defaultAction = QAction(QIcon(getImagePath("icon.png")), self.tr("Create example data"), self.iface.mainWindow())
        self.defaultAction.triggered.connect(lambda: self.openView(PluginDialog.Views.ExampleDataView))
        self.defaultAction.setWhatsThis(self.tr("Create example data"))
        self.defaultAction.setStatusTip(self.tr("Create example data"))

    def initGui(self):
        QgsApplication.pluginLayerRegistry().addPluginLayerType(QgsGraphLayerType())

        QgsProviderRegistry.instance().registerProvider(QgsProviderMetadata(QgsGraphDataProvider.providerKey(),
                                                                            QgsGraphDataProvider.description(),
                                                                            QgsGraphDataProvider.createProvider()))

        # re-read and therefore reload plugin layers after adding QgsGraphLayerType to PluginLayerRegistry
        self.reloadPluginLayers()

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

        QgsApplication.pluginLayerRegistry().removePluginLayerType(QgsGraphLayer.LAYER_TYPE)

    def reloadPluginLayers(self):
        """Re-reads and reloads plugin layers
        """
        # if project is empty
        if QgsProject.instance().baseName() == "":
            return False

        wasZipped = False
        if not QgsProject.instance().isZipped():
            readFileName = QgsProject.instance().absoluteFilePath()
        else:
            # temporarily unzip qgz to qgs
            directory = QgsProject.instance().absolutePath() + "/" + QgsProject.instance().baseName()
            if not os.path.exists(directory):
                os.makedirs(directory)
            QgsZipUtils.unzip(QgsProject.instance().absoluteFilePath(), directory)

            readFileName = directory + "/" + QgsProject.instance().baseName() + ".qgs"

            wasZipped = True

        # read def. not zipped project file
        with open(readFileName, 'r') as projectFile:
            projectDocument = QDomDocument()
            projectDocument.setContent(projectFile.read())

            # for every maplayer node in project file
            mapLayerNodeList = projectDocument.elementsByTagName("maplayer")
            for mapLayerNodeId in range(mapLayerNodeList.count()):
                mapLayerNode = mapLayerNodeList.at(mapLayerNodeId)

                # check if maplayer is a plugin layer
                mapLayerElem = mapLayerNode.toElement()
                if mapLayerElem.attribute("type") == "plugin":
                    # re-read plugin layer from node
                    QgsProject.instance().readLayer(mapLayerNode)

        # delete unzipped directory
        if wasZipped:
            os.remove(directory + "/" + QgsProject.instance().baseName() + ".qgd")
            os.remove(directory + "/" + QgsProject.instance().baseName() + ".qgs")
            os.rmdir(directory)
            