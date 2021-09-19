from qgis.testing import unittest, start_app, TestCase
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsPointXY

from ..models.ExtGraph import ExtGraph

start_app()


class TestExtGraph(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.graph = ExtGraph()

    def tearDown(self):
        """Runs after each test."""
        del self.graph

    # @classmethod
    # def setUpClass(cls):
    #     """Runs before each test class instantiation."""
    #     pass
    #
    # @classmethod
    # def tearDownClass(cls):
    #     """Runs after each test class instantiation."""
    #     pass

    def test_vertex_class(self):
        vertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 0.5), 7)
        self.assertEqual(vertex.id(), 7)
        self.assertEqual(vertex.point(), QgsPointXY(1.0, 0.5))

        vertex.setNewPoint(QgsPointXY(2.0, 3.4))
        self.assertEqual(vertex.id(), 7)
        self.assertEqual(vertex.point(), QgsPointXY(2.0, 3.4))

    def test_edge_class(self):
        fromVertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 2.0), 7)
        toVertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 3.5), 2)
        edge = ExtGraph.ExtEdge(fromVertex.id(), toVertex.id(), 2, True)
        self.assertEqual(edge.id(), 2)
        self.assertEqual(edge.fromVertex(), 7)
        self.assertEqual(edge.toVertex(), 2)
        self.assertTrue(edge.highlighted())

        edge.toggleHighlight()
        self.assertFalse(edge.highlighted())

    def test_vertex_addition(self):
        firstIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdIndex = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthIndex = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        self.assertEqual(self.graph.vertexCount(), 4)

        fifthIndex = self.graph.addVertex(QgsPointXY(0.5, 0.5))
        self.assertEqual(self.graph.vertexCount(), 5)

        self.assertEqual(self.graph.vertex(firstIndex).point(), QgsPointXY(1.0, 1.0))
        self.assertEqual(self.graph.vertex(thirdIndex).point(), QgsPointXY(0.0, 1.0))
        self.assertEqual(self.graph.vertex(fifthIndex).point(), QgsPointXY(0.5, 0.5))

    def test_edge_addition(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        firstVertex = self.graph.vertex(firstVertexIndex)
        secondVertex = self.graph.vertex(secondVertexIndex)
        thirdVertex = self.graph.vertex(thirdVertexIndex)
        fourthVertex = self.graph.vertex(fourthVertexIndex)

        firstEdgeIndex = self.graph.addEdge(firstVertex.id(), secondVertex.id(), ID=4)
        secondEdgeIndex = self.graph.addEdge(thirdVertex.id(), fourthVertex.id(), ID=3)
        thirdEdgeIndex = self.graph.addEdge(secondVertex.id(), thirdVertex.id(), ID=5)

        self.assertEqual(self.graph.edgeCount(), 3)
        self.assertEqual(self.graph.hasEdge(secondVertexIndex, thirdVertexIndex), thirdEdgeIndex)
        self.assertEqual(self.graph.hasEdge(thirdVertexIndex, secondVertexIndex), -1)
        self.assertEqual(self.graph.hasEdge(firstVertexIndex, thirdVertexIndex), -1)

        self.assertEqual(self.graph.edge(thirdEdgeIndex).id(), 5)
        self.assertEqual(self.graph.edge(thirdEdgeIndex).fromVertex(), secondVertex.id())
        self.assertEqual(self.graph.edge(thirdEdgeIndex).toVertex(), thirdVertex.id())
        self.assertEqual(self.graph.findEdgeByID(3), secondEdgeIndex)
        self.assertEqual(self.graph.findEdgeByID(4), firstEdgeIndex)
        self.assertEqual(self.graph.findEdgeByID(5), thirdEdgeIndex)


if __name__ == '__main__':
    unittest.main()
