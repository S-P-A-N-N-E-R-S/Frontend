from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
from .PGGraph import PGGraph
from .AdvancedCostCalculator import AdvancedCostCalculator
from random import *
from qgis import processing
import math
import re



class GraphBuilder:
    """
    The GraphBuilder offers the possibility to build different graphs in QGIS. Define the desired graph
    by setting options and layers before calling the makeGraph method.

    Options:
        - connectionType: None, Complete, Nearest neighbor, ShortestPathNetwork
        - neighborNumber: int
        - edgeDirection: Undirected, Directed
        - distanceStrategy: Euclidean, Manhattan, Geodesic, Advanced
        - createGraphAsLayers: False, True
        - createRandomGraph: False, True        
        - usePolygons: False, True
    
    Random options:
        - numberOfVertices: int
        - area: Area of the globe you want the random Graph to be in
        - crs: ID for the crs to use    
        
    """
    
    def __init__(self):
        """
        Constructor:
        Initial setting for the GraphBuilder. If no additional options or layers are set, a random
        graph with a nearest neighbor connection is generated.
        """
        self.graph = PGGraph()        
        self.vLayer = QgsVectorLayer()
        self.rLayers = []
        self.polygonLayer = QgsVectorLayer()
        self.additionalLineLayer = QgsVectorLayer()
        self.additionalPointLayer = QgsVectorLayer()
        self.costFunctions = []
       
        
        self.__options = {
            "connectionType": "Nearest neighbor",            
            "neighborNumber": 4,       
            "edgeDirection": "Directed",
            "distanceStrategy": "Euclidean",
            "useRasterData": False,
            "createGraphAsLayers": True,
            "createRandomGraph": True,          
            "usePolygons": False,   
                              
        }
        
        self.__randomOptions = {
            "numberOfVertices": 100,
            "area": "Germany",
            "crs": ""      
        }
    
    def setPolygonLayer(self, vectorLayer):
        """
        All edges crossing the polygon will be deleted from the graph
        
        :type vectorLayer: QgsVectorLayer containing polygons
        """
        if vectorLayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise TypeError("Not a polygon geometry")                     
        
        self.__options["usePolygons"] = True
        self.polygonLayer = vectorLayer
    
    def setAdditionalPointLayer(self, vectorLayer): 
        """
        Additional points to a given line layer. The points will be added in addition to the
        network generated for the line layer and connected to the nearest point
        
        :type vectorLayer: QgsVectorLayer containing points
        """       
        if vectorLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point geometry") 
        
        self.additionalPointLayer = vectorLayer
        
    def setAdditionalLineLayer(self, vectorLayer):
        """
        Additional network for given point layer. The points will be connected by the 
        shortest path in the network.
        
        :type vectorLayer: QgsVectorLayer containing lines
        """
        if vectorLayer.geometryType() != QgsWkbTypes.LineGeometry:
            raise TypeError("Not a line geometry") 
        
        self.__options["connectionType"] = "ShortestPathNetwork"
        self.additionalLineLayer = vectorLayer
        
    def setVectorLayer(self, vectorLayer):
        """
        Set the basis vector layer for the graph creation.
        
        :type vectorLayer: QgsVectorLayer containing lines or points
        """
        if vectorLayer.geometryType() != QgsWkbTypes.LineGeometry and vectorLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point or line geometry") 
       
        self.__options["createRandomGraph"] = False
        self.vLayer = vectorLayer    
                
    def setRasterLayer(self, rasterLayer):
        """
        Set raster data to be used in the AdvancedCostCalculator class.
        
        :type QgsRasterLayer
        """
        self.__options["useRasterData"] = True;
        self.rLayers.append(rasterLayer)
    
    def setCostFunction(self, function):
        """
        Set the cost function for an advanced distance strategy. Returns if the
        function has a valid format and the function is set. 
        
        :type function: String
        :return Boolean
        """  
        self.__options["distanceStrategy"] = "Advanced"
        costFunction = function.replace(" ", "").replace('"', '')            
        formulaParts = re.split("\+|-|\*|/", costFunction)
        possibleMetrics = ["euclidean", "manhattan", "geodesic"]
        possibleRasterAnalysis = ["raster:sum", "raster:mean", "raster:median", "raster:min",
                                  "raster:max", "raster:variance", "raster:standDev", "raster:majority",
                                  "raster:minority", "raster:gradientSum", "raster:gradientMin", "raster:gradientMax"]
        
        for i in range(len(formulaParts)):            
            var = formulaParts[i]
            if not (var in possibleMetrics or var.isnumeric() or "if" in var or "field:" in var or "math." in var or "raster:" in var):
                return False
            if "raster:"  in var:
                if not var in possibleRasterAnalysis:
                    return False
                                
        self.costFunctions.append(function)
        return True
    
    def setOption(self, optionsType, value):
        if not optionsType in self.__options:
            raise KeyError("Option not found")                
        self.__options[optionsType] = value
    
    def setRandomOptions(self, optionType, value):
        if not optionType in self.__randomOptions:
            raise KeyError("Option not found")
        self.__randomOptions[optionType] = value        
    
    def __createRandomVertices(self):
        for i in range(self.__randomOptions["numberOfVertices"]):
            if self.__randomOptions["area"] == "Germany":
                self.graph.addVertex(QgsPointXY(randrange(742723,1534455), randrange(6030995,7314884))) 
            elif self.__randomOptions["area"] == "France":
                self.graph.addVertex(QgsPointXY(randrange(-216458,686688), randrange(5414887,6442792)))     
            elif self.__randomOptions["area"] == "Osnabrueck":
                self.graph.addVertex(QgsPointXY(randrange(891553,903357), randrange(6842102,6856659))) 
            elif self.__randomOptions["area"] == "United States":
                self.graph.addVertex(QgsPointXY(randrange(-13615804,-7941914), randrange(3807078,6115319)))     
            elif self.__randomOptions["area"] == "Rome":
                self.graph.addVertex(QgsPointXY(randrange(1378926,1402097), randrange(5131959,5158304))) 
            elif self.__randomOptions["area"] == "Australia":
                self.graph.addVertex(QgsPointXY(randrange(12842159,16797763), randrange(-4432001,-1569266)))     
    
    def __createVerticesForPoints(self):        
        for feat in self.vLayer.getFeatures():
            geom = feat.geometry()                
            self.graph.addVertex(geom.asPoint())
            
    def __createComplete(self):
        for i in range(self.graph.vertexCount()):
            for j in range(i+1, self.graph.vertexCount()):                                                                              
                self.graph.addEdge(i, j)
                                              
    def __createNearestNeighbor(self):
        if self.graph.vertexCount() < self.__options["neighborNumber"]:
            self.__options["neighborNumber"] = self.graph.vertexCount()-1
        # calculate shortest distances between all pairs of nodes                
        for i in range(self.graph.vertexCount()):
            distances = []
            maxDistanceValue = 0
            for j in range(self.graph.vertexCount()):               
                distanceP2P = self.graph.distanceP2P(i,j)
                distances.append(distanceP2P)    
                if(distanceP2P > maxDistanceValue):
                    maxDistanceValue = distanceP2P                            
            distances[i] = maxDistanceValue+100
                       
            # get the defined amount of neighbors
            for k in range(self.__options["neighborNumber"]):
                minIndex = 0
                minValue = maxDistanceValue+100
                for p in range(len(distances)):
                    if distances[p] < minValue:
                        minIndex = p
                        minValue = distances[p]
                        
                # add edge                
                if not self.graph.hasEdge(minIndex, i):
                    self.graph.addEdge(i,minIndex)
                                         
                # don't look at minIndex again
                distances[minIndex] = maxDistanceValue+100           
            
    def __createShortestPathNetwork(self):
        if self.__options["createRandomGraph"] == False:           
            crs = self.vLayer.crs().authid()
        else:                    
            crs = "EPSG:4326" 
        
        endNodes = []
        newGraph = PGGraph()
        for i in range(self.graph.vertexCount()-1):   
            help = 0                                   
            for j in range(i+1, self.graph.vertexCount()):    
                point1Coordinates = str(self.graph.vertex(i).point().x()) + "," + str(self.graph.vertex(i).point().y()) + " [" + crs +"]"
                point2Coordinates = str(self.graph.vertex(j).point().x()) + "," + str(self.graph.vertex(j).point().y()) + " [" + crs + "]"                                                      
                result = processing.run("qgis:shortestpathpointtopoint", {"INPUT": self.additionalLineLayer, "START_POINT": point1Coordinates, "END_POINT": point2Coordinates, "OUTPUT": "memory:"})                        
                layer = result["OUTPUT"]  
                                                               
                for feature in layer.getFeatures():                                                      
                    geom = feature.geometry()
                    vertices = geom.asPolyline()                       
                    for k in range(len(vertices)-1): 
                        if k == 0:                                   
                            endNodes.append(vertices[k])
                            endNodes.append(vertices[len(vertices)-1])                                
                        startVertex = vertices[k]                                  
                        endVertex = vertices[k+1]
                        if newGraph.findVertex(startVertex) == -1 or newGraph.findVertex(endVertex) == -1:                                   
                            id1 = newGraph.addVertex(startVertex)
                            id2 = newGraph.addVertex(endVertex)                                    
                            newGraph.addEdge(id1, id2)
                                                                                                                                                                                                                                                                                            
        # add vertices from the point layer and create an edge to the network        
        for i in range(self.graph.vertexCount()):
            nearestVertex = 0
            newVertex = newGraph.addVertex(self.graph.vertex(i).point())
            distanceP2PMin = newGraph.distanceP2P(newVertex, newGraph.findVertex(endNodes[0]))                     
            for j in range(1,len(endNodes)):  
                id = newGraph.findVertex(endNodes[j])                     
                distanceP2P = newGraph.distanceP2P(newVertex, id)
                if distanceP2P < distanceP2PMin:
                    distanceP2PMin = distanceP2P
                    nearestVertex = id            
               
            newGraph.addEdge(newVertex, nearestVertex)                   
        
        self.graph = newGraph 
     
    
    def __createGraphForLineGeometry(self):        
        # get all the lines and set end nodes as vertices and connections as edges
        for feature in self.vLayer.getFeatures():                   
            geom = feature.geometry()
            
            if QgsWkbTypes.isMultiType(geom.wkbType()):                 
                for part in geom.asMultiPolyline():
                    for i in range(len(part)):
                        addedID = self.graph.addVertex(part[i]) 
                        if i!=0:                               
                            self.graph.addEdge(addedID-1, addedID)
                                                                         
            else:                        
                vertices = geom.asPolyline()                       
                for i in range(len(vertices)-1):
                    startVertex = vertices[i]
                    endVertex = vertices[i+1]
                    id1 = self.graph.addVertex(startVertex)
                    id2 = self.graph.addVertex(endVertex)                    
                    self.graph.addEdge(id1, id2)
        
        # add points and connection to network if additional points are given           
        for feature in self.additionalPointLayer.getFeatures():          
            geom = feature.geometry()
            pointID = self.graph.addVertex(geom.asPoint())
            
            # search nearest node in network
            nearestNodeID = 0
            shortestDist = self.graph.distanceP2P(pointID, 0)
            for i in range(1, self.graph.vertexCount()):
                if i!= pointID:
                    currentDist = self.graph.distanceP2P(pointID, i)
                    if currentDist < shortestDist:
                        nearestNodeID = i
                        shortestDist = currentDist
            
            self.graph.addEdge(pointID, nearestNodeID)        
    
    def __removeIntersectingEdges(self): 
        # create the current edge layer              
        currentEdges = self.__createEdgeLayer(False)
        # call QGIS tool to extract all the edges which cross the polygon
        result2 = processing.run("native:extractbylocation", {"INPUT": currentEdges, "PREDICATE": 2, "INTERSECT": self.polygonLayer, "OUTPUT": "memory:"})         
        layerWithDelEdges = result2["OUTPUT"]
        
        # copy the result of the QGIS tool into a new graph
        newGraph = PGGraph()
        for feature in layerWithDelEdges.getFeatures():                   
            geom = feature.geometry()
                                            
            vertices = geom.asPolyline()                       
            for i in range(len(vertices)-1):
                startVertex = vertices[i]
                endVertex = vertices[i+1]
                id1 = newGraph.addVertex(startVertex)
                id2 = newGraph.addVertex(endVertex)                    
                newGraph.addEdge(id1, id2)
        
        
        self.graph = newGraph
    
    def __createVertexLayer(self, addToCanvas):
        """
        Method creates a QgsVectorLayer containing points. The points are the vertices of the graph.
        
        :type addToCanvas: Boolean
        :return QgsVectorLayer
        """
        graphLayerVertices = QgsVectorLayer("Point", "GraphVertices", "memory")
        dpVerticeLayer = graphLayerVertices.dataProvider()
        dpVerticeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("X", QVariant.Double), QgsField("Y", QVariant.Double)])
        graphLayerVertices.updateFields()  
        
        if self.__options["createRandomGraph"] == False:            
            graphLayerVertices.setCrs(self.vLayer.crs())  
        else:
            if self.__randomOptions["crs"] == "":                
                graphLayerVertices.setCrs(QgsProject.instance().crs())
            else:
                graphLayerVertices.setCrs(QgsCoordinateReferenceSystem(self.__randomOptions["crs"]))       
        
    
        #add the vertices and edges to the layers
        for i in range(self.graph.vertexCount()):
            newFeature = QgsFeature()
            newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))  
            newFeature.setAttributes([i, self.graph.vertex(i).point().x(), self.graph.vertex(i).point().y()])
            dpVerticeLayer.addFeature(newFeature)
            
            
        if addToCanvas == True:
            QgsProject.instance().addMapLayer(graphLayerVertices)    
    
        return graphLayerVertices
       
    def __createEdgeLayer(self, addToCanvas):
        """
        Method creates a QgsVectorLayer containing lines. The lines are the edges of the graph. The weights are
        visible by creating labels.
        
        :type addToCanvas: Boolean
        :return QgsVectorLayer
        """        
        graphLayerEdges = QgsVectorLayer("MultiLineString", "GraphEdges", "memory")        
        dpEdgeLayer = graphLayerEdges.dataProvider()
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("fromVertex",QVariant.Double), QgsField("toVertex",QVariant.Double),QgsField("weight", QVariant.Double)])
        graphLayerEdges.updateFields() 
                
        if self.__options["createRandomGraph"] == False:         
            graphLayerEdges.setCrs(self.vLayer.crs())  
        else:
            if self.__randomOptions["crs"] == "":                
                graphLayerEdges.setCrs(QgsProject.instance().crs())
            else:               
                graphLayerEdges.setCrs(QgsCoordinateReferenceSystem(self.__randomOptions["crs"]))      
                
        for i in range(self.graph.edgeCount()):
            newFeature = QgsFeature()
            fromVertex = self.graph.vertex(self.graph.edge(i).fromVertex()).point()
            toVertex = self.graph.vertex(self.graph.edge(i).toVertex()).point()
            newFeature.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))                              
            newFeature.setAttributes([i, self.graph.edge(i).fromVertex(), self.graph.edge(i).toVertex(), self.graph.costOfEdge(i)])
            dpEdgeLayer.addFeature(newFeature)

        if addToCanvas == True:        
            layer_settings  = QgsPalLayerSettings()
            text_format = QgsTextFormat()
    
            text_format.setFont(QFont("Arial", 12))
            text_format.setSize(12)
    
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(0.1)
            buffer_settings.setColor(QColor("black"))
    
            text_format.setBuffer(buffer_settings)
            layer_settings.setFormat(text_format)
    
            layer_settings.fieldName = "weight"
            layer_settings.placement = 2
    
            layer_settings.enabled = True
    
            layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
            graphLayerEdges.setLabelsEnabled(True)
            graphLayerEdges.setLabeling(layer_settings)
            graphLayerEdges.triggerRepaint()                             
            QgsProject.instance().addMapLayer(graphLayerEdges)
       
        return graphLayerEdges

       
    def makeGraph(self):
        """
        If this method is called the creation of the graph starts. The set options are read and 
        methods are called accordingly.   
        
        :return PGGraph    
        """                                                              
        if self.__options["createRandomGraph"] == True:
            self.__createRandomVertices()        
        else:          
            if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                self.__createVerticesForPoints()                   
        if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry or self.__options["createRandomGraph"] == True:                          
            if self.__options["connectionType"] == "Complete":
                self.__createComplete()                        
            elif self.__options["connectionType"] == "Nearest neighbor":
                self.__createNearestNeighbor()                
            elif self.__options["connectionType"] == "ShortestPathNetwork":
                self.__createShortestPathNetwork()                                               
        elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:      
            self.__createGraphForLineGeometry()
                      
        if self.__options["edgeDirection"] == "Undirected":
            eCount = self.graph.edgeCount()
            for i in range(eCount):
                edge = self.graph.edge(i)
                self.graph.addEdge(edge.toVertex(), edge.fromVertex())  
                            
        if self.__options["usePolygons"] == True:
            self.__removeIntersectingEdges()        
    
        # set distance strategy
        self.graph.setDistanceStrategy(self.__options["distanceStrategy"])
        
        # call AdvancedCostCalculations methods
        if self.__options["distanceStrategy"] == "Advanced":
            if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry and self.__options["connectionType"] == "ShortestPathNetwork":
                costCalculator = AdvancedCostCalculator(self.rLayers, self.additionalLineLayer, self.graph, True, self.__options["usePolygons"])                     
            else:
                costCalculator = AdvancedCostCalculator(self.rLayers, self.vLayer, self.graph, False, self.__options["usePolygons"])
            
            for func in self.costFunctions:
                self.graph = costCalculator.setEdgeCosts(func)  
              
        
        if self.__options["createGraphAsLayers"] == True:
            self.__createVertexLayer(True)
            self.__createEdgeLayer(True)
        
        return self.graph
        
        