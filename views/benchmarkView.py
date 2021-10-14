from .baseContentView import BaseContentView
from ..controllers.example import ExampleController
from ..helperFunctions import getRasterFileFilter, getVectorFileFilter
from ..controllers.benchmark import BenchmarkController
from .widgets.QgsOgdfBenchmarkWidget import QgsOGDFBenchmarkWidget
from .. import mainPlugin
from ..network import parserManager
from ..network.protocol.build.available_handlers_pb2 import FieldInformation


from qgis.gui import QgsFileWidget
from qgis.core import *

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class BenchmarkView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.benchmarkAnalysisCounter = 1
        addButton = QToolButton()
        addButton.setObjectName("new_benchmark")
        addButton.setText("➕")
        addButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        addButton.setMaximumSize(25, 25)
        addButton.setIcon(QgsApplication.getThemeIcon("symbologyAdd.svg"))
        addButton.clicked.connect(self._newBenchmarkSelection)
        self.dialog.analysis_visualisation.layout().addWidget(addButton, *(0,2))
        
        self._createNewBenchmarkSelections(True)
                       
        # get controller (this calls the addOGDFAlg method)
        self.controller = BenchmarkController(self)  
        
        self.dialog.refresh_all_graphs.clicked.connect(self._updateAllGraphs)
        self.dialog.clear_graph_selection.clicked.connect(self._clearGraphSelection)     
        self.dialog.start_benchmark.clicked.connect(self.controller.runJob)
        self.dialog.add_all_graphs.clicked.connect(self._addAllGraphs)
        
        self.dialog.graph_selection.model().rowsInserted.connect(self._updateOGDFParameters)
        
        self._updateAllGraphs()
        self.dialog.all_graphs.itemDoubleClicked.connect(self._addItemToSelected)
        self.dialog.graph_selection.itemDoubleClicked.connect(self._deleteItem)
        
        # load parameters for every selected ogdf algorithm
        self.ogdfBenchmarkWidget = QgsOGDFBenchmarkWidget(self.dialog)
            
        self.dialog.ogdf_parameters.setLayout(self.ogdfBenchmarkWidget.layout)
        self.dialog.ogdf_algorithms.itemChanged.connect(self._updateOGDFParameters)
        self.dialog.ogdf_algorithms.itemChanged.connect(self._createNewBenchmarkSelections)
        
        self.FIELD_TYPES = [FieldInformation.FieldType.BOOL,
            FieldInformation.FieldType.INT,
            FieldInformation.FieldType.DOUBLE,
            FieldInformation.FieldType.STRING,
            FieldInformation.FieldType.CHOICE,
            FieldInformation.FieldType.EDGE_COSTS,
            FieldInformation.FieldType.VERTEX_COSTS,
            FieldInformation.FieldType.EDGE_ID,
            FieldInformation.FieldType.VERTEX_ID]
    
    
    def _createNewBenchmarkSelections(self, initial = False):
        # delete all widgets
        copy = self.benchmarkAnalysisCounter
        for i in reversed(range(1, copy+1)):
            self._clearOneBenchmarkSelection(i, initial)    
        # create the same amount of updated widgets
        for i in range(1,copy+1):
            self._newBenchmarkSelection()
          
        
    def _newBenchmarkSelection(self):
        self.benchmarkAnalysisCounter+=1
        listWidgetBenchmark = QListWidget()
        listWidgetBenchmark.setMinimumSize(380, 192)
        listWidgetBenchmark.setObjectName("benchmark_selection_" + str(self.benchmarkAnalysisCounter))
        self.dialog.analysis_visualisation.layout().addWidget(listWidgetBenchmark,*(self.benchmarkAnalysisCounter,0))
        
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
        
        # fill widget
        item = QListWidgetItem("--------------------Parameters Selection 1--------------------")
        listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem("Graphs")
        item.setCheckState(Qt.Unchecked)
        listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem("Algorithms")
        item.setCheckState(Qt.Unchecked)
        listWidgetBenchmark.addItem(item)
        
        # add field of selected algorithms        
        alreadyAddedLabels = []
        
        for fields in requests:                   
            for key in fields:
                field = fields[key]
                if field.get("type") not in self.FIELD_TYPES:
                    continue
                if not field.get("label") in alreadyAddedLabels:
                    alreadyAddedLabels.append(field.get("label"))
                    item = QListWidgetItem(field.get("label"))
                    item.setCheckState(Qt.Unchecked)
                    listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem("--------------------Parameters Selection 2--------------------")
        listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem("Graphs")
        item.setCheckState(Qt.Unchecked)
        listWidgetBenchmark.addItem(item)
              
        item = QListWidgetItem("Algorithms")
        item.setCheckState(Qt.Unchecked)
        listWidgetBenchmark.addItem(item)
        
        # add field of selected algorithms
        alreadyAddedLabels = []
        
        for fields in requests:                   
            for key in fields:
                field = fields[key]
                if field.get("type") not in self.FIELD_TYPES:
                    continue
                if not field.get("label") in alreadyAddedLabels:
                    alreadyAddedLabels.append(field.get("label"))
                    item = QListWidgetItem(field.get("label"))
                    item.setCheckState(Qt.Unchecked)
                    listWidgetBenchmark.addItem(item)
          
        item = QListWidgetItem("-------------------------------Analysis--------------------------------")
        listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem()        
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Runtime"))
        
        item = QListWidgetItem()  
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Number of Edges"))
        
        item = QListWidgetItem()     
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Number of Vertices"))
        
        item = QListWidgetItem()     
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Edges Difference"))
        
        item = QListWidgetItem()     
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Vertices Difference"))

        item = QListWidgetItem()     
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Average Degree"))

        item = QListWidgetItem()      
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Sparseness"))
        
        listWidgetVisualisation = QListWidget()
        listWidgetVisualisation.setMinimumSize(380,192)
        listWidgetVisualisation.setObjectName("visualisation_"+ str(self.benchmarkAnalysisCounter))
        self.dialog.analysis_visualisation.layout().addWidget(listWidgetVisualisation,*(self.benchmarkAnalysisCounter,1))
        
        # fill widget
        item = QListWidgetItem("Points without connection")
        item.setCheckState(Qt.Unchecked)
        listWidgetVisualisation.addItem(item)
        item = QListWidgetItem("Points with connection")
        item.setCheckState(Qt.Unchecked)
        listWidgetVisualisation.addItem(item)
        item = QListWidgetItem("Bar chart")
        item.setCheckState(Qt.Unchecked)
        listWidgetVisualisation.addItem(item)
        item = QListWidgetItem("Lines")
        item.setCheckState(Qt.Unchecked)
        listWidgetVisualisation.addItem(item)
        
        removeButton = QToolButton()
        removeButton.setText("➖")
        removeButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        removeButton.setMaximumSize(25, 25)
        removeButton.setIcon(QgsApplication.getThemeIcon("symbologyRemove.svg"))
        removeButton.clicked.connect(lambda: self._clearOneBenchmarkSelection(self.benchmarkAnalysisCounter))
        self.dialog.analysis_visualisation.layout().addWidget(removeButton, *(self.benchmarkAnalysisCounter,2))
   
    def _clearOneBenchmarkSelection(self, row, initial = False):
        self.benchmarkAnalysisCounter-=1
        rangeEnd = 3
        if initial:
            rangeEnd = 2
        for i in reversed(range(rangeEnd)):
            self.dialog.analysis_visualisation.layout().itemAtPosition(row, i).widget().setParent(None)
         
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
    
    def _addAllGraphs(self):
        for i in range(self.dialog.all_graphs.count()):
            self.dialog.graph_selection.addItem(self.dialog.all_graphs.item(i).text())
    
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
        
    def getSelection1(self):
        # returns 2D object
        
        grid = self.dialog.analysis_visualisation.layout()
        selection1 = []
        
        for c in range(1,grid.rowCount()):
            benchmarkSelWidget = grid.itemAtPosition(c,0).widget()
            oneSelection = []
            for i in range(benchmarkSelWidget.count()):
                if "Selection 2" in benchmarkSelWidget.item(i).text():
                    break
                if benchmarkSelWidget.item(i).checkState() == Qt.Checked:
                    oneSelection.append(benchmarkSelWidget.item(i).text()) 
            selection1.append(oneSelection)
        
        return selection1
        
    def getSelection2(self):
        grid = self.dialog.analysis_visualisation.layout()
        selection2 = []
        
        for c in range(1,grid.rowCount()):
            benchmarkSelWidget = grid.itemAtPosition(c,0).widget()
            oneSelection = []
            sectionFound = False
            for i in range(benchmarkSelWidget.count()):
                if "Analysis" in benchmarkSelWidget.item(i).text():
                    break
                if "Selection 2" in benchmarkSelWidget.item(i).text():
                    sectionFound = True
                if benchmarkSelWidget.item(i).checkState() == Qt.Checked and sectionFound:
                    oneSelection.append(benchmarkSelWidget.item(i).text()) 
            selection2.append(oneSelection)
        
        return selection2
    
    def getAnalysis(self):
        grid = self.dialog.analysis_visualisation.layout()
        analysis = []
        
        for c in range(1,grid.rowCount()):
            benchmarkSelWidget = grid.itemAtPosition(c,0).widget()
            sectionFound = False
            for i in range(benchmarkSelWidget.count()):
                if "Analysis" in benchmarkSelWidget.item(i).text():
                    sectionFound = True
                    continue
                if sectionFound:    
                    radioB = benchmarkSelWidget.itemWidget(benchmarkSelWidget.item(i))   
                    if radioB.isChecked():
                        analysis.append(radioB.text())      
        return analysis
    
    def getVisualisation(self): 
        grid = self.dialog.analysis_visualisation.layout()  
        visualisation = []
        
        for c in range(1,grid.rowCount()):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            oneSelection = []
            for i in range(visualisationSelWidget.count()):
                if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                    oneSelection.append(visualisationSelWidget.item(i).text())
            visualisation.append(oneSelection)
            
        return visualisation
        
                
            
        
        
        
        
       
        
        
               