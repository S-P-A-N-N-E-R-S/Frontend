from statistics import mean


class BenchmarkDataObjWrapper():
      
    def __init__(self, DOs):
        self.benchmarkDOs = DOs
        
        self.parameterKeyHash = {}
        self.labelHash = {}
        
        for dataObj in self.benchmarkDOs:
            for label in dataObj.parameterKeyHash.keys():
                if not label in self.parameterKeyHash:
                    self.parameterKeyHash[label] = dataObj.getParameterKey(label)
            
        for label in self.parameterKeyHash.keys():
            parameterKey = self.parameterKeyHash[label]
            self.labelHash[parameterKey] = label    
        

    # gets called at the end of the partitioning process
    def getAnalysisValue(self, analysis, dataObjs):
        print(dataObjs)
        print(analysis)
        values = []
        for dataObj in dataObjs:
            
            originalGraph = dataObj.getGraph()
            responseGraph = dataObj.getResponseGraph()
            if analysis == "Runtime":
                print("TODO")
                values.append(0)
            elif analysis == "Number of Edges":
                values.append(responseGraph.edgeCount())
            elif analysis == "Number of Vertices":
                values.append(responseGraph.vertexCount())
            elif analysis == "Edges Difference":
                values.append(abs(originalGraph.edgeCount() - responseGraph.edgeCount()))
            elif analysis == "Vertices Difference":
                values.append(abs(originalGraph.vertexCount() - responseGraph.vertexCount()))
            elif analysis == "Average Degree":
                values.append(responseGraph.edgeCount() / responseGraph.vertexCount())
            elif analysis == "Sparseness":
                values.append(responseGraph.edgeCount() / originalGraph.edgeCount()  ) 
            
        return mean(values)      
    
              
    def firstPartition(self, type, parameterKey = None):
        # creates the first partitioning of all data objects (into dictionary)
       
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
            
        
        