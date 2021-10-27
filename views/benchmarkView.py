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
        self.dialog.abort_benchmark.clicked.connect(self._setAbort)
        
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
        
        ogdfAlgs = self.getSelectedAlgs()
        requests = []             
         
        # get field information for all selected algorithms        
        for alg in ogdfAlgs:
            request = parserManager.getRequestParser(alg)         
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
        
        item = QListWidgetItem("Graph Edges")
        item.setCheckState(Qt.Unchecked)
        listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem("Graph Vertices")
        item.setCheckState(Qt.Unchecked)
        listWidgetBenchmark.addItem(item)
        
        item = QListWidgetItem("Graph Densities")
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
        
        item = QListWidgetItem()      
        listWidgetBenchmark.addItem(item)
        listWidgetBenchmark.setItemWidget(item, QRadioButton("Lightness"))
        
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
        item = QListWidgetItem("Box plot")
        item.setCheckState(Qt.Unchecked)
        listWidgetVisualisation.addItem(item)
        
        item = QListWidgetItem("------------------------------Additional Options------------------------------")
        listWidgetVisualisation.addItem(item)
        
        item = QListWidgetItem("Logarithmic y-axis")
        item.setCheckState(Qt.Unchecked)
        listWidgetVisualisation.addItem(item)
        item = QListWidgetItem("Create legend")
        item.setCheckState(Qt.Checked)
        listWidgetVisualisation.addItem(item)
        item = QListWidgetItem("Tight layout")
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
            ogdfAlgs = self.getSelectedAlgs()
            requests = []
                  
            # get field information for all selected algorithms        
            for alg in ogdfAlgs:
                request = parserManager.getRequestParser(alg)         
                if request:          
                    requests.append(request.getFieldInfo())
            
            # set the parameter fields so the widgets can be created
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
        item = QTreeWidgetItem(self.dialog.ogdf_algorithms)
        item.setText(0, analysis)
        item.setCheckState(0,Qt.Unchecked)
        self.dialog.ogdf_algorithms.insertTopLevelItem(0,item)
     
    def addOGDFAlgs(self, analysisList):
        groups = {}
        for analysis in analysisList:
            try:
                groups[analysis.split("/")[0]]
            except:
                groups[analysis.split("/")[0]] = []
            
            groups[analysis.split("/")[0]].append(analysis.split("/")[1])
        
        items = []
        for key, values in groups.items():
            item = QTreeWidgetItem([key])
            for value in values:
                child = QTreeWidgetItem([value])
                child.setCheckState(0, Qt.Unchecked)
                item.addChild(child)
            items.append(item)    
        
        self.dialog.ogdf_algorithms.insertTopLevelItems(0, items)
     
    def getSelectedAlgs(self):
        checked = []
        root = self.dialog.ogdf_algorithms.invisibleRootItem()
        childCount = root.childCount()
        
        for i in range(childCount):
            child = root.child(i)
            numChildren = child.childCount()
            
            for n in range(numChildren):
                child2 = child.child(n)
                if child2.checkState(0) == Qt.Checked:
                    checked.append(child.text(0) + "/" + child2.text(0))
                   
        return checked     
                         
    def getSelection1(self):
        """
        Method to get the first selections of all the benchmark_visualisation QtListWidgets.
        These selections are used in the first partitioning step.
        
        :returns 2D list   
        """ 
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
        """
        Method to get the first selections of all the benchmark_visualisation QtListWidgets.
        These selections are used in the second partitioning step.
        
        :returns 2D list   
        """
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
        """
        Method to get the analysis of all the benchmark_visualisation QtListWidgets.
        The selection is used to perform a specified analysis like number of edges or sparseness.
                
        :returns list
        """
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
        """
        Method to get the selected visualisations of all the benchmark requests. 
        
        :returns 2D list
        """
        grid = self.dialog.analysis_visualisation.layout()  
        visualisation = []
        
        for c in range(1,grid.rowCount()):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            oneSelection = []
            for i in range(visualisationSelWidget.count()):
                if "Additional Options" in visualisationSelWidget.item(i).text():
                    break                
                if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                    oneSelection.append(visualisationSelWidget.item(i).text())
            visualisation.append(oneSelection)
            
        return visualisation
        
    
    def getExecutions(self, algName):
        for i in range(self.dialog.ogdf_parameters.layout().count()):
            widget = self.dialog.ogdf_parameters.layout().itemAt(i).widget()
            if widget.objectName() == "Executions_" + algName:
                return widget.value()
        
        return -1
    
    def getCreateLegendSelection(self):
        legendSelections = []
        grid = self.dialog.analysis_visualisation.layout()
        for c in range(1,grid.rowCount()):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            for i in range(visualisationSelWidget.count()):
                if "Create legend" == visualisationSelWidget.item(i).text():
                    if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                        legendSelections.append(True)
                    else:
                        legendSelections.append(False)
           
                    
                    
        return legendSelections   
                   
    def getLogAxisSelection(self):
        logSelections = []
        grid = self.dialog.analysis_visualisation.layout()  
        for c in range(1,grid.rowCount()):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            for i in range(visualisationSelWidget.count()):
                if "Logarithmic y-axis" == visualisationSelWidget.item(i).text():
                    if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                        logSelections.append(True)
                    else:
                        logSelections.append(False)
                    
        return logSelections    
        
    def getTightLayoutSelection(self):
        tightSelections = []    
        grid = self.dialog.analysis_visualisation.layout()    
        for c in range(1,grid.rowCount()):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            for i in range(visualisationSelWidget.count()):
                if "Tight layout" == visualisationSelWidget.item(i).text():
                    if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                        tightSelections.append(True)
                    else:
                        tightSelections.append(False)
                    
        return tightSelections      
       
    def getNumberOfRequestedBenchmarks(self):
        return self.benchmarkAnalysisCounter
    
    def getTextFilePath(self):
        return self.dialog.txt_path.filePath()
    
    def getTxtCreationSelection(self):
        if self.dialog.create_as_txt.checkState() == Qt.Checked:
            return True
        else:
            return False
     
    def getNumberOfSelectedGraphs(self):
        return self.dialog.graph_selection.count()
     
    def _setAbort(self):
        if self.controller.running == True:
            self.controller.abort = True
               