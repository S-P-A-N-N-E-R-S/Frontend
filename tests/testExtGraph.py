from qgis.testing import unittest, start_app, TestCase
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsPointXY, QgsCoordinateReferenceSystem

from ..models.ExtGraph import ExtGraph
from ..helperFunctions import getPluginPath

import os
import tempfile
import math

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

    def test_vertex_removal(self):
        firstIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        self.assertEqual(self.graph.vertexCount(), 2)

        firstVertex = self.graph.vertex(firstIndex)
        secondVertex = self.graph.vertex(secondIndex)

        self.graph.deleteVertex(secondIndex)
        self.assertEqual(self.graph.vertexCount(), 1)
        self.assertEqual(self.graph.vertex(secondIndex), -1)

        thirdIndex = self.graph.addVertex(QgsPointXY(0.5, 0.5))
        thirdVertex = self.graph.vertex(thirdIndex)
        self.assertEqual(self.graph.vertexCount(), 2)
        self.assertEqual(len(self.graph.vertices()), 2)
        for vertex in self.graph.vertices():
            self.assertIn(vertex, [firstVertex, thirdVertex])

    def test_edge_removal(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        firstVertex = self.graph.vertex(firstVertexIndex)
        secondVertex = self.graph.vertex(secondVertexIndex)
        thirdVertex = self.graph.vertex(thirdVertexIndex)
        fourthVertex = self.graph.vertex(fourthVertexIndex)

        firstEdgeIndex = self.graph.addEdge(firstVertex.id(), secondVertex.id())
        secondEdgeIndex = self.graph.addEdge(thirdVertex.id(), fourthVertex.id())
        thirdEdgeIndex = self.graph.addEdge(secondVertex.id(), thirdVertex.id())

        firstEdge = self.graph.edge(firstEdgeIndex)
        secondEdge = self.graph.edge(secondEdgeIndex)
        thirdEdge = self.graph.edge(thirdEdgeIndex)

        self.assertEqual(self.graph.edgeCount(), 3)
        self.assertTrue(self.graph.deleteEdge(secondEdgeIndex))
        self.assertEqual(self.graph.edgeCount(), 2)

        fourthIndex = self.graph.addEdge(fourthVertex.id(), firstVertex.id())
        fourthEdge = self.graph.edge(fourthIndex)
        self.assertEqual(self.graph.edgeCount(), 3)
        self.assertEqual(len(self.graph.edges()), 3)
        for edge in self.graph.edges():
            self.assertIn(edge, [firstEdge, thirdEdge, fourthEdge])

    def test_read_graphML(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)

        self.assertEqual(self.graph.vertexCount(), 10)
        self.assertEqual(self.graph.edgeCount(), 15)

        # check some vertices
        self.assertEqual(self.graph.vertex(self.graph.findEdgeByID(3)).point(), QgsPointXY(0, -1.0))
        self.assertEqual(self.graph.vertex(self.graph.findEdgeByID(0)).point(), QgsPointXY(0.0, 0.0))
        self.assertEqual(self.graph.vertex(self.graph.findEdgeByID(5)).point(), QgsPointXY(2.0, 0))

        # check some edges
        vertex = self.graph.vertex(self.graph.findEdgeByID(0))
        outgoingEdges = vertex.outgoingEdges()
        self.assertEqual(len(outgoingEdges), 2)
        incomingEdges = vertex.incomingEdges()
        self.assertEqual(len(incomingEdges), 6)

        self.assertNotEqual(self.graph.hasEdge(self.graph.findEdgeByID(0), self.graph.findEdgeByID(1)), -1)
        self.assertNotEqual(self.graph.hasEdge(self.graph.findEdgeByID(3), self.graph.findEdgeByID(1)), -1)
        self.assertNotEqual(self.graph.hasEdge(self.graph.findEdgeByID(4), self.graph.findEdgeByID(3)), -1)

    def test_write_graphML(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        firstVertex = self.graph.vertex(firstVertexIndex)
        secondVertex = self.graph.vertex(secondVertexIndex)

        firstEdgeIndex = self.graph.addEdge(firstVertex.id(), secondVertex.id())
        secondEdgeIndex = self.graph.addEdge(secondVertex.id(), firstVertex.id())
        firstEdge = self.graph.edge(firstEdgeIndex)
        secondEdge = self.graph.edge(secondEdgeIndex)

        temp_file = os.path.join(tempfile.mkdtemp(), "graph.graphml")
        self.graph.writeGraphML(temp_file)

        temp_graph = ExtGraph()
        temp_graph.readGraphML(temp_file)
        self.assertEqual(temp_graph.edgeCount(), 2)
        self.assertEqual(temp_graph.vertexCount(), 2)

        self.assertEqual(temp_graph.vertex(temp_graph.findEdgeByID(firstVertex.id())).point(), QgsPointXY(1.0, 1.0))
        self.assertEqual(temp_graph.vertex(temp_graph.findEdgeByID(secondVertex.id())).point(), QgsPointXY(0.0, 0.0))

        self.assertNotEqual(temp_graph.hasEdge(temp_graph.findEdgeByID(firstVertex.id()), temp_graph.findEdgeByID(secondVertex.id())), -1)
        self.assertNotEqual(temp_graph.hasEdge(temp_graph.findEdgeByID(secondVertex.id()), temp_graph.findEdgeByID(firstVertex.id())), -1)

    def test_edge_costs(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        firstVertex = self.graph.vertex(firstVertexIndex)
        secondVertex = self.graph.vertex(secondVertexIndex)

        edgeIndex = self.graph.addEdge(firstVertex.id(), secondVertex.id())
        edge = self.graph.edge(edgeIndex)
        self.graph.crs = QgsCoordinateReferenceSystem("EPSG:4326")

        self.graph.setDistanceStrategy("Euclidean")
        self.assertEqual(self.graph.costOfEdge(edgeIndex), math.sqrt(2))
        self.graph.setDistanceStrategy("Manhattan")
        self.assertEqual(self.graph.costOfEdge(edgeIndex), 2)
        self.graph.setDistanceStrategy("Geodesic")
        self.assertEqual(self.graph.costOfEdge(edgeIndex), 157249.38127194397)
        self.graph.setDistanceStrategy("Ellipsoidal")
        self.assertEqual(self.graph.costOfEdge(edgeIndex), 156899.56829134026)
        self.graph.setDistanceStrategy("Advanced")
        self.graph.setCostOfEdge(edgeIndex, 0, 12)
        self.graph.setCostOfEdge(edgeIndex, 1, 24)
        self.assertEqual(self.graph.costOfEdge(edgeIndex, 0), 12)
        self.assertEqual(self.graph.costOfEdge(edgeIndex, 1), 24)

        self.assertEqual(self.graph.distanceP2P(firstVertexIndex, secondVertexIndex), math.sqrt(2))

    def test_findVertexByID(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0), ID=12)
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0), ID=4)
        thirdVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 1.0), ID=9)
        fourthVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 0.0), ID=0)

        self.assertEqual(self.graph.findVertexByID(12), firstVertexIndex)
        self.assertEqual(self.graph.findVertexByID(4), secondVertexIndex)
        self.assertEqual(self.graph.findVertexByID(9), thirdVertexIndex)
        self.assertEqual(self.graph.findVertexByID(0), fourthVertexIndex)

    def test_find_vertex(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))

        self.assertEqual(self.graph.findVertex(QgsPointXY(1.5, 1.0), 1), firstVertexIndex)
        self.assertEqual(self.graph.findVertex(QgsPointXY(0.0, 0.0), 0), secondVertexIndex)

    def test_addVertexWithEdges(self):
        # todo: the current version does not look finished
        pass


if __name__ == '__main__':
    unittest.main()
