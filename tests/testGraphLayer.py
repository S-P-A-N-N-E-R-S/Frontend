from qgis.testing import unittest, start_app, TestCase
from qgis.core import QgsApplication, QgsProviderRegistry, QgsMapRendererParallelJob, QgsProviderMetadata, QgsProject, QgsPointXY, QgsCoordinateReferenceSystem, QgsRenderChecker, QgsMapSettings, QgsRectangle, QgsVectorLayer

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor

from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer, QgsGraphLayerType, QgsGraphDataProvider
from ..helperFunctions import getPluginPath

import os
import tempfile
import math

start_app()


class TestQgsGraphLayer(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.graph = ExtGraph()
        self.graphLayer = QgsGraphLayer("TestLayer")

    def tearDown(self):
        """Runs after each test."""
        del self.graph
        del self.graphLayer

    @classmethod
    def setUpClass(cls):
        """Runs before each test class instantiation."""
        QgsApplication.pluginLayerRegistry().addPluginLayerType(QgsGraphLayerType())
        QgsProviderRegistry.instance().registerProvider(QgsProviderMetadata(QgsGraphDataProvider.providerKey(),
                                                                            QgsGraphDataProvider.description(),
                                                                            QgsGraphDataProvider.createProvider()))

    @classmethod
    def tearDownClass(cls):
        """Runs after each test class instantiation."""
        QgsApplication.pluginLayerRegistry().removePluginLayerType(QgsGraphLayer.LAYER_TYPE)

    def test_graph_rendering(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)
        self.graphLayer.mRandomColor = QColor(0, 0, 0)
        QgsProject.instance().addMapLayer(self.graphLayer)

        renderChecker = QgsRenderChecker()
        renderChecker.setControlImagePath(os.path.join(getPluginPath(), "tests/testdata"))
        renderChecker.setControlName("simple_graph_graphlayer")
        renderChecker.setColorTolerance(20)
        renderChecker.setSizeTolerance(20, 20)

        mapSettings = QgsMapSettings()
        mapSettings.setLayers([self.graphLayer])
        mapSettings.setExtent(self.graphLayer.extent())
        renderChecker.setMapSettings(mapSettings)

        self.assertTrue(renderChecker.runTest("test_simple_graph_graphlayer"))


if __name__ == '__main__':
    unittest.main()
