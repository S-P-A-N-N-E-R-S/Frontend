#  This file is part of the OGDF plugin.
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

from qgis.testing import unittest, start_app, TestCase

from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtCore import Qt

from ..views.widgets.QgsOgdfParametersWidget import QgsOGDFParametersWidget
from ..network.protocol.build.available_handlers_pb2 import FieldInformation
from ..exceptions import FieldRequiredError

start_app()


class TestQgsOGDFParametersWidget(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.widget = QgsOGDFParametersWidget()
        self.widget.show()

    def tearDown(self):
        """Runs after each test."""
        del self.widget

    def test_fields(self):
        self.widget.setParameterFields({
            "key1": {
                "type": FieldInformation.FieldType.GRAPH,
                "label": "Graph",
                "default": "",
                "required": False,
            },
            "key2": {"type": FieldInformation.FieldType.VERTEX_ID,
                "label": "Vertex",
                "default": "",
                "required": False,
            },
            "key3": {"type": FieldInformation.FieldType.EDGE_ID,
                "label": "Edge",
                "default": "",
                "required": False,
            },
            "key4": {"type": FieldInformation.FieldType.BOOL,
                "label": "Checkbox",
                "default": False,
                "required": False,
            },
            "key5": {"type": FieldInformation.FieldType.INT,
                "label": "Integer",
                "default": "",
                "required": False,
            },
            "key6": {"type": FieldInformation.FieldType.DOUBLE,
                "label": "Double",
                "default": "",
                "required": False,
            },
            "key7": {"type": FieldInformation.FieldType.STRING,
                "label": "Text",
                "default": "",
                "required": False,
            },
            "key8": {"type": FieldInformation.FieldType.CHOICE,
                "label": "Selection",
                "default": "",
                "choices": {
                    "first choice": "first choice data",
                    "second choice": "second choice data",
                },
                "required": False,
            },
            "key9": {"type": FieldInformation.FieldType.EDGE_COSTS,
                "label": "Edge costs",
                "default": "",
                "required": False,
            },
            "key10": {"type": FieldInformation.FieldType.VERTEX_COSTS,
                "label": "Vertex costs",
                "default": "",
                "required": False,
            },
        })

        QTest.mouseClick(self.widget.fieldWidgets["key4"]["inputWidget"], Qt.LeftButton)
        QTest.keyClicks(self.widget.fieldWidgets["key5"]["inputWidget"], "123")
        self.widget.fieldWidgets["key6"]["inputWidget"].setValue(1.23)
        QTest.keyClicks(self.widget.fieldWidgets["key7"]["inputWidget"], "Test string")
        self.widget.fieldWidgets["key8"]["inputWidget"].setCurrentIndex(1)

        fieldsData = self.widget.getParameterFieldsData()
        self.assertEqual(True, fieldsData["key4"])
        self.assertEqual(123, fieldsData["key5"])
        self.assertEqual(1.23, fieldsData["key6"])
        self.assertEqual("Test string", fieldsData["key7"])
        self.assertEqual("second choice data", fieldsData["key8"])

    def test_required_fields(self):
        self.widget.setParameterFields({
            "key1": {
                "type": FieldInformation.FieldType.STRING,
                "label": "Text",
                "default": "",
                "required": True,
            },
        })
        self.assertRaises(FieldRequiredError, self.widget.getParameterFieldsData)

        self.widget.setParameterFields({
            "key1": {
                "type": FieldInformation.FieldType.GRAPH,
                "label": "Text",
                "default": "",
                "required": True,
            },
        })
        self.assertRaises(FieldRequiredError, self.widget.getParameterFieldsData)

    def test_default_values(self):
        self.widget.setParameterFields({
            "key1": {
                "type": FieldInformation.FieldType.BOOL,
                "label": "Checkbox",
                "default": True,
                "required": False,
            },
            "key2": {
                "type": FieldInformation.FieldType.INT,
                "label": "Integer",
                "default": 123,
                "required": False,
            },
            "key3": {
                "type": FieldInformation.FieldType.DOUBLE,
                "label": "Double",
                "default": 1.23,
                "required": False,
            },
            "key4": {
                "type": FieldInformation.FieldType.STRING,
                "label": "Text",
                "default": "Test string",
                "required": False,
            },
            "key5": {
                "type": FieldInformation.FieldType.CHOICE,
                "label": "Selection",
                "default": "second choice",
                "choices": {
                    "first choice": "first choice data",
                    "second choice": "second choice data",
                    "third choice": "third choice data",
                },
                "required": False,
            },
        })

        fieldsData = self.widget.getParameterFieldsData()
        self.assertEqual(True, fieldsData["key1"])
        self.assertEqual(123, fieldsData["key2"])
        self.assertEqual(1.23, fieldsData["key3"])
        self.assertEqual("Test string", fieldsData["key4"])
        self.assertEqual("second choice data", fieldsData["key5"])


if __name__ == '__main__':
    unittest.main()
