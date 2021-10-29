from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QLabel, QGridLayout

from qgis.gui import QgsMapLayerComboBox
from qgis.core import  *

from .QgsGraphEdgePickerWidget import QgsGraphEdgePickerWidget
from ...models.benchmark.BenchmarkData import BenchmarkData
from .QgsGraphVertexPickerWidget import QgsGraphVertexPickerWidget
from ...exceptions import FieldRequiredError

from ...network.protocol.build.available_handlers_pb2 import FieldInformation

import sys
from PyQt5.Qt import QRadioButton
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import itertools

class QgsOGDFBenchmarkWidget(QWidget):
    """
    Dynamically creates and shows input widgets created from parameter list
    """
    def __init__(self, dialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
       
        # list of BenchmarkData objects, which hold all the information about one request
        self.benchmarkDataObjects = []
       
        self.benchmarkObjectsHash = {}
       
        # contains functions to create a field widget based on field type
        self.FIELD_WIDGETS = {
            FieldInformation.FieldType.BOOL: self._createBoolWidget,
            FieldInformation.FieldType.INT: self._createIntWidget,
            FieldInformation.FieldType.DOUBLE: self._createDoubleWidget,
            FieldInformation.FieldType.STRING: self._createStringWidget,
            FieldInformation.FieldType.CHOICE: self._createChoiceWidget,
            FieldInformation.FieldType.EDGE_COSTS: self._createEdgeCostsWidget,
            FieldInformation.FieldType.VERTEX_COSTS: self._createVertexCostWidget,
            FieldInformation.FieldType.EDGE_ID: self._createEdgeWidget,
            FieldInformation.FieldType.VERTEX_ID: self._createVertexWidget,
        }
        
        self.fieldsList = [] 
             
        self.layout = QGridLayout()

        self.setLayout(self.layout)
        
        self._createParameterWidgets()
    
    def setParameterFields(self, fields):
        self.fieldsList = fields
        self._createParameterWidgets()        
     
    def clearWidgets(self):
        """
        Removes all widgets from layout
        :return:
        """        
        for i in reversed(range(self.layout.count())):
            self.layout.takeAt(i).widget().setParent(None)
                                 
    
    def getBenchmarkDataObjects(self):
        """
        Returns one dictionary when called and loads a new one to be requested next
        
        :return: dictionary with field key and corresponding value
        """
        self._createBenchmarkDataObjects()
        
        return list(self.benchmarkObjectsHash.values())
   
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
   
    def _createBenchmarkDataObjects(self):
        """
        Read all data from the widgets and create all BenchmarkData objects        
        """
              
        # IDEA: just one loop, go throw every field and store for every field the value ranges in an array
        # store array in dict together with field
        # create all permutations of those arrays (normal fields with one value have array of size 1)
        # use itertools.product(*allArrays)
        
        self.benchmarkObjectsHash = {}
        
        diffForGraphs = [FieldInformation.FieldType.VERTEX_ID, FieldInformation.FieldType.EDGE_ID, FieldInformation.FieldType.VERTEX_COSTS, FieldInformation.FieldType.EDGE_COSTS]
        
        rangesForEachAlg = []
        allSelectedAlgs = self.getSelectedAlgs()
        for i in range(len(allSelectedAlgs)):
            rangesForEachAlg.append([])
                     
        listOfGraphs = []   
        rangeFields = [FieldInformation.FieldType.INT, FieldInformation.FieldType.DOUBLE, FieldInformation.FieldType.EDGE_ID, FieldInformation.FieldType.VERTEX_ID]       
        for i in range(self.dialog.graph_selection.count()):
            listOfGraphs.append(self.dialog.graph_selection.item(i))

        alreadyDoneFields = []
        for i in range(len(self.fieldsList)):
            alreadyDoneFields.append([])
        
        # go through graphs
        for graphName in listOfGraphs:  
            algCount = 0
            # go through all selected algorithms
            for fields in self.fieldsList:
                ranges = {}   
                # go through all fields
                for key in fields:
                    field = fields[key]   
                    if field.get("label") in alreadyDoneFields[algCount] and not field.get("type") in diffForGraphs:
                        continue        
                    alreadyDoneFields[algCount].append(field.get("label"))        
                    if field.get("type") in rangeFields:
                        start = 1.0
                        end = 1.0
                        incr = 1.0                     
                        # find widgets for this field
                        for i in range(self.dialog.ogdf_parameters.layout().count()):                           
                            widget = self.dialog.ogdf_parameters.layout().itemAt(i).widget()
                            if field.get("label") in widget.objectName():                                
                                if (widget.objectName() == (field.get("label") + graphName.text() + "From")) or (widget.objectName() == (field.get("label") + "From")):
                                    start = widget.value()
                                elif (widget.objectName() == (field.get("label") + graphName.text() + "To")) or (widget.objectName() == (field.get("label") + "To")):
                                    end = widget.value()
                                elif (widget.objectName() == (field.get("label") + graphName.text() + "Increment")) or (widget.objectName() == (field.get("label") +  "Increment")):
                                    incr = widget.value()
                       
                        rangeValues = []
                        current = start
                        while current <= end:                          
                            rangeValues.append(current)
                            current += incr
                            
                        ranges[field.get("label")] = rangeValues
                        
                    elif field.get("type") == FieldInformation.FieldType.BOOL:
                        # find widget for this field
                        for i in range(self.dialog.ogdf_parameters.layout().count()):
                            widget = self.dialog.ogdf_parameters.layout().itemAt(i).widget()
                            if widget.objectName() == field.get("label"):
                                # get value
                                if str(widget.currentText()) == "Both":
                                    rangeValues = ["True", "False"]
                                    ranges[field.get("label")] = rangeValues  
                                else:
                                    ranges[field.get("label")] = [str(widget.currentText())]   
                                    
                        
                    elif field.get("type") == FieldInformation.FieldType.EDGE_COSTS:    
                        for i in range(self.dialog.ogdf_parameters.layout().count()):
                            widget = self.dialog.ogdf_parameters.layout().itemAt(i).widget()
                            if widget.objectName() == (field.get("label") + graphName.text()):
                                layer = None
                                for currLayer in QgsProject.instance().mapLayers().values():
                                    if isinstance(currLayer, QgsPluginLayer) and currLayer.name() == graphName.text():
                                        layer = currLayer
                                # get value
                                if str(widget.currentText()) == "All":                                  
                                    if layer.getGraph().distanceStrategy == "Advanced":
                                        rangeValues = []
                                        for c in range(len(layer.getGraph().edgeWeights)):
                                            rangeValues.append(c)
                                            #rangeValues.append(("Advanced",c))                                                                                    
                                    else:    
                                        rangeValues = [("Euclidean",0), ("Manhattan",0), ("Geodesic",0), ("Ellipsoidal",0)]
                                    ranges[field.get("label")] = rangeValues
                                else:
                                    if layer.getGraph().distanceStrategy == "Advanced":
                                        ranges[field.get("label")] = [0] 
                                        #ranges[field.get("label")] = [("Advanced", int(widget.currentText().split(":")[1]))] 
                                    else:                                          
                                        ranges[field.get("label")] = [(str(widget.currentText()),0)]    
               
                    # normal field
                    else:    
                        for i in range(self.dialog.ogdf_parameters.layout().count()):
                            widget = self.dialog.ogdf_parameters.layout().itemAt(i).widget()
                            if widget.objectName() == field.get("label") and widget.objectName() != "":                              
                                ranges[field.get("label")] = [str(widget.currentText())]               
                
                # holds labels of fields and all the values (list of list of dictionaries, first index for the algorithm, second for the graph) 
                rangesForEachAlg[algCount].append(ranges)   
                algCount+=1 
                        
        toDeleteFieldIndices = [] 
        # create permutations
        for i in range(len(rangesForEachAlg)):
            allLists = []
            # go through each parameter dictionary
            for j in range(len(rangesForEachAlg[i])):

                for v in rangesForEachAlg[i][j].values():
                    allLists.append(v)
             
            permutationRes = list(itertools.product(*allLists))                         
            # find algorithm name
            algName = allSelectedAlgs[i]
            # permutation holds one parameter setting
            for permutation in permutationRes:                                    
                alreadyDoneMatches = {}
                toDeleteFieldIndices = [] 
                for g in range(len(listOfGraphs)):
                    counter = 0                             
                    for index in toDeleteFieldIndices:                     
                        permutation = permutation[0:index-counter] + permutation[index+1-counter:]        
                        counter+=1
                    toDeleteFieldIndices = []  
                    graph = listOfGraphs[g].text()
                    bo = BenchmarkData(graph, algName)
                                     
                    # go through fields for algorithm and read values from permutation                 
                    fieldLabels = list(rangesForEachAlg[i][g].keys())

                    for key in self.fieldsList[i]:                      
                        field = self.fieldsList[i][key]
                        if field.get("label") in alreadyDoneMatches.keys():
                            bo.setParameterField(key, permutation[alreadyDoneMatches[field.get("label")]])
                            bo.setParameterKeyHash(field.get("label"), key)
                            if field.get("type") in diffForGraphs:
                                toDeleteFieldIndices.append(alreadyDoneMatches[field.get("label")])
                        else:
                            # get position in permutation tuple            
                            for rangesKeyIndex in range(len(fieldLabels)):
                                
                                if field.get("label") == fieldLabels[rangesKeyIndex]:
                                    alreadyDoneMatches[field.get("label")] = rangesKeyIndex                     
                                    bo.setParameterField(key, permutation[rangesKeyIndex])
                                    bo.setParameterKeyHash(field.get("label"), key)
                                    
                                    if field.get("type") in diffForGraphs:
                                        toDeleteFieldIndices.append(rangesKeyIndex)

                    if not bo.toString() in self.benchmarkObjectsHash:                   
                        self.benchmarkObjectsHash[bo.toString()] = bo                   
                             
            
    def _createParameterWidgets(self):
        """
        Creates and shows all parameter fields as widgets
        :return:
        """
        posCounter = 0
        diffForGraphs = [FieldInformation.FieldType.VERTEX_ID, FieldInformation.FieldType.EDGE_ID, FieldInformation.FieldType.VERTEX_COSTS, FieldInformation.FieldType.EDGE_COSTS]
        allSelectedAlgs = self.getSelectedAlgs()         
        self.clearWidgets()
        # loop over algorithms
        algCounter = 0
        for fields in self.fieldsList:
            
            for key in fields:
                field = fields[key]
    
                # look if widget for this field already exists from other algorithm
                found = False
                for i in range(self.layout.count()):
                    widget = self.layout.itemAt(i).widget()
                    if field.get("label") in widget.objectName():
                        found = True
                        break
                if found:
                    continue        
    
                # skip field if widget of corresponding field type is not implemented (possibly intended)
                if field.get("type") not in self.FIELD_WIDGETS:
                    continue
    
                widgetFunction = self.FIELD_WIDGETS.get(field.get("type"), None)       
                listOfGraphs = []      
                for i in range(self.dialog.graph_selection.count()):
                    listOfGraphs.append(self.dialog.graph_selection.item(i))
                
                if field.get("type") in diffForGraphs:
                    
                    for graphName in listOfGraphs:
                        labelWidget = QLabel(field.get("label") + ": " + (graphName.text().split("GraphLayer")[0]))
                        
                        for layer in QgsProject.instance().mapLayers().values():
                            if isinstance(layer, QgsPluginLayer) and layer.name() == graphName.text():
                        
                                inputWidgets = widgetFunction(field, layer.getGraph(), layer.name())                      
                                
                                if labelWidget is not None:
                                    self.layout.addWidget(labelWidget, *(posCounter, 0))
                                    
                                if isinstance(inputWidgets, list):              
                                    for i in range(0,len(inputWidgets),2):  
                                        if i == 0:
                                            posCounter+=1                              
                                        # add widgets to layout
                                        if inputWidgets[i] is not None:
                                            self.layout.addWidget(inputWidgets[i], *(posCounter, 1))
                                            self.layout.addWidget(inputWidgets[i+1], *(posCounter, 2))   
                                        posCounter+=1                                      
                                        
                                else:
                                    self.layout.addWidget(inputWidgets, *(posCounter, 1))
                                    posCounter+=1
        
                else:
                    
                    labelWidget = QLabel(field.get("label"))
                    inputWidgets = widgetFunction(field)                      
                    
                    if labelWidget is not None:
                        self.layout.addWidget(labelWidget, *(posCounter, 0))
                        
                    if isinstance(inputWidgets, list):              
                        for i in range(0,len(inputWidgets),2):  
                            if i == 0:
                                posCounter+=1                              
                            # add widgets to layout
                            if inputWidgets[i] is not None:
                                self.layout.addWidget(inputWidgets[i], *(posCounter, 1))
                                self.layout.addWidget(inputWidgets[i+1], *(posCounter, 2))   
                            posCounter+=1                                      
                            
                    else:
                        self.layout.addWidget(inputWidgets, *(posCounter, 1))
                        posCounter+=1
        # create execution widget
        for algName in allSelectedAlgs:
            inputWidgets = self._createExecutionWidget(algName)
            self.layout.addWidget(inputWidgets[0], *(posCounter,0))
            self.layout.addWidget(inputWidgets[1], *(posCounter,1))
            posCounter+=1
        
             
    def _createBoolWidget(self, field):
        comboBoxWidget = QComboBox()
        comboBoxWidget.setObjectName(field.get("label"))
        comboBoxWidget.addItem("True")
        comboBoxWidget.addItem("False")
        comboBoxWidget.addItem("Both")
        
        return comboBoxWidget

    def _createIntWidget(self, field):
        spinBoxesList = []
        for i in range(3):
            if i == 0:
                labelWidget = QLabel("From")
            elif i == 1:
                labelWidget = QLabel("To")
            elif i == 2:    
                labelWidget = QLabel("Increment")            
            
            spinBoxesList.append(labelWidget)
        
            spinBoxWidget = QSpinBox()
            spinBoxWidget.setObjectName(field.get("label") + labelWidget.text())
            # highest minimum and maximum
            if labelWidget.text() == "Increment":
                spinBoxWidget.setRange(1, 2147483647)
            else:
                spinBoxWidget.setRange(-2147483648, 2147483647)
                
            spinBoxesList.append(spinBoxWidget)
        
        return spinBoxesList

    def _createDoubleWidget(self, field):
        spinBoxesList = []
        for i in range(3): 
            if i == 0:
                labelWidget = QLabel("From")
            elif i == 1:
                labelWidget = QLabel("To")
            elif i == 2:    
                labelWidget = QLabel("Increment")            
            spinBoxesList.append(labelWidget)
                
            spinBoxWidget = QDoubleSpinBox()
            spinBoxWidget.setObjectName(field.get("label") + labelWidget.text())
            
            # highest minimum and maximum
            if labelWidget.text() == "Increment":
                spinBoxWidget.setRange(1.0, sys.float_info.max)
            else:          
                spinBoxWidget.setRange(-sys.float_info.min, sys.float_info.max)
            
            spinBoxWidget.setDecimals(6)
            spinBoxWidget.setValue(1.0)  # default value
            if field.get("default") and isinstance(field.get("default"), float):
                spinBoxWidget.setValue(field.get("default"))
            spinBoxesList.append(spinBoxWidget)                       
        
        return spinBoxesList

    def _createStringWidget(self, field):
        lineEditWidget = QLineEdit(str(field.get("default", "")))
        lineEditWidget.setObjectName(field.get("label"))
        
        return lineEditWidget

    def _createChoiceWidget(self, field):
        comboBoxWidget = QComboBox()
        comboBoxWidget.setObjectName(field.get("label"))
        choices = field.get("choices")
        for choice in choices:
            choiceData = choices[choice]
            comboBoxWidget.addItem(choice, choiceData)
        
        comboBoxWidget.addItem("all")
        # select default item if exist
        comboBoxWidget.setCurrentIndex(comboBoxWidget.findText(str(field.get("default"))))
        
        return comboBoxWidget    
        
    def _createEdgeCostsWidget(self, field, graph, graphName):
        widgetList = []
        
        # create label
        labelWidget = QLabel()
        widgetList.append(labelWidget)
        comboBoxWidget = QComboBox()
        comboBoxWidget.setObjectName(field.get("label") + graphName)   
        if graph.distanceStrategy != "Advanced":
            comboBoxWidget.addItem("Euclidean")
            comboBoxWidget.addItem("Manhattan")
            comboBoxWidget.addItem("Geodesic")
            comboBoxWidget.addItem("Ellipsoidal")
            comboBoxWidget.addItem("All")                       
        else:
            # get all advanced cost functions
            for i in range(len(graph.edgeWeights)):
                 comboBoxWidget.addItem("Cost Function: " + str(i))
            comboBoxWidget.addItem("All")                         
            
            
        widgetList.append(comboBoxWidget)         
        
        return widgetList

    # possibly remove because we do not use vertex weights
    def _createVertexCostWidget(self, field, graph, graphName): 
        return QComboBox()
    
    def _createEdgeWidget(self, field, graph):
        widgetList = []   
        
        for i in range(3):
            if i == 0:
                labelWidget = QLabel("From")
            elif i == 1:
                labelWidget = QLabel("To")
            elif i == 2:    
                labelWidget = QLabel("Increment")
                
            widgetList.append(labelWidget)
            spinBoxWidget = QSpinBox()
            spinBoxWidget.setObjectName(field.get("label") + graphName + labelWidget.text())
            
            if labelWidget.text() == "Increment":
                spinBoxWidget.setRange(1, 2147483647)
            else:           
                spinBoxWidget.setRange(0, graph.edgeCount())
            widgetList.append(spinBoxWidget)
                      
        return widgetList   

    def _createVertexWidget(self, field, graph, graphName):
        widgetList = []   
        
        for i in range(3):
            if i == 0:
                labelWidget = QLabel("From")
            elif i == 1:
                labelWidget = QLabel("To")
            elif i == 2:    
                labelWidget = QLabel("Increment")
        
            widgetList.append(labelWidget)
            spinBoxWidget = QSpinBox()
            spinBoxWidget.setObjectName(field.get("label") + graphName + labelWidget.text())
            if labelWidget.text() == "Increment":
                spinBoxWidget.setRange(1, 2147483647)
            else:           
                spinBoxWidget.setRange(0, graph.vertexCount())
            widgetList.append(spinBoxWidget)
                      
        return widgetList   
    
    def _createExecutionWidget(self, algName):
        widgetList = []
        labelWidget = QLabel("Executions: " + algName)
        widgetList.append(labelWidget)
        spinBoxWidget = QSpinBox()
        spinBoxWidget.setObjectName("Executions"+ "_" + algName)
        spinBoxWidget.setRange(1, 2147483647)
        widgetList.append(spinBoxWidget)
        
        return widgetList
        
        
    
    
            