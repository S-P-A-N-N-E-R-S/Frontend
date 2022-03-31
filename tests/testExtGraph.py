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
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem

from ..models.extGraph import ExtGraph
from ..models.graphBuilder import GraphBuilder
from ..helperFunctions import getPluginPath

import os
import tempfile
import math
import shutil

start_app()


class TestExtGraph(TestCase):
    """ Provides test cases for testing the graph class """

    def setUp(self):
        """Runs before each test."""
        self.graph = ExtGraph()

    def tearDown(self):
        """Runs after each test."""
        del self.graph

    @classmethod
    def setUpClass(cls):
        """Runs before each test class instantiation."""
        cls.tempDir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """Runs after each test class instantiation."""
        shutil.rmtree(cls.tempDir, True)

    def test_vertex_class(self):
        vertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 0.5))
        self.assertEqual(QgsPointXY(1.0, 0.5), vertex.point())

        vertex.setNewPoint(QgsPointXY(2.0, 3.4))
        self.assertEqual(QgsPointXY(2.0, 3.4), vertex.point())

    def test_edge_class(self):
        fromVertexId = self.graph.addVertex(QgsPointXY(1.0, 2.0))
        toVertexId = self.graph.addVertex(QgsPointXY(1.0, 3.5))
        edge = ExtGraph.ExtEdge(fromVertexId, toVertexId, True)

        self.assertEqual(fromVertexId, edge.fromVertex())
        self.assertEqual(toVertexId, edge.toVertex())
        self.assertTrue(edge.highlighted())

        edge.toggleHighlight()
        self.assertFalse(edge.highlighted())

    def test_vertex_addition(self):
        firstId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondId = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdId = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthId = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        self.assertEqual(4, self.graph.vertexCount())

        fifthId = self.graph.addVertex(QgsPointXY(0.5, 0.5))
        self.assertEqual(5, self.graph.vertexCount())

        self.assertEqual(QgsPointXY(1.0, 1.0), self.graph.vertex(firstId).point())
        self.assertEqual(QgsPointXY(0.0, 1.0), self.graph.vertex(thirdId).point())
        self.assertEqual(QgsPointXY(0.5, 0.5), self.graph.vertex(fifthId).point())

    def test_edge_addition(self):
        firstVertexId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexId = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdVertexId = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthVertexId = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        firstVertex = self.graph.vertex(firstVertexId)
        secondVertex = self.graph.vertex(secondVertexId)
        thirdVertex = self.graph.vertex(thirdVertexId)
        fourthVertex = self.graph.vertex(fourthVertexId)

        firstEdgeId = self.graph.addEdge(firstVertexId, secondVertexId, addedEdgeID=4)
        secondEdgeId = self.graph.addEdge(thirdVertexId, fourthVertexId, addedEdgeID=3)
        thirdEdgeId = self.graph.addEdge(secondVertexId, thirdVertexId, addedEdgeID=5)

        self.assertEqual(3, self.graph.edgeCount())
        self.assertEqual(thirdEdgeId, self.graph.hasEdge(secondVertexId, thirdVertexId))
        self.assertEqual(-1, self.graph.hasEdge(thirdVertexId, secondVertexId))
        self.assertEqual(-1, self.graph.hasEdge(firstVertexId, thirdVertexId))

        self.assertEqual(secondVertexId, self.graph.edge(thirdEdgeId).fromVertex())
        self.assertEqual(thirdVertexId, self.graph.edge(thirdEdgeId).toVertex())
        self.assertEqual(secondEdgeId, 3)
        self.assertEqual(firstEdgeId, 4)
        self.assertEqual(thirdEdgeId, 5)

    def test_vertex_removal(self):
        firstId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondId = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        self.assertEqual(2, self.graph.vertexCount())

        firstVertex = self.graph.vertex(firstId)
        secondVertex = self.graph.vertex(secondId)

        self.graph.deleteVertex(secondId)
        self.assertEqual(1, self.graph.vertexCount())
        self.assertRaises(IndexError, self.graph.vertex, secondId)

        thirdId = self.graph.addVertex(QgsPointXY(0.5, 0.5))
        thirdVertex = self.graph.vertex(thirdId)
        self.assertEqual(2, self.graph.vertexCount())
        self.assertEqual(2, len(self.graph.vertices()))
        for vertexId, vertex in self.graph.vertices().items():
            self.assertIn(vertex, [firstVertex, thirdVertex])

    def test_edge_removal(self):
        firstVertexId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexId = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdVertexId = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthVertexId = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        firstVertex = self.graph.vertex(firstVertexId)
        secondVertex = self.graph.vertex(secondVertexId)
        thirdVertex = self.graph.vertex(thirdVertexId)
        fourthVertex = self.graph.vertex(fourthVertexId)

        firstEdgeId = self.graph.addEdge(firstVertexId, secondVertexId)
        secondEdgeId = self.graph.addEdge(thirdVertexId, fourthVertexId)
        thirdEdgeId = self.graph.addEdge(secondVertexId, thirdVertexId)

        firstEdge = self.graph.edge(firstEdgeId)
        secondEdge = self.graph.edge(secondEdgeId)
        thirdEdge = self.graph.edge(thirdEdgeId)

        self.assertEqual(3, self.graph.edgeCount())
        self.assertTrue(self.graph.deleteEdge(secondEdgeId))
        self.assertEqual(2, self.graph.edgeCount())

        fourthId = self.graph.addEdge(fourthVertexId, firstVertexId)
        fourthEdge = self.graph.edge(fourthId)
        self.assertEqual(3, self.graph.edgeCount())
        self.assertEqual(3, len(self.graph.edges()))
        for edgeId, edge in self.graph.edges().items():
            self.assertIn(edge, [firstEdge, thirdEdge, fourthEdge])

    def test_read_graphML(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)

        self.assertEqual(10, self.graph.vertexCount())
        self.assertEqual(15, self.graph.edgeCount())

        # check some vertices
        self.assertEqual(QgsPointXY(0, -1.0), self.graph.vertex(3).point())
        self.assertEqual(QgsPointXY(0.0, 0.0), self.graph.vertex(0).point())
        self.assertEqual(QgsPointXY(2.0, 0), self.graph.vertex(5).point())

        # check some edges
        vertex = self.graph.vertex(0)
        outgoingEdges = vertex.outgoingEdges()
        self.assertEqual(3, len(outgoingEdges))
        incomingEdges = vertex.incomingEdges()
        self.assertEqual(5, len(incomingEdges))

        self.assertNotEqual(-1, self.graph.hasEdge(0, 1))
        self.assertNotEqual(-1, self.graph.hasEdge(3, 1))
        self.assertNotEqual(-1, self.graph.hasEdge(4, 3))

    def test_write_graphML(self):
        firstVertexId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexId = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        firstVertex = self.graph.vertex(firstVertexId)
        secondVertex = self.graph.vertex(secondVertexId)

        firstEdgeId = self.graph.addEdge(firstVertexId, secondVertexId)
        secondEdgeId = self.graph.addEdge(secondVertexId, firstVertexId)
        firstEdge = self.graph.edge(firstEdgeId)
        secondEdge = self.graph.edge(secondEdgeId)

        temp_file = os.path.join(self.tempDir, "graph.graphml")
        self.graph.writeGraphML(temp_file)

        temp_graph = ExtGraph()
        temp_graph.readGraphML(temp_file)
        self.assertEqual(2, temp_graph.edgeCount())
        self.assertEqual(2, temp_graph.vertexCount())

        self.assertEqual(QgsPointXY(1.0, 1.0), temp_graph.vertex(firstVertexId).point())
        self.assertEqual(QgsPointXY(0.0, 0.0), temp_graph.vertex(secondVertexId).point())

        self.assertNotEqual(-1, temp_graph.hasEdge(firstVertexId, secondVertexId))
        self.assertNotEqual(-1, temp_graph.hasEdge(secondVertexId, firstVertexId))

    def test_edge_costs(self):
        firstVertexId = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        secondVertexId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        firstVertex = self.graph.vertex(firstVertexId)
        secondVertex = self.graph.vertex(secondVertexId)

        edgeId = self.graph.addEdge(firstVertexId, secondVertexId)
        edge = self.graph.edge(edgeId)
        # self.graph.crs = QgsCoordinateReferenceSystem("EPSG:4326")
        self.graph.updateCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        self.graph.setDistanceStrategy("Euclidean")
        self.assertEqual(math.sqrt(2), self.graph.costOfEdge(edgeId))
        self.graph.setDistanceStrategy("Manhattan")
        self.assertEqual(2, self.graph.costOfEdge(edgeId))
        self.graph.setDistanceStrategy("Geodesic")
        self.assertEqual(157249.38127194397, self.graph.costOfEdge(edgeId))
        self.graph.setDistanceStrategy("Ellipsoidal")
        self.assertLess(156899, self.graph.costOfEdge(edgeId))
        self.assertGreater(156900, self.graph.costOfEdge(edgeId))
        self.graph.setDistanceStrategy("Advanced")
        self.graph.setCostOfEdge(edgeId, 0, 12)
        self.graph.setCostOfEdge(edgeId, 1, 24)
        self.assertEqual(12, self.graph.costOfEdge(edgeId, 0))
        self.assertEqual(24, self.graph.costOfEdge(edgeId, 1))

        self.assertEqual(math.sqrt(2), self.graph.distanceP2P(firstVertexId, secondVertexId))

    def test_findVertexByID(self):
        firstVertexId = self.graph.addVertex(QgsPointXY(1.0, 1.0), addedVertexID=12)
        secondVertexId = self.graph.addVertex(QgsPointXY(0.0, 0.0), addedVertexID=4)
        thirdVertexId = self.graph.addVertex(QgsPointXY(0.0, 1.0), addedVertexID=9)
        fourthVertexId = self.graph.addVertex(QgsPointXY(1.0, 0.0), addedVertexID=0)

        self.assertEqual(firstVertexId, 12)
        self.assertEqual(secondVertexId, 4)
        self.assertEqual(thirdVertexId, 9)
        self.assertEqual(fourthVertexId, 0)

    def test_find_vertex(self):
        firstVertexId = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexId = self.graph.addVertex(QgsPointXY(0.0, 0.0))

        self.assertEqual(firstVertexId, self.graph.findVertex(QgsPointXY(1.5, 1.0)))
        self.assertEqual(secondVertexId, self.graph.findVertex(QgsPointXY(0.0, 0.0)))

    def test_add_vertex_complete(self):
        graphBuilder = GraphBuilder()
        graphBuilder.setRandomOption("numberOfVertices", 10)
        graphBuilder.setOption("connectionType", "Complete")
        graph = graphBuilder.makeGraph()

        graph.addVertexWithEdges([-1.0, 1.0])

        self.assertEqual(11, graph.vertexCount())
        newVertex = graph.vertex(graph.findVertex(QgsPointXY(-1.0, 1.0)))
        self.assertTrue(len(newVertex.outgoingEdges())+len(newVertex.incomingEdges()), 10)

    def test_add_vertex_nearest_neighbor(self):
        graphBuilder = GraphBuilder()
        graphBuilder.setRandomOption("numberOfVertices", 10)
        graphBuilder.setOption("connectionType", "Nearest neighbor")
        graph = graphBuilder.makeGraph()

        graph.addVertexWithEdges([-1.0, 1.0])

        self.assertEqual(11, graph.vertexCount())
        self.assertNotEqual(-1, graph.findVertex(QgsPointXY(-1.0, 1.0)))

    def test_add_vertex_distanceNN(self):
        graphBuilder = GraphBuilder()
        graphBuilder.setRandomOption("numberOfVertices", 10)
        graphBuilder.setOption("connectionType", "DistanceNN")
        graph = graphBuilder.makeGraph()
        graph.updateCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        graph.addVertexWithEdges([-1.0, 1.0])

        self.assertEqual(11, graph.vertexCount())
        self.assertNotEqual(-1, graph.findVertex(QgsPointXY(-1.0, 1.0)))

    def test_add_vertex_clusterComplete(self):
        graphBuilder = GraphBuilder()
        graphBuilder.setRandomOption("numberOfVertices", 10)
        graphBuilder.setOption("connectionType", "ClusterComplete")
        graph = graphBuilder.makeGraph()

        graph.addVertexWithEdges([-1.0, 1.0])

        self.assertEqual(11, graph.vertexCount())
        self.assertNotEqual(-1, graph.findVertex(QgsPointXY(-1.0, 1.0)))

    def test_add_vertex_clusterNN(self):
        graphBuilder = GraphBuilder()
        graphBuilder.setRandomOption("numberOfVertices", 10)
        graphBuilder.setOption("connectionType", "ClusterNN")
        graph = graphBuilder.makeGraph()

        graph.addVertexWithEdges([-1.0, 1.0])

        self.assertEqual(11, graph.vertexCount())
        self.assertNotEqual(-1, graph.findVertex(QgsPointXY(-1.0, 1.0)))


if __name__ == '__main__':
    unittest.main()
