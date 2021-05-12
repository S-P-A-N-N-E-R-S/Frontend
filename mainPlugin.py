from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import QVariant

from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

from . import resources

import time

class ProtoPlugin:

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction(QIcon(":/plugins/ProtoPlugin/icon.png"), "Proto Plugin", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.action.setWhatsThis("Select VectorLayer and click green Button")
        self.action.setStatusTip("Select VectorLayer and click green Button")

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Proto Plugin", self.action)


    def unload(self):
        self.iface.removePluginMenu("&Proto Plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        print("ProtoPlugin: Run Called!")
        self.createGraph()
    
       
    
    def createGraph(self):
        layer = self.iface.activeLayer()
        graph = QgsGraph() 
        vertexID = 0
        edgeID = 0 
        
        # create new VectorLayer to show graph
        # TODO: add function to create VectorLayer (used for points and lines) to minimize double code
        newVectorLayerVertices = QgsVectorLayer("Point", "GraphVertices", "memory")
        newDataProviderVertices = newVectorLayerVertices.dataProvider()

        # add Fields to VectorLayer
        newDataProviderVertices.addAttributes([QgsField("ID", QVariant.Int)])
        newVectorLayerVertices.updateFields()
        
        # create new VectorLayer to show graph
        # TODO: add function to create VectorLayer (used for points and lines) to minimize double code
        newVectorLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")
        newDataProviderEdges = newVectorLayerEdges.dataProvider()

        # add Fields to VectorLayer
        newDataProviderEdges.addAttributes([QgsField("ID", QVariant.Int), QgsField("fromVertex",QVariant.Int), QgsField("toVertex",QVariant.Int),QgsField("weight", QVariant.String)])
        newVectorLayerEdges.updateFields()
        
           
        #check if vector layer   
        if layer.type() == QgsMapLayer.VectorLayer:
            
            #get the geometry type      
            geometryTypeOfLayer = layer.geometryType()
        
            if geometryTypeOfLayer == QgsWkbTypes.PointGeometry:
                vertexID = 0
                
                for feat in layer.getFeatures():
                    geom = feat.geometry()
                    vertexID+=1
                    graph.addVertex(geom.asPoint())
                    newFeature = QgsFeature()                                         
                    newFeature.setGeometry(QgsGeometry.fromPointXY(geom.asPoint()))                   
                    newFeature.setAttributes([vertexID])               
                    newDataProviderVertices.addFeature(newFeature)                                    
                QgsProject.instance().addMapLayer(newVectorLayerVertices)                          
                
            elif geometryTypeOfLayer == QgsWkbTypes.LineGeometry:
                edgeID = 0
                vertexID = 0
      
                for feat in layer.getFeatures():
                    geom = feat.geometry()
                    startVertex = QgsPointXY
                    endVertex = QgsPointXY
                    #vertices
                    if QgsWkbTypes.isSingleType(geom.wkbType()):
                        
                        vertices = geom.asPolyline()
                        startVertex = vertices[0]
                        endVertex = vertices[-1]
                        
                        graph.addVertex(startVertex)
                        graph.addVertex(endVertex)
                        
                        newFeature = QgsFeature()                     
                        newFeature.setGeometry(QgsGeometry.fromPointXY(startVertex))                                           
                        newFeature.setAttributes([vertexID])
                        vertexID+=1               
                        newDataProviderVertices.addFeature(newFeature)                     
                        
                        newFeature = QgsFeature(newVectorLayerVertices.fields())  
                        newFeature.setAttributes([vertexID])                    
                        newFeature.setGeometry(QgsGeometry.fromPointXY(endVertex))                                                                  
                        vertexID+=1               
                        newDataProviderVertices.addFeature(newFeature) 
                                                                                        
                    else:
                        
                        vertices = geom.asMultiPolyline()
                        startVertex = vertices[0][0]
                        endVertex = vertices[-1][-1]
                                                
                        graph.addVertex(startVertex)
                        graph.addVertex(endVertex)
                                              
                        newFeature = QgsFeature()                     
                        newFeature.setGeometry(QgsGeometry.fromPointXY(startVertex))                                           
                        newFeature.setAttributes([vertexID])
                        vertexID+=1              
                        newDataProviderVertices.addFeature(newFeature)                     
                        
                        newFeature = QgsFeature(newVectorLayerVertices.fields())   
                        newFeature.setAttributes([vertexID])                   
                        newFeature.setGeometry(QgsGeometry.fromPointXY(endVertex))                                                                 
                        vertexID+=1                
                        newDataProviderVertices.addFeature(newFeature) 
                                            
                        
                        
                    #edges 
                    edgeID+=1
                    strategy = QgsNetworkSpeedStrategy(1,50,1)
                    graph.addEdge(vertexID-2, vertexID-1,[strategy])             
                    newFeature = QgsFeature()
                    newFeature.setGeometry(QgsGeometry.fromPolyline([QgsPoint(startVertex), QgsPoint(endVertex)]))
                    newFeature.setAttributes([edgeID, vertexID-2, vertexID-1, 1])
                    newDataProviderEdges.addFeature(newFeature)
                   
                    QgsProject.instance().addMapLayer(newVectorLayerVertices)
                    QgsProject.instance().addMapLayer(newVectorLayerEdges)  
      
            elif geometryTypeOfLayer == QgsWkbTypes.PolygonGeometry:
                
                for feat in layer.getFeatures():
                    print("TODO")
   
                      
        
                 
