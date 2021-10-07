from .baseContentView import BaseContentView
from ..controllers.example import ExampleController
from ..helperFunctions import getRasterFileFilter, getVectorFileFilter
from ..controllers.benchmark import BenchmarkController
from .widgets.QgsOgdfBenchmarkWidget import QgsOGDFBenchmarkWidget
from .. import mainPlugin
from ..network import parserManager

from qgis.gui import QgsFileWidget
from qgis.core import *

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class BenchmarkView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        
        # get controller (this calls the addOGDFAlg method)
        self.controller = BenchmarkController(self)  
        
        self.dialog.refresh_all_graphs.clicked.connect(self._updateAllGraphs)
        self.dialog.clear_graph_selection.clicked.connect(self._clearGraphSelection)     
        self.dialog.start_benchmark.clicked.connect(self.controller.runJob)
        self.dialog.graph_selection.model().rowsInserted.connect(self._updateOGDFParameters)
        
        self._updateAllGraphs()
        self.dialog.all_graphs.itemDoubleClicked.connect(self._addItemToSelected)
        self.dialog.graph_selection.itemDoubleClicked.connect(self._deleteItem)
        
        # load parameters for every selected ogdf algorithm
        self.ogdfBenchmarkWidget = QgsOGDFBenchmarkWidget(self.dialog)
            
        self.dialog.ogdf_parameters.setLayout(self.ogdfBenchmarkWidget.layout)
        self.dialog.ogdf_algorithms.itemChanged.connect(self._updateOGDFParameters)
            
   
    def _updateOGDFParameters(self):
        if self.dialog.graph_selection.count() > 0:
            ogdfAlgs = []
            requests = []
            for i in range(self.dialog.ogdf_algorithms.count()):
                if self.dialog.ogdf_algorithms.item(i).checkState() == Qt.Checked:
                    ogdfAlgs.append(self.dialog.ogdf_algorithms.item(i))         
             
            # get field information for all selected algorithms        
            for alg in ogdfAlgs:
                request = parserManager.getRequestParser(alg.text())         
                if request:          
                    requests.append(request.getFieldInfo())
            
            self.ogdfBenchmarkWidget.setParameterFields(requests)
            
        else:
            self.ogdfBenchmarkWidget.clearWidgets() 
        
   
    def _getOGDFParameters(self):
        self.ogdfBenchmarkWidget.getBenchmarkDataObjects()

    def _updateAllGraphs(self): 
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsPluginLayer) and not self.dialog.all_graphs.findItems(layer.name(), Qt.MatchExactly):
                self.dialog.all_graphs.addItem(layer.name())
    
    def _addItemToSelected(self, item):
        self.dialog.graph_selection.addItem(item.text())
        
    def _deleteItem(self, item):
        self.dialog.graph_selection.takeItem(self.dialog.graph_selection.row(item))
        self._updateOGDFParameters()
                
    def _clearGraphSelection(self): 
        self.dialog.graph_selection.clear()    
        self._updateOGDFParameters()
           
    def addOGDFAlg(self, analysis):
        item = QListWidgetItem(analysis)
        item.setCheckState(Qt.Unchecked)
        self.dialog.ogdf_algorithms.addItem(item)
        
        
       
        
        
               