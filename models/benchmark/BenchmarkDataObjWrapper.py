import time
from statistics import mean
from collections import OrderedDict
from ...network.client import Client
from ...network import parserManager
from ...network.exceptions import NetworkClientError, ParseError
from ... import helperFunctions as helper
from ...network import statusManager
from ...network.protocol.build.status_pb2 import StatusType

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

        for label in self.parameterKeyHash:
            parameterKey = self.parameterKeyHash[label]
            self.labelHash[parameterKey] = label
            
        self.STATUS_TEXTS = {
            StatusType.UNKNOWN_STATUS: "unknown",
            StatusType.WAITING: "waiting",
            StatusType.RUNNING: "running",
            StatusType.SUCCESS: "success",
            StatusType.FAILED: "failed",
            StatusType.ABORTED: "aborted",
        }
        
        self.serverCallMatchings = {"Min Fragility": ("utils/Fragility", "minFragility", None),
                                    "Max Fragility": ("utils/Fragility", "maxFragility", None),
                                    "Avg Fragility": ("utils/Fragility", "avgFragility", None),
                                    "Diameter": ("utils/Diameter", "diameter", None),
                                    "Radius": ("utils/Radius", "radius", None),
                                    "Girth (unit weights)": ("utils/Girth", "girth", {"graphAttributes.unitWeights": 1}),
                                    "Girth": ("utils/Girth", "girth", {"graphAttributes.unitWeights": 0})}

    def getAnalysisValue(self, analysis, dataObjs, average):
        """
        Method gets called at the end of the partitioning process. Returns a value depending on the
        chosen analysis. Since multiple execution of the same parameters are possible a list of
        values might be returned.

        :type analysis: String
        :type dataObjs: list of BenchmarkData objects
        :type average: boolean
        :return list or value
        """
        values = []
        for dataObj in dataObjs:
            originalGraph = dataObj.getGraph()
            if analysis == "Runtime (seconds)":
                if average:
                    values = [dataObj.getAvgRuntime()]
                else:
                    values = dataObj.getAllRuntimes()                       
            elif analysis == "Number of Edges":
                if average:
                    values = [dataObj.getAvgNumberOfEdgesResponse()]
                else:
                    values = dataObj.getAllNumberOfEdgesResponse()
            elif analysis == "Number of Vertices":
                if average:
                    values = [dataObj.getAvgNumberOfVerticesResponse()]
                else:
                    values = dataObj.getAllNumberOfVerticesResponse()
            elif analysis == "Edges Difference":
                if average:
                    values = [abs(originalGraph.edgeCount() - dataObj.getAvgNumberOfEdgesResponse())]
                else:
                    for edgeCount in dataObj.getAllNumberOfEdgesResponse():
                        values.append(abs(originalGraph.edgeCount() - edgeCount))
            elif analysis == "Vertices Difference":
                if average:
                    values = [abs(dataObj.getAvgNumberOfVerticesResponse() - originalGraph.vertexCount())]
                else:
                    for vertexCount in dataObj.getAllNumberOfVerticesResponse():
                        values.append(abs(originalGraph.vertexCount() - vertexCount))
            elif analysis == "Average Degree":
                if average:
                    values = [dataObj.getAvgNumberOfEdgesResponse() / dataObj.getAvgNumberOfVerticesResponse()]
                else:
                    allEdgeCounts = dataObj.getAllNumberOfEdgesResponse()
                    allVertexCounts = dataObj.getAllNumberOfVerticesResponse()
                    for i in range(len(allEdgeCounts)):
                        values.append(round(allEdgeCounts[i] / allVertexCounts[i],3))
            elif analysis == "Sparseness":
                if average:
                    values = [dataObj.getAvgNumberOfEdgesResponse() / originalGraph.edgeCount()]
                else:
                    allEdgeCounts = dataObj.getAllNumberOfEdgesResponse()
                    for edgeCount in allEdgeCounts:
                        values.append(round(edgeCount / originalGraph.edgeCount(), 3))
            elif analysis == "Lightness":           
                costFunction = dataObj.getParameters()['edgeCosts']    
                mstWeight = float(self.serverCall(originalGraph, "Minimum Spanning Trees/Kruskals Algorithm", costFunction).data["totalWeight"])  
                if average:
                    values = [dataObj.getAvgEdgeWeightResponse() / mstWeight]
                else:
                    allEdgeCounts = dataObj.getAllEdgeWeightResponse()
                    for edgeCount in allEdgeCounts:
                        values.append(round(edgeCount / mstWeight, 3))                       
            
            if analysis in self.serverCallMatchings:
                values = self._getAnalysisValuesFromServer(dataObj, analysis)
                      
            elif analysis == "Node Connectivity":
                if originalGraph.edgeDirection == "Directed":
                    directed = 1
                else:
                    directed = 0  
                addInfos = {"graphAttributes.directed": directed, "graphAttributes.nodeConnectivity": 1}
                for graph in dataObj.getResponseGraphs():              
                    values.append(float(self.serverCall(graph, "utils/Connectivity", 0, addInfos).data["connectivity"]))
            elif analysis == "Edge Connectivity":
                if originalGraph.edgeDirection == "Directed":
                    directed = 1
                else:
                    directed = 0   
                addInfos = {"graphAttributes.directed": directed, "graphAttributes.nodeConnectivity": 0}
                for graph in dataObj.getResponseGraphs():              
                    values.append(float(self.serverCall(graph, "utils/Connectivity", 0, addInfos).data["connectivity"]))
            elif analysis == "Reciprocity":
                if average:
                    values = [dataObj.getAvgNumberOfReciprocalEdges() / dataObj.getAvgNumberOfEdgesResponse()]                      
                else:
                    counts = dataObj.getAllNumberOfReciprocalEdges()
                    allResponseGraphs = dataObj.getResponseGraphs()
                    for index, count  in enumerate(counts):
                        values.append(count / allResponseGraphs[index].edgeCount())
                                                                    
        # redundant in most cases because values has only one value
        if average:
            return mean(values)
        else:
            return values

    def partition(self, partitionType, partitionDict, parameterKey = None, graphAnalysis = None):
        """
        Method is called multiple times, depending on the number of selections made.

        :type partitionType: String
        :type parameterKey: String (only set if type is "Parameters")
        :returns dictionary
        """
        partition = {}
        for key in partitionDict.keys():
            doList = partitionDict[key]
            if partitionType == "Graphs":
                partitionToSort = {}
                allGraphs = self._getAllGraphs(doList)
                for i in range(len(allGraphs)):
                    graphName = allGraphs[i][0]
                    # get all data objects which use the graph
                    dataObjsForPartition = []
                    for j in range(len(doList)):
                        dataObj = doList[j]
                        if dataObj.getGraphName() == graphName:
                            dataObjsForPartition.append(dataObj)
                    keyTuple = key

                    # check if the graph name should be used or a graph attribute
                    if graphAnalysis is None:
                        axisEntry = graphName
                    else:
                        if graphAnalysis == "Edges" or graphAnalysis == "Vertices" or graphAnalysis == "Densities" or graphAnalysis == "Reciprocity":
                            if graphAnalysis == "Edges":
                                axisEntry = allGraphs[i][1].edgeCount()
                            elif graphAnalysis == "Vertices":
                                axisEntry = allGraphs[i][1].vertexCount()
                            elif graphAnalysis == "Densities":
                                if allGraphs[i][1].edgeDirection == "Directed":
                                    axisEntry = allGraphs[i][1].edgeCount() / (allGraphs[i][1].vertexCount()*(allGraphs[i][1].vertexCount()-1))
                                else:
                                    axisEntry = (2 * allGraphs[i][1].edgeCount()) / (allGraphs[i][1].vertexCount()*(allGraphs[i][1].vertexCount()-1))
                            elif graphAnalysis == "Reciprocity":
                                count = 0
                                for edgeID in range(allGraphs[i][1].edgeCount()):
                                    edge = allGraphs[i][1].edge(edgeID)
                                    if allGraphs[i][1].hasEdge(edge.toVertex(), edge.fromVertex()) != -1:
                                        count+=1
                                axisEntry = count / allGraphs[i][1].edgeCount()
                            # order the data objects into the correct dictionary entry
                            axisEntry = round(axisEntry,3)
                            if axisEntry in partitionToSort:
                                partitionToSort[axisEntry].extend(dataObjsForPartition)
                            else:
                                partitionToSort[axisEntry] = dataObjsForPartition
                        else:                          
                            if graphAnalysis in self.serverCallMatchings:
                                for dataObj in dataObjsForPartition:
                                    axisEntry = self._getAxisEntryFromServer(dataObj, graphAnalysis, allGraphs, i)
                                    if axisEntry in partitionToSort:
                                        partitionToSort[axisEntry].append(dataObj)
                                    else:
                                        partitionToSort[axisEntry] = [dataObj] 
                                        
                            elif graphAnalysis == "Node Connectivity":
                                if allGraphs[i][1].edgeDirection == "Directed":
                                    directed = 1
                                else:
                                    directed = 0
                                costFunction = dataObj.getParameters()['edgeCosts']
                                addInfos = {"graphAttributes.directed": directed, "graphAttributes.nodeConnectivity": 1}
                                axisEntry = float(self.serverCall(allGraphs[i][1], "utils/Connectivity", costFunction, addInfos).data["connectivity"])  
                                if axisEntry in partitionToSort:
                                    partitionToSort[axisEntry].append(dataObj)
                                else:
                                    partitionToSort[axisEntry] = [dataObj] 
                            elif graphAnalysis == "Edge Connectivity":
                                if allGraphs[i][1].edgeDirection == "Directed":
                                    directed = 1
                                else:
                                    directed = 0
                                costFunction = dataObj.getParameters()['edgeCosts'] 
                                addInfos = {"graphAttributes.directed": directed, "graphAttributes.nodeConnectivity": 0}
                                axisEntry = float(self.serverCall(allGraphs[i][1], "utils/Connectivity", costFunction, addInfos).data["connectivity"])  
                                if axisEntry in partitionToSort:
                                    partitionToSort[axisEntry].append(dataObj)
                                else:
                                    partitionToSort[axisEntry] = [dataObj]                                    
                    
                    if graphAnalysis is None:
                        if isinstance(keyTuple, tuple):
                            listConv = list(keyTuple)
                            listConv.append(axisEntry)
                            keyTuple = tuple(listConv)
                        else:
                            keyTuple = (key, axisEntry)
                        partition[keyTuple] = dataObjsForPartition

                if graphAnalysis is not None:
                    partition = OrderedDict()

                    for sortedKey in sorted(partitionToSort.keys()):
                        keyTuple = key
                        if isinstance(keyTuple, tuple):
                            listConv = list(keyTuple)
                            listConv.append(str(sortedKey))
                            keyTuple = tuple(listConv)
                        else:
                            keyTuple = (key, str(sortedKey))

                        partition[keyTuple] = partitionToSort[sortedKey]
                
            elif partitionType == "Algorithms":
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

    def _getAxisEntryFromServer(self, dataObj, analysis, allGraphs, i):
        costFunction = dataObj.getParameters()['edgeCosts']  
        result = self.serverCall(allGraphs[i][1], self.serverCallMatchings[analysis][0], costFunction, self.serverCallMatchings[analysis][2]).data[self.serverCallMatchings[analysis][1]]
        return float(result)

    def _getAnalysisValuesFromServer(self, dataObj, analysis):
        values = []
        for graph in dataObj.getResponseGraphs():
            values.append(float(self.serverCall(graph, self.serverCallMatchings[analysis][0], 0, self.serverCallMatchings[analysis][2]).data[self.serverCallMatchings[analysis][1]]))
        return values

    def serverCall(self, graph, algoString, costFunction, addInfos = None):
        # TODO: set costFunction correctly if this is fixed in the network
        # Currently the returned graph has advanced costs with one cost function
        # so its works to set the edge costs to 0 for the analysis calls (except lightness call)
        
        request = parserManager.getRequestParser(algoString)
        parameterFieldsData = {}
        parameterFieldsData['graph'] = graph
        parameterFieldsData['edgeCosts'] = costFunction
        parameterFieldsData['vertexCoordinates'] = ''
        if addInfos is not None:
            for key in addInfos:
                parameterFieldsData[key] = addInfos[key]
        for key in parameterFieldsData:
            fieldData = parameterFieldsData[key]
            request.setFieldData(key, fieldData) 
        request.jobName = algoString + "benchmark" 
        try:
            with Client(helper.getHost(), helper.getPort()) as client:
                executionID = client.sendJobRequest(request)
        except (NetworkClientError, ParseError) as error:
            pass 
        status = "waiting"
        counter = 0
        while status != "success":
            if status == "failed":
                return -1        
            try:
                with Client(helper.getHost(), helper.getPort()) as client:
                    if counter == 0:
                        time.sleep(0.25)
                        counter+=1
                    else:
                        time.sleep(0.25)       
                    jobStatus = client.getJobStatus()
                                  
                    jobId = executionID
                    job = jobStatus[jobId]                 
                    status = self.STATUS_TEXTS.get(job.status, "status not supported")
            except (NetworkClientError, ParseError) as error:
                return -1
        try:
            with Client(helper.getHost(), helper.getPort()) as client:         
                response = client.getJobResult(job.jobId)                          
                return response
                
        except (NetworkClientError, ParseError) as error:
            return -1

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
                graphList.append((dataObj.getGraphName(),dataObj.getGraph()))

        return graphList

    def _getAllAlgs(self, dataObjects):
        algList = []
        for dataObj in dataObjects:
            if not dataObj.getAlgorithm() in algList:
                algList.append(dataObj.getAlgorithm())

        return algList
