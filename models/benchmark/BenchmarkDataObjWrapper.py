from statistics import mean


class BenchmarkDataObjWrapper():
    """
    Wrapper for all the BenchmarkData objects. It provides an interface to get the information necessary for the
    visualisation process. After the objects are created the benchmark controller only communicates with this wrapper.  
    """
    def __init__(self, DOs):
        # all the BenchmarkData objects created by executing all the permutations
        self.benchmarkDOs = DOs
        
        # dicts the switch between labels and keys of the the fields
        self.parameterKeyHash = {}
        self.labelHash = {}
        
        for dataObj in self.benchmarkDOs:
            for label in dataObj.parameterKeyHash.keys():
                if not label in self.parameterKeyHash:
                    self.parameterKeyHash[label] = dataObj.getParameterKey(label)
            
        for label in self.parameterKeyHash.keys():
            parameterKey = self.parameterKeyHash[label]
            self.labelHash[parameterKey] = label    
        


    def getAnalysisValue(self, analysis, dataObjs):
        """
        Method gets called at the end of the partitioning process. Returns a value depending on the
        chosen analysis. Since multiple execution of the same parameters are possible a list of
        values might be returned.
        
        :type analysis: String
        :type dataObjs: list of BenchmarkData objects
        :return list
        """
        values = []
        for dataObj in dataObjs:
            
            originalGraph = dataObj.getGraph()
            if analysis == "Runtime":
                print("TODO")
                values.append(0)
            elif analysis == "Number of Edges":
                values.append(dataObj.getAvgNumberOfEdgesResponse())
            elif analysis == "Number of Vertices":
                values.append(dataObj.getAvgNumberOfVerticesResponse())
            elif analysis == "Edges Difference":
                values.append(abs(originalGraph.edgeCount() - dataObj.getAvgNumberOfEdgesResponse()))
            elif analysis == "Vertices Difference":
                values.append(abs(dataObj.getAvgNumberOfVerticesResponse() - originalGraph.vertexCount()))
            elif analysis == "Average Degree":
                values.append(dataObj.getAvgNumberOfEdgesResponse() / dataObj.getAvgNumberOfVerticesResponse())
            elif analysis == "Sparseness":
                values.append(dataObj.getAvgNumberOfEdgesResponse() / originalGraph.edgeCount()) 
            
        return mean(values)      
    
              
    def firstPartition(self, type, parameterKey = None):
        """
        Creates the first partitioning of all data objects into a dictionary.
        
        :type type: String
        :type parameterKey: String (only set if type is "Parameters")
        :returns dictionary
        """
        partition = {}
        
        if type == "Graphs":
            allGraphs = self._getAllGraphs(self.benchmarkDOs)
            for i in range(len(allGraphs)):  
                graphName = allGraphs[i]  
                dataObjsForPartition = []           
                for j in range(len(self.benchmarkDOs)):
                    dataObj = self.benchmarkDOs[j]
                    if dataObj.getGraphName() == graphName:
                        dataObjsForPartition.append(dataObj)
                partition[graphName] = dataObjsForPartition
                
                
        elif type == "Algorithms":
            allAlgs = self._getAllAlgs(self.benchmarkDOs)
            for i in range(len(allAlgs)):
                algName = allAlgs[i]
                dataObjsForPartition = []  
                for j in range(len(self.benchmarkDOs)):
                    dataObj = self.benchmarkDOs[j]
                    if dataObj.getAlgorithm() == algName:
                        dataObjsForPartition.append(dataObj)
                partition[algName] = dataObjsForPartition
        
        elif type == "Parameter":  
            # there should be one list for every range value  
            allValues = self._getAllParameterValues(parameterKey, self.benchmarkDOs)
            
            for value in allValues:
                dataObjsForPartition = []
                for i in range(len(self.benchmarkDOs)):
                    dataObj = self.benchmarkDOs[i]
                    parameters = dataObj.getParameters()
                    for param in parameters.keys():
                        if param == parameterKey and parameters[param] == value:
                            dataObjsForPartition.append(dataObj)
                            
                partition[parameterKey + "#" + str(value)] = dataObjsForPartition
            
        return partition
    
    def partition(self, type, dict, parameterKey = None):
        """
        Method is called multiple times, depending on the number of selections made.
        
        :type type: String
        :type parameterKey: String (only set if type is "Parameters")
        :returns dictionary
        """
        partition = {}
        for key in dict.keys():
            doList = dict[key]          
            if type == "Graphs":
                allGraphs = self._getAllGraphs(doList)
                for i in range(len(allGraphs)):  
                    graphName = allGraphs[i]  
                    dataObjsForPartition = []           
                    for j in range(len(doList)):
                        dataObj = doList[j]
                        if dataObj.getGraphName() == graphName:
                            dataObjsForPartition.append(dataObj)          
                    keyTuple = key
                    if isinstance(keyTuple, tuple):
                        listConv = list(keyTuple)
                        listConv.append(graphName)
                        keyTuple = tuple(listConv)
                    else:
                        keyTuple = (key, graphName)             
                    
                    partition[keyTuple] = dataObjsForPartition 
            
            elif type == "Algorithms":
                allAlgs = self._getAllAlgs(doList)
                for i in range(len(allAlgs)):  
                    algName = allAlgs[i]  
                    dataObjsForPartition = []           
                    for j in range(len(doList)):
                        dataObj = doList[j]
                        if dataObj.getAlgorithm() == algName:
                            dataObjsForPartition.append(dataObj)              
                    keyTuple = key
                    if isinstance(keyTuple, tuple):
                        listConv = list(keyTuple)
                        listConv.append(algName)
                        keyTuple = tuple(listConv)
                    else:
                        keyTuple = (key, algName)       
                    
                    partition[keyTuple] = dataObjsForPartition       
             
            else:         
                # there should be one list for every range value  
                allValues = self._getAllParameterValues(parameterKey, doList)
                                        
                for value in allValues:                   
                    dataObjsForPartition = []
                    for i in range(len(doList)):
                        dataObj = doList[i]
                        parameters = dataObj.getParameters()
                        for param in parameters.keys():
                            if param == parameterKey and parameters[param] == value:
                                dataObjsForPartition.append(dataObj)
                                      
                    keyTuple = key
                    if isinstance(keyTuple, tuple):
                        listConv = list(keyTuple)
                        listConv.append(parameterKey + "#" + str(value))
                        keyTuple = tuple(listConv)
                    else:
                        keyTuple = (key, parameterKey + "#" + str(value))
                                                  
                    partition[keyTuple] = dataObjsForPartition                         
        
        return partition
        
        
    def _getAllParameterValues(self, parameterKey, dataObjects):
        valueList = []
        for dataObj in dataObjects:
            parameters = dataObj.getParameters()
            for param in parameters.keys():
                if param == parameterKey:
                    value = parameters[param]
                    if not value in valueList:
                        valueList.append(value)
        return valueList
    
    def _getAllGraphs(self, dataObjects):
        graphList = []
        for dataObj in dataObjects:
            if not dataObj.getGraphName() in graphList:
                graphList.append(dataObj.getGraphName())
        
        return graphList
    
    def _getAllAlgs(self, dataObjects):
        algList = []
        for dataObj in dataObjects:
            if not dataObj.getAlgorithm() in algList:
                algList.append(dataObj.getAlgorithm())
    
        return algList    
            
        
        