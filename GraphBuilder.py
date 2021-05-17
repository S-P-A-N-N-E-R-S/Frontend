from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
from .PGGraph import PGGraph
from random import *

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
    - connectionType: None, Complete, Nearest neighbor, Tree
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
    - createWeights: True, False
    - rangeOfWeights: Array with two values for the random weights


"""
class GraphBuilder:
    
    def __init__(self):
        self.graph = PGGraph()
        #TODO: load example data into the two layers
        self.vLayer = QgsVectorLayer()
        self.rLayer = QgsRasterLayer()
        self.__options = {
            "connectionType": "Complete",          
            "edgeDirection": "Undirected",
            "distanceMetric": "Euclidean",
            "speedOptions": [1, 50, 1],
            "useRasterData": False,
            "createGraphAsLayers": True,
            "createRandomGraph": True
            
        }
        self.__randomOptions = {
            "numberOfVertices": 100,
            "area": "Germany",
            "createWeights": True,
            "rangeOfWeights": [0,100]       
        }
        
        
        
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
    
    
    def __createVertices(self):
        #build graph using the set vector layer
        #TODO: if vector layer is not set use example vectorlayer in ressource folder
        if self.__options["createRandomGraph"] == False:
        
            if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:                                        
                for feat in self.vLayer.getFeatures():
                    geom = feat.geometry()                
                    self.graph.addVertex(geom.asPoint())
                                             
            elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:
                print("TODO")
            
            elif self.vLayer.geometryType() == QgsWkbTypes.PolygonGeometry:
                print("TODO")
        
        #create random graph 
        #TODO: solve problem with the CRS: Point position on map depend on the currently 
        #selected CRS in the Qgis Project       
        else:
            for i in range(self.__randomOptions["numberOfVertices"]):
                self.graph.addVertex(QgsPointXY(randrange(1136014), randrange(6681824)))           
        
        
        
    def __createEdges(self):   
        #set selected distance metric for the graph 
        self.graph.distanceMetric = self.__options["distanceMetric"] 
        
        if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
            if self.__options["connectionType"] == "Complete":
                for i in range(self.graph.vertexCount()):
                    for j in range(self.graph.vertexCount()):
                        if i != j:                                                       
                            self.graph.addEdge(i, j)
                            if self.__options["edgeDirection"] == "Directed":
                                self.graph.addEdge(j, i)    
                                    
            
            elif self.options["connectionType"] == "Nearest neighbor":
                print("TODO")
            elif self.options["connectionType"] == "Tree":
                print("TODO")
                
                                
        elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:
            print("TODO")
        
        elif self.vLayer.geometryType() == QgsWkbTypes.PolygonGeometry:
            print("TODO")
         
            
        
    def __createEdgeWeights(self):
        print("TODO")
    
    #TODO:(possible remove/replace for custom layer type)
    #create the two layers that represent the graph
    def __createLayers(self):
        graphLayerVertices = QgsVectorLayer("Point", "GraphVertices", "memory")
        graphLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")
        dpVerticeLayer = graphLayerVertices.dataProvider()
        dpEdgeLayer = graphLayerEdges.dataProvider()
        dpVerticeLayer.addAttributes([QgsField("ID", QVariant.Int)])
        graphLayerVertices.updateFields()
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("fromVertex",QVariant.Int), QgsField("toVertex",QVariant.Int),QgsField("weight", QVariant.Int)])
        graphLayerEdges.updateFields() 
            
        #add the vertices and edges to the layers
        for i in range(self.graph.vertexCount()):
            newFeature = QgsFeature()
            newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))  
            newFeature.setAttributes([i])
            dpVerticeLayer.addFeature(newFeature)
        
        for i in range(self.graph.edgeCount()):
            newFeature = QgsFeature()
            fromVertex = self.graph.vertex(self.graph.edge(i).fromVertex()).point()
            toVertex = self.graph.vertex(self.graph.edge(i).toVertex()).point()
            newFeature.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))            
            newFeature.setAttributes([i, self.graph.edge(i).fromVertex(), self.graph.edge(i).toVertex(), self.graph.costOfEdgeID(i)])
            dpEdgeLayer.addFeature(newFeature)    
        
        graphLayerVertices.setCrs(self.vLayer.crs())      
        QgsProject.instance().addMapLayer(graphLayerVertices)
        
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
        
        graphLayerEdges.setCrs(self.vLayer.crs())
        QgsProject.instance().addMapLayer(graphLayerEdges)
       
       

    #returns the graph    
    def makeGraph(self):
                               
        self.__createVertices()
        self.__createEdges()
        self.__createEdgeWeights()
        
        if(self.__options["createGraphAsLayers"] == True):
            self.__createLayers()
        
        
        return self.graph
        
        
        
        
        
    
    
        
       
