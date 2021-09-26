from qgis.testing import unittest, start_app, TestCase
from qgis.core import QgsApplication, QgsProviderRegistry, QgsProviderMetadata, QgsProject, QgsPointXY, QgsRenderChecker, QgsMapSettings, QgsRectangle, QgsVectorLayer

from qgis.PyQt.QtGui import QColor

from ..models.ExtGraph import ExtGraph
from ..models.QgsGraphLayer import QgsGraphLayer, QgsGraphLayerType, QgsGraphDataProvider
from ..helperFunctions import getPluginPath

import os

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

    def test_get_graph(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)

        graph = self.graphLayer.getGraph()
        self.assertEqual(graph.vertexCount(), 10)
        self.assertEqual(graph.edgeCount(), 15)

        self.assertEqual(self.graph.vertex(self.graph.findEdgeByID(3)).point(), QgsPointXY(0, -1.0))
        self.assertEqual(self.graph.vertex(self.graph.findEdgeByID(0)).point(), QgsPointXY(0.0, 0.0))
        self.assertEqual(self.graph.vertex(self.graph.findEdgeByID(5)).point(), QgsPointXY(2.0, 0))

    def test_createVectorLayer(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)

        pointLayer, lineLayer = self.graphLayer.createVectorLayer()
        expectedPointLayer = QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.gpkg"))
        expectedLineLayer = QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.gpkg"))
        self.assertLayersEqual(pointLayer, expectedPointLayer)
        self.assertLayersEqual(lineLayer, expectedLineLayer)

    def test_extent(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)

        self.assertEqual(self.graphLayer.extent(), QgsRectangle(-1, -1, 2.0, 2.0))


if __name__ == '__main__':
    unittest.main()
