from qgis.testing import unittest, start_app, TestCase

from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsRasterLayer

from ..views.widgets.QgsCostFunctionDialog import QgsCostFunctionDialog
from ..helperFunctions import getPluginPath

import os

start_app()


class TestQgsOGDFParametersWidget(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.dialog = QgsCostFunctionDialog()
        self.dialog.show()

    def tearDown(self):
        """Runs after each test."""
        del self.dialog

    def test_cost_function_dialog(self):
        vectorLayer = QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.gpkg"))
        self.dialog.setVectorLayer(vectorLayer)
        self.dialog.setCostFunction("field:vertexId")

        self.assertEqual(self.dialog.costFunction(), "field:vertexId")
        self.dialog.insertEditorText("10 * ")
        self.assertEqual(self.dialog.costFunction(), "10 * field:vertexId")

        self.dialog.setRasterData([(QgsRasterLayer(os.path.join(getPluginPath(), "tests/testdata/simple_raster.tif")), 1)])
        self.dialog.setPolygonLayers([QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_polygons/simple_polygons.gpkg"))])


if __name__ == '__main__':
    unittest.main()
