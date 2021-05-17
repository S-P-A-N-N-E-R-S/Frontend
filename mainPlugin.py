from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import QVariant

from .GraphBuilder import GraphBuilder
from qgis.core import *
from qgis.gui import *
from qgis.analysis import *
from .PGGraph import PGGraph
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
        
        
        #testGraph = QgsGraph()
        
    
        #testGraph.addVertex(QgsPointXY(123,333))
        #testGraph.addVertex(QgsPointXY(100,200))
        #testGraph.addEdge(0, 1,[])
        
        #print(testGraph.edge(0).cost())
        
        
        
        
        
    
       
    
    def createGraph(self):
        
        #change later if the gui is done
        selectedLayer = self.iface.activeLayer()
        ga = GraphBuilder()
        
        ga.setVectorLayer(selectedLayer)
        
        
        graph = ga.makeGraph()
        
         
   
                      
        
                 
