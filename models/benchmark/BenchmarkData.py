from qgis.core import  *

class BenchmarkData():
    """
    Holds information about one benchmark call
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
        
        self.serverResponse = None
        self.responseGraph = None
  
        # parameters + graph to be returned as data for the server request
        self.parameters["graph"] = self.graph
        
        self.parameterKeyHash = {}
               
        
    def setParameterField(self, key, value):
        self.parameters[key] = value    
     
    def setParameterKeyHash(self, label, key):
        self.parameterKeyHash[label] = key 
    
    def getParameterKey(self, label):
        return self.parameterKeyHash[label]
     
    def setServerResponse(self, response):
        self.serverResponse = response

    def setResponseGraph(self, graph):
        self.responseGraph = graph
  
    def getNumberOfEdgesRequest(self):
        return self.graph.edgeCount()
        
    def getNumberOfEdgesResponse(self): 
        return self.responseGraph.edgeCount()
    
    def getNumberOfVerticesRequest(self):
        return self.graph.vertexCount()
    
    def getNumberOfVerticesResponse(self):
        return self.responseGraph.vertexCount()       
  
    def getServerResponse(self):
        return self.serverResponse
    
    def getParameters(self):
        return self.parameters
  
    def getAlgorithm(self):
        return self.algorithm
  
    def getGraphName(self):
        return self.graphName
    
    def getGraph(self):
        return self.graph
  
    def getResponseGraph(self):
        return self.responseGraph
  
    def toString(self):
        string = self.graphName + self.algorithm
        
        for paraKey in self.parameters.keys():
            string = string + str(paraKey) + str(self.parameters[paraKey])
            
        return string    