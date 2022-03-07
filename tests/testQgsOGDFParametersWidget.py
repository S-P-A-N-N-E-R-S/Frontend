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

from ..views.widgets.QgsOgdfParametersWidget import QgsOGDFParametersWidget
from ..network.protocol.build.available_handlers_pb2 import FieldInformation
from ..network.requests.baseRequest import BaseRequest
from ..network.fields import baseField, boolField, graphField, intField, choiceField, doubleField, stringField, edgeIDField, vertexIDField, edgeCostsField, vertexCostsField
from ..exceptions import FieldRequiredError

start_app()


class TestQgsOGDFParametersWidget(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.widget = QgsOGDFParametersWidget()
        self.widget.show()
        self.request = BaseRequest()

    def tearDown(self):
        """Runs after each test."""
        del self.widget

    def test_fields(self):
        self.request.fields = {
            "key1": graphField.GraphField("key1", "Graph", None, False),
            "key2": vertexIDField.VertexIDField("key2", "Vertex", None, False),
            "key3": edgeIDField.EdgeIDField("key3", "Edge", None, False),
            "key4": boolField.BoolField("key4", "Checkbox", False, False),
            "key5": intField.IntField("key5", "Integer", None, False),
            "key6": doubleField.DoubleField("key6", "Double", None, False),
            "key7": stringField.StringField("key7", "Text", "", False),
            "key8": choiceField.ChoiceField("key8", "Selection", None, False),
            "key9": edgeCostsField.EdgeCostsField("key9", "Edge costs", None, False),
            "key10": vertexCostsField.VertexCostsField("key10", "Vertex costs", None, False),
        }
        self.request.fields["key8"].choices = {
            "first choice": "first choice data",
            "second choice": "second choice data",
        }

        self.widget.setParameterFields(self.request)

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
        self.request.fields = {
            "key1": stringField.StringField("key1", "Text", "", True),
        }
        self.widget.setParameterFields(self.request)
        self.assertRaises(FieldRequiredError, self.widget.getParameterFieldsData)

        self.request.fields = {
            "key1": graphField.GraphField("key1", "Graph", None, True),
        }
        self.widget.setParameterFields(self.request)
        self.assertRaises(FieldRequiredError, self.widget.getParameterFieldsData)

    def test_default_values(self):
        self.request.fields = {
            "key1": boolField.BoolField("key1", "Checkbox", True, False),
            "key2": intField.IntField("key2", "Integer", 123, False),
            "key3": doubleField.DoubleField("key3", "Double", 1.23, False),
            "key4": stringField.StringField("key4", "Text", "Test string", False),
            "key5": choiceField.ChoiceField("key5", "Selection", "second choice", False),
        }
        self.request.fields["key5"].choices = {
            "first choice": "first choice data",
            "second choice": "second choice data",
            "third choice": "third choice data",
        }
        self.widget.setParameterFields(self.request)

        fieldsData = self.widget.getParameterFieldsData()
        self.assertEqual(True, fieldsData["key1"])
        self.assertEqual(123, fieldsData["key2"])
        self.assertEqual(1.23, fieldsData["key3"])
        self.assertEqual("Test string", fieldsData["key4"])
        self.assertEqual("second choice data", fieldsData["key5"])


if __name__ == '__main__':
    unittest.main()
