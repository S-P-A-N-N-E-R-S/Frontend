#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz, Tim Hartmann
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
from qgis.core import QgsApplication, QgsRectangle, QgsCoordinateReferenceSystem, QgsProviderRegistry, QgsPointXY, QgsProviderMetadata, QgsUnitTypes, QgsVectorLayer, QgsRasterLayer

from ..models.QgsGraphLayer import QgsGraphLayer, QgsGraphLayerType, QgsGraphDataProvider
from ..models.GraphBuilder import GraphBuilder
from ..helperFunctions import getPluginPath

import os
import sys
import math


start_app()

# Append the path where processing plugin can be found
sys.path.append('/usr/share/qgis/python/plugins')

import processing
from processing.core.Processing import Processing
Processing.initialize()

class TestGraphBuilder(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.graphBuilder = GraphBuilder()

    def tearDown(self):
        """Runs after each test."""
        del self.graphBuilder

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

    def test_random_graph_complete_without_seed(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("connectionType", "Complete")

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(90, graph.edgeCount())

    def test_random_graph_nearestNeighbor(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("connectionType", "Nearest neighbor")
        self.graphBuilder.setOption("nnAllowDoubleEdges", False)
        self.graphBuilder.setOption("neighborNumber", 1)

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(9, graph.edgeCount())

        self.graphBuilder.setOption("nnAllowDoubleEdges", True)
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("neighborNumber", 2)

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(20, graph.edgeCount())

    def test_random_graph_clusterComplete(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("connectionType", "ClusterComplete")
        self.graphBuilder.setOption("clusterNumber", 10)

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(0, graph.edgeCount())

        self.graphBuilder.setOption("connectionType", "ClusterComplete")
        self.graphBuilder.setOption("clusterNumber", 9)

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(2, graph.edgeCount())

    def test_random_graph_clusterNN(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("connectionType", "ClusterNN")
        self.graphBuilder.setOption("nnAllowDoubleEdges", True)
        self.graphBuilder.setOption("neighborNumber", 1)
        self.graphBuilder.setOption("clusterNumber", 2)

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertLessEqual(9, graph.edgeCount())

    def test_random_graph_distanceNN(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("connectionType", "DistanceNN")
        self.graphBuilder.setOption("nnAllowDoubleEdges", True)
        self.graphBuilder.setOption("neighborNumber", 2)
        self.graphBuilder.setOption("distance", (1.0, QgsUnitTypes.DistanceDegrees))

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())

    def test_lineBasedConnection(self):
        # first test
        self.graphBuilder.setOption("connectionType", "LineLayerBased")
        self.graphBuilder.setOption("distance", (0.0, QgsUnitTypes.DistanceDegrees))
        self.graphBuilder.setOption("degreeThreshold", 5)
        self.graphBuilder.setOption("edgeDirection", "Undirected")
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/lineBased_connection_test_layer/lineBased_connection_points_1.shp")))
        self.graphBuilder.setLineLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/lineBased_connection_test_layer/lineBased_connection_lines_1.shp")))
        
        graph = self.graphBuilder.makeGraph()
        
        self.assertEqual(graph.edgeCount(), 5)
        self.assertNotEqual(graph.hasEdge(0,3), -1)
        self.assertNotEqual(graph.hasEdge(3,1), -1)
        self.assertNotEqual(graph.hasEdge(1,2), -1)
        self.assertNotEqual(graph.hasEdge(2,5), -1)
        self.assertNotEqual(graph.hasEdge(5,4), -1)
        
        # second test
        self.graphBuilder.setOption("degreeThreshold", 3)
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/lineBased_connection_test_layer/lineBased_connection_points_2.shp")))
        self.graphBuilder.setLineLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/lineBased_connection_test_layer/lineBased_connection_lines_2.shp")))
        
        graph = self.graphBuilder.makeGraph()
        
        self.assertEqual(graph.edgeCount(), 2)
        self.assertNotEqual(graph.hasEdge(1,2), -1)
        self.assertNotEqual(graph.hasEdge(2,0), -1)
        
        #third test
        self.graphBuilder.setOption("degreeThreshold", 5)
        graph = self.graphBuilder.makeGraph()
        self.assertEqual(graph.edgeCount(), 12)

    def test_cluster_number(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setOption("connectionType", "ClusterComplete")
        self.graphBuilder.setOption("clusterNumber", 4)

        graph = self.graphBuilder.makeGraph()

        def determine_clusters(graph):
            clusters = []
            for vertex in graph.vertices():
                # check if vertex already in a cluster
                inCluster = False
                for cluster in clusters:
                    if vertex in cluster:
                        inCluster = True

                if not inCluster:
                    # collect all cluster vertices of related vertex
                    clusterVertices = [vertex]
                    remainingVertices = [vertex]

                    # collect neighbors of remaining vertices
                    while remainingVertices:
                        remainingVertex = remainingVertices.pop()
                        inEdges = remainingVertex.incomingEdges()
                        outEdges = remainingVertex.outgoingEdges()
                        # iterate over adjacent vertices
                        for adjacentVertexId in [graph.edge(e).fromVertex() for e in inEdges] + [graph.edge(e).toVertex() for e in outEdges]:
                            adjacentVertex = graph.vertex(graph.findVertexByID(adjacentVertexId))
                            if adjacentVertex not in clusterVertices:
                                clusterVertices.append(adjacentVertex)
                                remainingVertices.append(adjacentVertex)
                    clusters.append(clusterVertices)

            return clusters

        self.assertEqual(4, len(determine_clusters(graph)))

    def test_setVectorLayer(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp")))
        self.graphBuilder.setOption("connectionType", "Complete")
        graph = self.graphBuilder.makeGraph()

        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(90, graph.edgeCount())

    def test_distanceNN(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp")))
        self.graphBuilder.setOption("connectionType", "DistanceNN")
        self.graphBuilder.setOption("nnAllowDoubleEdges", True)
        self.graphBuilder.setOption("distance", (0.5, QgsUnitTypes.DistanceDegrees))

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(0, graph.edgeCount())

        self.graphBuilder.setOption("distance", (1.1, QgsUnitTypes.DistanceDegrees))
        graph = self.graphBuilder.makeGraph()
        self.assertEqual(22, graph.edgeCount())

    def test_euclidean_distance_strategy(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp")))
        self.graphBuilder.setOption("connectionType", "Complete")
        self.graphBuilder.setOption("distanceStrategy", "Euclidean")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0, 1.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)
        if edgeIdx == -1:
            fromVertex = graph.findVertex(QgsPointXY(0, 1.0))
            toVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
            edgeIdx = graph.hasEdge(fromVertex, toVertex)

        self.assertEqual(math.sqrt(2), graph.costOfEdge(edgeIdx))

    def test_manhattan_distance_strategy(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp")))
        self.graphBuilder.setOption("connectionType", "Complete")
        self.graphBuilder.setOption("distanceStrategy", "Manhattan")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0, 1.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)
        if edgeIdx == -1:
            fromVertex = graph.findVertex(QgsPointXY(0, 1.0))
            toVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
            edgeIdx = graph.hasEdge(fromVertex, toVertex)

        self.assertEqual(2, graph.costOfEdge(edgeIdx))

    def test_geodesic_distance_strategy(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_vertices_layer/simple_graph_vertices_layer.shp")))
        self.graphBuilder.setOption("connectionType", "Complete")
        self.graphBuilder.setOption("distanceStrategy", "Geodesic")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0, 1.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)
        if edgeIdx == -1:
            fromVertex = graph.findVertex(QgsPointXY(0, 1.0))
            toVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
            edgeIdx = graph.hasEdge(fromVertex, toVertex)

        self.assertEqual(157249.38127194397, graph.costOfEdge(edgeIdx))

    def test_advanced_distance_strategy_with_raster(self):
        self.graphBuilder.setOption("distanceStrategy", "Advanced")
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp")))
        self.graphBuilder.setRasterLayer(QgsRasterLayer(os.path.join(getPluginPath(), "tests/testdata/simple_raster.tif")))

        self.graphBuilder.addCostFunction("raster[0]:sum")
        self.graphBuilder.addCostFunction("raster[0]:min")
        self.graphBuilder.addCostFunction("raster[0]:mean")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0.0, 0.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)

        self.assertEqual(7.0, graph.costOfEdge(edgeIdx))
        self.assertEqual(2.0, graph.costOfEdge(edgeIdx, 1))
        self.assertEqual(3.5, graph.costOfEdge(edgeIdx, 2))

    def test_fields_in_advance_distance_strategy(self):
        self.graphBuilder.setOption("distanceStrategy", "Advanced")
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp")))

        self.graphBuilder.addCostFunction("field:edgeId")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0.0, 0.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)

        self.assertEqual(graph.edge(edgeIdx).id(), graph.costOfEdge(edgeIdx, 0))

    def test_polygons_in_advanced_distance_strategy(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp")))
        self.graphBuilder.setPolygonsForCostFunction(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_polygons/simple_polygons.shp")))
        self.graphBuilder.addCostFunction("if(polygon[0]:crossesPolygon == True; 1; 0)")
        self.graphBuilder.addCostFunction("if(polygon[0]:insidePolygon == True; 1; 0)")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0.0, 0.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)
        self.assertEqual(0, graph.costOfEdge(edgeIdx, 0))
        self.assertEqual(0, graph.costOfEdge(edgeIdx, 1))

        fromVertex = graph.findVertex(QgsPointXY(-1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0.0, 0.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)
        self.assertEqual(1, graph.costOfEdge(edgeIdx, 0))
        self.assertEqual(0, graph.costOfEdge(edgeIdx, 1))

    def test_math_in_advanced_distance_strategy(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp")))
        self.graphBuilder.addCostFunction("math.sqrt(9)")

        graph = self.graphBuilder.makeGraph()
        fromVertex = graph.findVertex(QgsPointXY(1.0, 0.0))
        toVertex = graph.findVertex(QgsPointXY(0.0, 0.0))
        edgeIdx = graph.hasEdge(fromVertex, toVertex)
        self.assertEqual(3, graph.costOfEdge(edgeIdx, 0))

    def test_forbidden_areas(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp")))
        self.graphBuilder.setForbiddenAreas(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_polygons/simple_polygons.shp")))

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(10, graph.vertexCount())
        self.assertEqual(5, graph.edgeCount())

    def test_additional_point_layer(self):
        self.graphBuilder.setVectorLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_graph_edges_layer/simple_graph_edges_layer.shp")))
        self.graphBuilder.setAdditionalPointLayer(QgsVectorLayer(os.path.join(getPluginPath(), "tests/testdata/simple_points/simple_points.shp")))

        graph = self.graphBuilder.makeGraph()
        self.assertEqual(12, graph.vertexCount())
        self.assertEqual(18, graph.edgeCount())

    def test_random_seed(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setRandomOption("seed", 4)
        self.graphBuilder.setOption("connectionType", "Nearest neighbor")

        firstGraph = self.graphBuilder.makeGraph()
        self.assertEqual(10, firstGraph.vertexCount())

        secondGraph = self.graphBuilder.makeGraph()
        self.assertEqual(10, secondGraph.vertexCount())
        self.assertEqual(firstGraph.edgeCount(), secondGraph.edgeCount())

        for vertexIdx in range(len(firstGraph.vertices())):
            self.assertEqual(firstGraph.vertex(vertexIdx).point(), secondGraph.vertex(vertexIdx).point())

        for edgeIdx in range(len(firstGraph.edges())):
            self.assertEqual(firstGraph.edge(edgeIdx).fromVertex(), secondGraph.edge(edgeIdx).fromVertex())
            self.assertEqual(firstGraph.edge(edgeIdx).toVertex(), secondGraph.edge(edgeIdx).toVertex())

    def test_random_area_extent(self):
        self.graphBuilder.setRandomOption("numberOfVertices", 10)
        self.graphBuilder.setRandomOption("area", (QgsRectangle(-50, -50, 50, 50), QgsCoordinateReferenceSystem("EPSG:4326")))

        graph = self.graphBuilder.makeGraph()
        rectangle = QgsRectangle(-50, -50, 50, 50)
        for vertex in graph.vertices():
            self.assertTrue(rectangle.contains(vertex.point()))


if __name__ == '__main__':
    unittest.main()
