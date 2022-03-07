#  This file is part of the OGDF plugin.
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
        vectorLayer = QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp"))
        self.dialog.setVectorLayer(vectorLayer)
        self.dialog.setCostFunction("field:vertexId")

        self.assertEqual("field:vertexId", self.dialog.costFunction())
        self.dialog.insertEditorText("10 * ")
        self.assertEqual("10 * field:vertexId", self.dialog.costFunction())

        self.dialog.setRasterData([(QgsRasterLayer(os.path.join(getPluginPath(), "tests/testdata/simple_raster.tif")), 1)])
        self.dialog.setPolygonLayers([QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_polygons/simple_polygons.shp"))])


if __name__ == '__main__':
    unittest.main()
