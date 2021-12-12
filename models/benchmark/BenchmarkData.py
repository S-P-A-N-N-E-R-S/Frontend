from statistics import mean

from qgis.core import QgsProject, QgsPluginLayer


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
        self.serverResponses = []
        self.responseGraphs = []
        # set the graph parameter for the server request
        self.parameters["graph"] = self.graph
        # dict holds field labels as keys and the the field keys as keys
        self.parameterKeyHash = {}
        self.runtimes = []

    def setRuntime(self, runtime):
        self.runtimes.append(runtime)

    def setParameterField(self, key, value):
        self.parameters[key] = value

    def setParameterKeyHash(self, label, key):
        self.parameterKeyHash[label] = key

    def getParameterKey(self, label):
        return self.parameterKeyHash[label]

    def addServerResponse(self, response):
        self.serverResponses.append(response)

    def setResponseGraph(self, graph):
        self.responseGraphs.append(graph)

    def getNumberOfEdgesRequest(self):
        return self.graph.edgeCount()

    def getAvgRuntime(self):
        values = []
        for time in self.runtimes:
            values.append(time/1000000)
        return mean(values)
        
    def getAllRuntimes(self):
        values = []
        for time in self.runtimes:
            values.append(time/1000000)
        return values    

    def getAvgNumberOfEdgesResponse(self):
        values = []
        for i in range(len(self.responseGraphs)):
            values.append(self.responseGraphs[i].edgeCount())
        return mean(values)

    def getAllNumberOfEdgesResponse(self):
        values = []
        for i in range(len(self.responseGraphs)):
            values.append(self.responseGraphs[i].edgeCount())
        return values

    def getNumberOfVerticesRequest(self):
        return self.graph.vertexCount()

    def getAvgNumberOfVerticesResponse(self):
        values = []
        for i in range(len(self.responseGraphs)):
            values.append(self.responseGraphs[i].vertexCount())

        return mean(values)

    def getAllNumberOfVerticesResponse(self):
        values = []
        for i in range(len(self.responseGraphs)):
            values.append(self.responseGraphs[i].vertexCount())

        return values

    def getAvgEdgeWeightResponse(self):
        values = []
        for i in range(len(self.responseGraphs)):
            totalWeight = 0
            for edgeID in range(self.responseGraphs[i].edgeCount()):      
                totalWeight += self.responseGraphs[i].costOfEdge(edgeID)
            values.append(totalWeight)    
            
        return mean(values)
        
    def getAllEdgeWeightResponse(self):
        values = []
        for i in range(len(self.responseGraphs)):
            totalWeight = 0
            for edgeID in range(self.responseGraphs[i].edgeCount()):
                totalWeight += self.responseGraphs[i].costOfEdge(edgeID)
            values.append(totalWeight)    
            
        return values
            
    def getServerResponses(self):
        return self.serverResponses

    def getParameters(self):
        return self.parameters

    def getAlgorithm(self):
        return self.algorithm

    def getGraphName(self):
        return self.graphName

    def getGraph(self):
        return self.graph

    def getResponseGraphs(self):
        return self.responseGraphs

    def toString(self):
        string = self.graphName + self.algorithm

        for paraKey in self.parameters:
            string = string + str(paraKey) + str(self.parameters[paraKey])

        return string
