from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QLabel, QGridLayout

from qgis.gui import QgsMapLayerComboBox
from qgis.core import  *

from .QgsGraphEdgePickerWidget import QgsGraphEdgePickerWidget
from .QgsGraphVertexPickerWidget import QgsGraphVertexPickerWidget
from ...exceptions import FieldRequiredError

from ...network.protocol.build.available_handlers_pb2 import FieldInformation

import sys
from PyQt5.Qt import QRadioButton
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class BenchmarkData():
    """
    Holds information about one benchmark call
    
    --> Maybe use dataclass instead 
    """

    def __init__(self, graph, algorithm):
        # holds field labels (field.get("label")) and values
        self.parameters = {}
        
        self.graphName = graph
        
        self.graph = None
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsPluginLayer) and layer.name() == self.graphName:
                self.graph = layer.getGraph()
        
        self.algorithm = algorithm
  
        # parameters + graph to be returned as data for the server request
        self.parameters["graph"] = self.graph
               
        
    def setParameterField(self, key, value):
        self.parameters[key] = value    
        
        
    def toString(self):
        string = self.graphName + self.algorithm
        
        for paraKey in self.parameters.keys():
            string = string + str(paraKey) + str(self.parameters[paraKey])
            
        return string    