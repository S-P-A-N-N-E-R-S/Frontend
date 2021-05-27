from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
from .PGGraph import PGGraph
from random import *
from qgis import processing
from .FunctionLibrary import *
import math


"""
Instuctions:

Call the makeGraph() method of this class to build a graph:
    ga = GraphBuilder()
    graph = ga.makeGraph()

To set the vector layer call:
    ga.setVectorLayer(vectorlayer)
    
To set the raster layer call:
    ga.setRasterLayer(rasterlayer)

Differet options for special graph creation can be set before calling makeGraph():
    ga.setOption(optionType, value) with optionType being a string
    
If you want to create a special random graph use:
    ga.setRandomOptions(optionType, value)    



Supported options:
    - connectionType: None, Complete, Nearest neighbor, ShortestPathNetwork
    - neighborNumber: int
    - edgeDirection: Undirected, Directed
    - distanceStrategy: Euclidean, Manhatten, Speed
    - speedOption: Attribute field with the speed information
    - useRasterData: False, True
    - createGraphAsLayers: False, True
    - createRandomGraph: False, True
        - further definitions possible at randomOptions dict             

Supported random options:
    - numberOfVertices: int
    - area: Area of the globe you want the random Graph to be in

Raster data options:
    - typeOfData
    - costFunction: Climb, notAllowedAreas
    - threshold
    
    
---> Not all of the options are implemented (more a list of possible options)    

"""
class GraphBuilder:
    
    def __init__(self):
        self.graph = PGGraph()
        
        #TODO: load example data into the two layers
        self.vLayer = QgsVectorLayer()
        self.rLayer = QgsRasterLayer()
        self.polygonLayer = QgsVectorLayer()
        self.additionalLineLayer = QgsVectorLayer()
        
        self.__options = {
            "connectionType": "Nearest neighbor",            
            "neighborNumber": 5,       
            "edgeDirection": "Directed",
            "distanceStrategy": "Euclidean",
            "speedOptions": [1, 50, 1],
            "useRasterData": False,
            "createGraphAsLayers": True,
            "createRandomGraph": True,          
            "usePolygons": False
                       
        }
        self.__randomOptions = {
            "numberOfVertices": 100,
            "area": "Germany",
                  
        }
        
    def setGraph(self, graph):
        self.graph = graph
    
    def setPolygonLayer(self, vectorLayer):
        self.__options["usePolygons"] = True
        self.polygonLayer = vectorLayer
        
    def setAdditionalLineLayer(self, vectorLayer):
        self.__options["connectionType"] = "ShortestPathNetwork"
        self.additionalLineLayer = vectorLayer
        
    def setVectorLayer(self, vectorLayer):
        self.__options["createRandomGraph"] = False
        self.vLayer = vectorLayer    
        
        
    def setRasterLayer(self, rasterLayer):
        self.__options["useRasterData"] = True;
        self.rLayer = rasterLayer
    
    
    def setOption(self, optionsType, value):
        #TODO: check if inputs are valid
        self.__options[optionsType] = value
    
    def setRandomOptions(self, optionType, value):
        #TODO: check if inputs are valid
        self.__randomOptions[optionType] = value        
    
    def createRandomVertices(self):
        for i in range(self.__randomOptions["numberOfVertices"]):
            if self.__randomOptions["area"] == "Germany":
                self.graph.addVertex(QgsPointXY(randrange(742723,1534455), randrange(6030995,7314884))) 
    
    def createVerticesForPoints(self):
       
        
        for feat in self.vLayer.getFeatures():
            geom = feat.geometry()                
            self.graph.addVertex(geom.asPoint())
            
    def createComplete(self):
        for i in range(self.graph.vertexCount()):
            for j in range(i+1, self.graph.vertexCount()):                                                                              
                self.graph.addEdge(i, j)
                        
            
            
    def createNearestNeighbor(self):
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
            
            if self.graph.vertexCount() < self.__options["neighborNumber"]:
                self.__options["neighborNumber"] = self.graph.vertexCount()-1
            
            # get the defined amount of neighbors
            for k in range(self.__options["neighborNumber"]):
                minIndex = 0
                minValue = maxDistanceValue+1
                for p in range(len(distances)):
                    if distances[p] < minValue:
                        minIndex = p
                        minValue = distances[p]
                        
                # add edge                
                if not self.graph.hasEdge(minIndex, i):
                    self.graph.addEdge(i,minIndex)
                          
                
                # don't look at minIndex again
                distances[minIndex] = maxDistanceValue+1           
            
    def createShortestPathNetwork(self):
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
     
    
    def createGraphForLineGeometry(self):
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
                   
    
    def removeIntersectingEdges(self):               
        currentEdges = self.__createEdgeLayer(False)
        result2 = processing.run("native:extractbylocation", {"INPUT": currentEdges, "PREDICATE": 2, "INTERSECT": self.polygonLayer, "OUTPUT": "memory:"})         
        layerWithDelEdges = result2["OUTPUT"]
        
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
    
    def createVertexLayer(self, addToCanvas):
        graphLayerVertices = QgsVectorLayer("Point", "GraphVertices", "memory")
        dpVerticeLayer = graphLayerVertices.dataProvider()
        dpVerticeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("X", QVariant.Double), QgsField("Y", QVariant.Double)])
        graphLayerVertices.updateFields()  
        
        if self.__options["createRandomGraph"] == False:            
            graphLayerVertices.setCrs(self.vLayer.crs())  
        else:
            graphLayerVertices.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))       
        
    
        #add the vertices and edges to the layers
        for i in range(self.graph.vertexCount()):
            newFeature = QgsFeature()
            newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))  
            newFeature.setAttributes([i, self.graph.vertex(i).point().x(), self.graph.vertex(i).point().y()])
            dpVerticeLayer.addFeature(newFeature)
            
            
        if addToCanvas == True:
            QgsProject.instance().addMapLayer(graphLayerVertices)    
    
    # create the two layers that represent the graph
    def createEdgeLayer(self, addToCanvas):
        
        graphLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")
        
        dpEdgeLayer = graphLayerEdges.dataProvider()
        
        
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("fromVertex",QVariant.Double), QgsField("toVertex",QVariant.Double),QgsField("weight", QVariant.Double)])
        graphLayerEdges.updateFields() 
        
        
        if self.__options["createRandomGraph"] == False:            
            graphLayerEdges.setCrs(self.vLayer.crs())  
        else:
            graphLayerEdges.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))       
        
        
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
            if self.__options["createRandomGraph"] == False:
                graphLayerEdges.setCrs(self.vLayer.crs())
            else:
                graphLayerEdges.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))    
                
            QgsProject.instance().addMapLayer(graphLayerEdges)
       
        return graphLayerEdges

    #returns the graph    
    def makeGraph(self):
                                                                      
        if self.__options["createRandomGraph"] == True:
            self.createRandomVertices()
        else:          
            if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                self.createVerticesForPoints()                   
        if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry or self.__options["createRandomGraph"] == True:                          
            if self.__options["connectionType"] == "Complete":
                self.createComplete()                        
            elif self.__options["connectionType"] == "Nearest neighbor":
                self.createNearestNeighbor()                
            elif self.__options["connectionType"] == "ShortestPathNetwork":
                self.createShortestPathNetwork()                                               
        elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:      
            self.createGraphForLineGeometry()
                      
        if self.__options["edgeDirection"] == "Undirected":
            eCount = self.graph.edgeCount()
            for i in range(eCount):
                edge = self.graph.edge(i)
                self.graph.addEdge(edge.toVertex(), edge.fromVertex())  
            
                
        if self.__options["usePolygons"] == True:
            self.removeIntersectingEdges()        
      
      
      
        if(self.__options["createGraphAsLayers"] == True):
            self.createVertexLayer(True)
            self.createEdgeLayer(True)
        
        return self.graph
        
        
        
        
        
    
    
        
       
