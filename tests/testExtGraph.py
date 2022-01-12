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
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem

from ..models.ExtGraph import ExtGraph
from ..models.GraphBuilder import GraphBuilder
from ..helperFunctions import getPluginPath

import os
import tempfile
import math
import shutil

start_app()


class TestExtGraph(TestCase):

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
        vertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 0.5), 7)
        self.assertEqual(7, vertex.id())
        self.assertEqual(QgsPointXY(1.0, 0.5), vertex.point())

        vertex.setNewPoint(QgsPointXY(2.0, 3.4))
        self.assertEqual(7, vertex.id())
        self.assertEqual(QgsPointXY(2.0, 3.4), vertex.point())

    def test_edge_class(self):
        fromVertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 2.0), 7)
        toVertex = ExtGraph.ExtVertex(QgsPointXY(1.0, 3.5), 2)
        edge = ExtGraph.ExtEdge(fromVertex.id(), toVertex.id(), 2, True)
        self.assertEqual(2, edge.id())
        self.assertEqual(7, edge.fromVertex())
        self.assertEqual(2, edge.toVertex())
        self.assertTrue(edge.highlighted())

        edge.toggleHighlight()
        self.assertFalse(edge.highlighted())

    def test_vertex_addition(self):
        firstIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        thirdIndex = self.graph.addVertex(QgsPointXY(0.0, 1.0))
        fourthIndex = self.graph.addVertex(QgsPointXY(1.0, 0.0))

        self.assertEqual(4, self.graph.vertexCount())

        fifthIndex = self.graph.addVertex(QgsPointXY(0.5, 0.5))
        self.assertEqual(5, self.graph.vertexCount())

        self.assertEqual(QgsPointXY(1.0, 1.0), self.graph.vertex(firstIndex).point())
        self.assertEqual(QgsPointXY(0.0, 1.0), self.graph.vertex(thirdIndex).point())
        self.assertEqual(QgsPointXY(0.5, 0.5), self.graph.vertex(fifthIndex).point())

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

        self.assertEqual(3, self.graph.edgeCount())
        self.assertEqual(thirdEdgeIndex, self.graph.hasEdge(secondVertexIndex, thirdVertexIndex))
        self.assertEqual(-1, self.graph.hasEdge(thirdVertexIndex, secondVertexIndex))
        self.assertEqual(-1, self.graph.hasEdge(firstVertexIndex, thirdVertexIndex))

        self.assertEqual(5, self.graph.edge(thirdEdgeIndex).id())
        self.assertEqual(secondVertex.id(), self.graph.edge(thirdEdgeIndex).fromVertex())
        self.assertEqual(thirdVertex.id(), self.graph.edge(thirdEdgeIndex).toVertex())
        self.assertEqual(secondEdgeIndex, self.graph.findEdgeByID(3))
        self.assertEqual(firstEdgeIndex, self.graph.findEdgeByID(4))
        self.assertEqual(thirdEdgeIndex, self.graph.findEdgeByID(5))

    def test_vertex_removal(self):
        firstIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        self.assertEqual(2, self.graph.vertexCount())

        firstVertex = self.graph.vertex(firstIndex)
        secondVertex = self.graph.vertex(secondIndex)

        self.graph.deleteVertex(secondIndex)
        self.assertEqual(1, self.graph.vertexCount())
        self.assertRaises(IndexError, self.graph.vertex, secondIndex)

        thirdIndex = self.graph.addVertex(QgsPointXY(0.5, 0.5))
        thirdVertex = self.graph.vertex(thirdIndex)
        self.assertEqual(2, self.graph.vertexCount())
        self.assertEqual(2, len(self.graph.vertices()))
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

        self.assertEqual(3, self.graph.edgeCount())
        self.assertTrue(self.graph.deleteEdge(secondEdgeIndex))
        self.assertEqual(2, self.graph.edgeCount())

        fourthIndex = self.graph.addEdge(fourthVertex.id(), firstVertex.id())
        fourthEdge = self.graph.edge(fourthIndex)
        self.assertEqual(3, self.graph.edgeCount())
        self.assertEqual(3, len(self.graph.edges()))
        for edge in self.graph.edges():
            self.assertIn(edge, [firstEdge, thirdEdge, fourthEdge])

    def test_read_graphML(self):
        graphmlFile = os.path.join(getPluginPath(), "tests/testdata/simple_graph.graphml")
        self.graph.readGraphML(graphmlFile)

        self.assertEqual(10, self.graph.vertexCount())
        self.assertEqual(15, self.graph.edgeCount())

        # check some vertices
        self.assertEqual(QgsPointXY(0, -1.0), self.graph.vertex(self.graph.findEdgeByID(3)).point())
        self.assertEqual(QgsPointXY(0.0, 0.0), self.graph.vertex(self.graph.findEdgeByID(0)).point())
        self.assertEqual(QgsPointXY(2.0, 0), self.graph.vertex(self.graph.findEdgeByID(5)).point())

        # check some edges
        vertex = self.graph.vertex(self.graph.findEdgeByID(0))
        outgoingEdges = vertex.outgoingEdges()
        self.assertEqual(3, len(outgoingEdges))
        incomingEdges = vertex.incomingEdges()
        self.assertEqual(5, len(incomingEdges))

        self.assertNotEqual(-1, self.graph.hasEdge(self.graph.findEdgeByID(0), self.graph.findEdgeByID(1)))
        self.assertNotEqual(-1, self.graph.hasEdge(self.graph.findEdgeByID(3), self.graph.findEdgeByID(1)))
        self.assertNotEqual(-1, self.graph.hasEdge(self.graph.findEdgeByID(4), self.graph.findEdgeByID(3)))

    def test_write_graphML(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        firstVertex = self.graph.vertex(firstVertexIndex)
        secondVertex = self.graph.vertex(secondVertexIndex)

        firstEdgeIndex = self.graph.addEdge(firstVertex.id(), secondVertex.id())
        secondEdgeIndex = self.graph.addEdge(secondVertex.id(), firstVertex.id())
        firstEdge = self.graph.edge(firstEdgeIndex)
        secondEdge = self.graph.edge(secondEdgeIndex)

        temp_file = os.path.join(self.tempDir, "graph.graphml")
        self.graph.writeGraphML(temp_file)

        temp_graph = ExtGraph()
        temp_graph.readGraphML(temp_file)
        self.assertEqual(2, temp_graph.edgeCount())
        self.assertEqual(2, temp_graph.vertexCount())

        self.assertEqual(QgsPointXY(1.0, 1.0), temp_graph.vertex(temp_graph.findEdgeByID(firstVertex.id())).point())
        self.assertEqual(QgsPointXY(0.0, 0.0), temp_graph.vertex(temp_graph.findEdgeByID(secondVertex.id())).point())

        self.assertNotEqual(-1, temp_graph.hasEdge(temp_graph.findEdgeByID(firstVertex.id()), temp_graph.findEdgeByID(secondVertex.id())))
        self.assertNotEqual(-1, temp_graph.hasEdge(temp_graph.findEdgeByID(secondVertex.id()), temp_graph.findEdgeByID(firstVertex.id())))

    def test_edge_costs(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        firstVertex = self.graph.vertex(firstVertexIndex)
        secondVertex = self.graph.vertex(secondVertexIndex)

        edgeIndex = self.graph.addEdge(firstVertex.id(), secondVertex.id())
        edge = self.graph.edge(edgeIndex)
        # self.graph.crs = QgsCoordinateReferenceSystem("EPSG:4326")
        self.graph.updateCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        self.graph.setDistanceStrategy("Euclidean")
        self.assertEqual(math.sqrt(2), self.graph.costOfEdge(edgeIndex))
        self.graph.setDistanceStrategy("Manhattan")
        self.assertEqual(2, self.graph.costOfEdge(edgeIndex))
        self.graph.setDistanceStrategy("Geodesic")
        self.assertEqual(157249.38127194397, self.graph.costOfEdge(edgeIndex))
        self.graph.setDistanceStrategy("Ellipsoidal")
        self.assertLess(156899, self.graph.costOfEdge(edgeIndex))
        self.assertGreater(156900, self.graph.costOfEdge(edgeIndex))
        self.graph.setDistanceStrategy("Advanced")
        self.graph.setCostOfEdge(edgeIndex, 0, 12)
        self.graph.setCostOfEdge(edgeIndex, 1, 24)
        self.assertEqual(12, self.graph.costOfEdge(edgeIndex, 0))
        self.assertEqual(24, self.graph.costOfEdge(edgeIndex, 1))

        self.assertEqual(math.sqrt(2), self.graph.distanceP2P(firstVertexIndex, secondVertexIndex))

    def test_findVertexByID(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0), ID=12)
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0), ID=4)
        thirdVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 1.0), ID=9)
        fourthVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 0.0), ID=0)

        self.assertEqual(firstVertexIndex, self.graph.findVertexByID(12))
        self.assertEqual(secondVertexIndex, self.graph.findVertexByID(4))
        self.assertEqual(thirdVertexIndex, self.graph.findVertexByID(9))
        self.assertEqual(fourthVertexIndex, self.graph.findVertexByID(0))

    def test_find_vertex(self):
        firstVertexIndex = self.graph.addVertex(QgsPointXY(1.0, 1.0))
        secondVertexIndex = self.graph.addVertex(QgsPointXY(0.0, 0.0))

        self.assertEqual(firstVertexIndex, self.graph.findVertex(QgsPointXY(1.5, 1.0), 1))
        self.assertEqual(secondVertexIndex, self.graph.findVertex(QgsPointXY(0.0, 0.0), 0))

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
