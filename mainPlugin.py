#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz, Tim Hartmann, Julian Wittker
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

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtXml import *
from qgis.PyQt.QtCore import *

from qgis.core import *
from qgis.gui import *
from qgis.analysis import *
from qgis.utils import *

from .views.pluginDialog import PluginDialog
from .helperFunctions import getImagePath

from .models.QgsGraphLayer import QgsGraphLayer, QgsGraphLayerType, QgsGraphDataProvider

import os, string, random


class OGDFPlugin:
    """
    This plugin provides the creation, visualization and modification of graphs.

    In addition, this plugin serves as a frontend for the backend that supports the execution of
    analyses on the created graphs.
    """

    def __init__(self, iface):
        """
        Constructor
        :type iface: QgisInterface
        """
        self.iface = iface
        self.dialog = None

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

        QgsProject.instance().layersWillBeRemoved.connect(self.deleteLayers)

        self.initActions()

    def tr(self, message):
        """
        Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('OGDFPlugin', message)

    def initActions(self):
        self.resourceAction = QAction(self.tr("Create from resource"), self.iface.mainWindow())
        self.resourceAction.triggered.connect(lambda: self.openView(PluginDialog.Views.ResourceView))
        self.resourceAction.setWhatsThis(self.tr("Create from resource"))
        self.resourceAction.setStatusTip(self.tr("Create from resource"))

        self.graphAction = QAction(self.tr("Create graph"), self.iface.mainWindow())
        self.graphAction.triggered.connect(lambda: self.openView(PluginDialog.Views.GraphView))
        self.graphAction.setWhatsThis(self.tr("Create graph"))
        self.graphAction.setStatusTip(self.tr("Create graph"))

        self.ogdfAnalysisAction = QAction(self.tr("OGDF analysis"), self.iface.mainWindow())
        self.ogdfAnalysisAction.triggered.connect(lambda: self.openView(PluginDialog.Views.OGDFAnalysisView))
        self.ogdfAnalysisAction.setWhatsThis(self.tr("OGDF analysis"))
        self.ogdfAnalysisAction.setStatusTip(self.tr("OGDF analysis"))

        self.benchmarksAction = QAction(self.tr("Benchmarks"), self.iface.mainWindow())
        self.benchmarksAction.triggered.connect(lambda: self.openView(PluginDialog.Views.BenchmarkView))
        self.benchmarksAction.setWhatsThis(self.tr("Benchmarks"))
        self.benchmarksAction.setStatusTip(self.tr("Benchmarks"))

        self.ogdfJobsAction = QAction(self.tr("OGDF jobs"), self.iface.mainWindow())
        self.ogdfJobsAction.triggered.connect(lambda: self.openView(PluginDialog.Views.JobsView))
        self.ogdfJobsAction.setWhatsThis(self.tr("OGDF jobs"))
        self.ogdfJobsAction.setStatusTip(self.tr("OGDF jobs"))

        self.optionsAction = QAction(self.tr("Options"), self.iface.mainWindow())
        self.optionsAction.triggered.connect(lambda: self.openView(PluginDialog.Views.OptionsView))
        self.optionsAction.setWhatsThis(self.tr("Options"))
        self.optionsAction.setStatusTip(self.tr("Options"))

        self.defaultAction = QAction(QIcon(getImagePath("icon.svg")), self.tr("Create from resource"), self.iface.mainWindow())
        self.defaultAction.triggered.connect(lambda: self.openView(PluginDialog.Views.ResourceView))
        self.defaultAction.setWhatsThis(self.tr("Create from resource"))
        self.defaultAction.setStatusTip(self.tr("Create from resource"))

    def initGui(self):
        self.iface.currentLayerChanged.connect(self.__layerChanged)

        # create menu
        menu = QMenu("OGDF Plugin")
        menu.setIcon(QIcon(getImagePath("icon.svg")))
        menu.addAction(self.resourceAction)
        menu.addAction(self.graphAction)
        menu.addAction(self.ogdfAnalysisAction)
        menu.addAction(self.benchmarksAction)
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

        # create toolbar entries for edit options if not already existing
        self.graphToolbar = None
        toolbars = iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            if toolbar.objectName() == "Graph ToolBar":
                self.graphToolbar = toolbar
                break
        if not self.graphToolbar:
            self.graphToolbar = self.iface.mainWindow().addToolBar("Graph ToolBar")
            self.graphToolbar.setObjectName("Graph ToolBar")

        self.zoomLayerAction = QAction(QIcon(getImagePath("Zoom_To_Layer_Icon.svg")), self.tr("Zoom to Layer"))
        # use whatsThis() to identify triggered action
        self.zoomLayerAction.setToolTip(self.tr("Zoom to Layer"))
        self.zoomLayerAction.setWhatsThis("Zoom to Layer")
        self.graphToolbar.addAction(self.zoomLayerAction)

        self.toggleEditAction = QAction(QIcon(getImagePath("Toggle_Edit_Icon.svg")), self.tr("Toggle Edit"))
        self.toggleEditAction.setToolTip(self.tr("Toggle Edit"))
        self.toggleEditAction.setWhatsThis("Toggle Edit")
        self.toggleEditAction.setCheckable(True)
        self.graphToolbar.addAction(self.toggleEditAction)

        self.selectVertexAction = QAction(QIcon(getImagePath("Select_Vertex_Icon.svg")), self.tr("Select Vertex"))
        self.selectVertexAction.setToolTip(self.tr("Select Vertex"))
        self.selectVertexAction.setWhatsThis("Select Vertex")
        self.selectVertexAction.setEnabled(False)
        self.selectVertexAction.setCheckable(True)
        self.graphToolbar.addAction(self.selectVertexAction)

        self.deleteVertexAction = QAction(QIcon(getImagePath("Delete_Vertex_Icon.svg")), self.tr("Delete Vertex"))
        self.deleteVertexAction.setToolTip(self.tr("Delete Vertex"))
        self.deleteVertexAction.setWhatsThis("Delete Vertex")
        self.deleteVertexAction.setEnabled(False)
        self.graphToolbar.addAction(self.deleteVertexAction)

        self.addVertexWithEdgesAction = QAction(QIcon(getImagePath("Add_Vertex_With_Edges_Icon.svg")), self.tr("Add Vertex With Edges"))
        self.addVertexWithEdgesAction.setToolTip(self.tr("Add Vertex With Edges"))
        self.addVertexWithEdgesAction.setWhatsThis("Add Vertex With Edges")
        self.addVertexWithEdgesAction.setEnabled(False)
        self.addVertexWithEdgesAction.setCheckable(True)
        self.graphToolbar.addAction(self.addVertexWithEdgesAction)

        self.undoAction = QAction(QIcon(getImagePath("Undo_Icon.svg")), self.tr("Undo"))
        self.undoAction.setToolTip(self.tr("Undo"))
        self.undoAction.setWhatsThis("Undo")
        self.undoAction.setEnabled(False)
        self.graphToolbar.addAction(self.undoAction)

        self.redoAction = QAction(QIcon(getImagePath("Redo_Icon.svg")), self.tr("Redo"))
        self.redoAction.setToolTip(self.tr("Redo"))
        self.redoAction.setWhatsThis("Redo")
        self.redoAction.setEnabled(False)
        self.graphToolbar.addAction(self.redoAction)

        self.graphToolbar.setEnabled(True)
        self.graphToolbar.setVisible(True)

        QgsApplication.pluginLayerRegistry().addPluginLayerType(QgsGraphLayerType())

        QgsProviderRegistry.instance().registerProvider(QgsProviderMetadata(QgsGraphDataProvider.providerKey(),
                                                                            QgsGraphDataProvider.description(),
                                                                            QgsGraphDataProvider.createProvider()))

        # re-read and therefore reload plugin layers after adding QgsGraphLayerType to PluginLayerRegistry
        self.reloadPluginLayers()

    def openView(self, view):
        """
        Opens the passed view

        :type view: PluginDialog.Views
        """
        if self.dialog is None:
            self.dialog = PluginDialog()
            self.dialog.setView(view)
            self.dialog.exec()
            self.dialog = None
        else:
            self.dialog.setView(view)

    def unload(self):
        """ Unload all gui elements """
        # remove toolbar entry
        self.iface.removeToolBarIcon(self.toolBarAction)

        self.graphToolbar.removeAction(self.toggleEditAction)
        self.graphToolbar.removeAction(self.zoomLayerAction)
        self.graphToolbar.removeAction(self.selectVertexAction)
        self.graphToolbar.removeAction(self.deleteVertexAction)
        self.graphToolbar.removeAction(self.addVertexWithEdgesAction)
        self.graphToolbar.removeAction(self.undoAction)
        self.graphToolbar.removeAction(self.redoAction)

        self.iface.mainWindow().removeToolBar(self.graphToolbar)

        del self.graphToolbar

        # remove menu entry
        plugin_menu = self.iface.pluginMenu()
        plugin_menu.removeAction(self.menuAction)

        QgsApplication.pluginLayerRegistry().removePluginLayerType(QgsGraphLayer.LAYER_TYPE)
        QgsProject.instance().layersWillBeRemoved.disconnect(self.deleteLayers)

        self.iface.currentLayerChanged.disconnect(self.__layerChanged)

    def reloadPluginLayers(self):
        """
        Re-reads and reloads plugin layers
        """
        # if project is empty
        if QgsProject.instance().baseName() == "":
            return False

        wasZipped = False
        if not QgsProject.instance().isZipped():
            readFileName = QgsProject.instance().absoluteFilePath()
        else:
            # temporarily unzip qgz to qgs
            directory = QgsProject.instance().absolutePath() + "/" + QgsProject.instance().baseName() + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
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
            if os.path.exists(directory + "/" + QgsProject.instance().baseName() + ".qgd"):
                os.remove(directory + "/" + QgsProject.instance().baseName() + ".qgd")
            os.remove(directory + "/" + QgsProject.instance().baseName() + ".qgs")
            os.rmdir(directory)

        # keep track of currently selected layer if it is a GraphLayer
        self.currentLayer = self.iface.activeLayer()
        if not hasattr(self.currentLayer, "LAYER_TYPE") or self.currentLayer.LAYER_TYPE != "graph":
            self.currentLayer = None

    def deleteLayers(self, layers):
        for l in layers:
            delLayer = QgsProject.instance().mapLayer(l)
            del delLayer

    def __layerChanged(self, layer):
        """
        Makes sure the current layer stops editing if the current layer is changed.

        :type layer: QgsMapLayer
        """
        if hasattr(self, "currentLayer") and self.currentLayer and self.currentLayer.isEditing:
            self.currentLayer.toggleEdit()

        if not layer == None:
            if hasattr(layer, "LAYER_TYPE") and layer.LAYER_TYPE == "graph":
                # only keep track of current QgsGraphLayers
                self.currentLayer = layer
