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

from qgis.testing import unittest, start_app, TestCase
from qgis.core import QgsApplication, QgsProviderRegistry, QgsProviderMetadata, QgsProject, QgsPointXY, QgsRenderChecker, QgsMapSettings, QgsRectangle, QgsVectorLayer, QgsCoordinateReferenceSystem, Qgis
from qgis.utils import iface

from qgis.PyQt.QtGui import QColor

from ..models.ExtGraph import ExtGraph
from ..models.GraphLayer import GraphLayer, GraphLayerType, GraphDataProvider
from ..helperFunctions import getPluginPath, saveLayer

import os
import tempfile
import shutil

start_app()


class TestGraphLayer(TestCase):
    """ Provides test cases for testing the graph layer """

    def setUp(self):
        """Runs before each test."""
        self.graph = ExtGraph()
        self.graphLayer = GraphLayer("TestLayer")

    def tearDown(self):
        """Runs after each test."""
        del self.graph
        del self.graphLayer

    @classmethod
    def setUpClass(cls):
        """Runs before each test class instantiation."""
        cls.tempDir = tempfile.mkdtemp()
        QgsApplication.pluginLayerRegistry().addPluginLayerType(GraphLayerType())
        QgsProviderRegistry.instance().registerProvider(QgsProviderMetadata(GraphDataProvider.providerKey(),
                                                                            GraphDataProvider.description(),
                                                                            GraphDataProvider.createProvider()))

    @classmethod
    def tearDownClass(cls):
        """Runs after each test class instantiation."""
        shutil.rmtree(cls.tempDir, True)
        QgsApplication.pluginLayerRegistry().removePluginLayerType(GraphLayer.LAYER_TYPE)

    @unittest.skipIf(Qgis.QGIS_VERSION_INT < 31800, "setControlImagePath available from QGIS 3.18")
    def test_graph_rendering(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)
        self.graphLayer.mRandomColor = QColor(0, 0, 0)
        QgsProject.instance().addMapLayer(self.graphLayer)

        renderChecker = QgsRenderChecker()
        renderChecker.setControlImagePath(os.path.join(getPluginPath(), "tests/testdata")) # setControlImagePath from QGIS 3.18
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
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(15, graph.edgeCount())

        self.assertEqual(QgsPointXY(0, -1.0), self.graph.vertex(3).point())
        self.assertEqual(QgsPointXY(0.0, 0.0), self.graph.vertex(0).point())
        self.assertEqual(QgsPointXY(2.0, 0), self.graph.vertex(5).point())

    def test_createVectorLayer(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)

        pointLayer, lineLayer = self.graphLayer.createVectorLayer()
        pointLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        lineLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        # save to temporary shapefile due to conflicts with geometry type
        tmp_path = os.path.join(self.tempDir, "graph_vertices_layer.shp")
        lineLayer = saveLayer(lineLayer, "tmp_line_layer", "vector", tmp_path, ".shp")

        expectedPointLayer = QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp"))
        expectedLineLayer = QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp"))
        self.assertLayersEqual(expectedPointLayer, pointLayer)
        self.assertLayersEqual(expectedLineLayer, lineLayer)

    def test_extent(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)
        self.graphLayer.setGraph(self.graph)

        self.assertEqual(QgsRectangle(-1, -1, 2.0, 2.0), self.graphLayer.extent())


if __name__ == '__main__':
    unittest.main()
