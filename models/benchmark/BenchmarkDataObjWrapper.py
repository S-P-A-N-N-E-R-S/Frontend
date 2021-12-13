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
            if analysis == "Runtime(s)":
                if average:
                    values.append(dataObj.getAvgRuntime())
                else:
                    for value in dataObj.getAllRuntimes():
                        values.append(value)                          
            elif analysis == "Number of Edges":
                if average:
                    values.append(dataObj.getAvgNumberOfEdgesResponse())
                else:
                    for value in dataObj.getAllNumberOfEdgesResponse():
                        values.append(value)
            elif analysis == "Number of Vertices":
                if average:
                    values.append(dataObj.getAvgNumberOfVerticesResponse())
                else:
                    for value in dataObj.getAllNumberOfVerticesResponse():
                        values.append(value)
            elif analysis == "Edges Difference":
                if average:
                    values.append(abs(originalGraph.edgeCount() - dataObj.getAvgNumberOfEdgesResponse()))
                else:
                    for edgeCount in dataObj.getAllNumberOfEdgesResponse():
                        values.append(abs(originalGraph.edgeCount() - edgeCount))
            elif analysis == "Vertices Difference":
                if average:
                    values.append(abs(dataObj.getAvgNumberOfVerticesResponse() - originalGraph.vertexCount()))
                else:
                    for vertexCount in dataObj.getAllNumberOfVerticesResponse():
                        values.append(abs(originalGraph.vertexCount() - vertexCount))

            elif analysis == "Average Degree":
                if average:
                    values.append(dataObj.getAvgNumberOfEdgesResponse() / dataObj.getAvgNumberOfVerticesResponse())
                else:
                    allEdgeCounts = dataObj.getAllNumberOfEdgesResponse()
                    allVertexCounts = dataObj.getAllNumberOfVerticesResponse()
                    for i in range(len(allEdgeCounts)):
                        values.append(round(allEdgeCounts[i] / allVertexCounts[i],3))

            elif analysis == "Sparseness":
                if average:
                    values.append(dataObj.getAvgNumberOfEdgesResponse() / originalGraph.edgeCount())
                else:
                    allEdgeCounts = dataObj.getAllNumberOfEdgesResponse()
                    for edgeCount in allEdgeCounts:
                        values.append(round(edgeCount / originalGraph.edgeCount(), 3))

            elif analysis == "Lightness":
                lightness = self._getLightness(originalGraph, dataObj.getParameters()['edgeCosts'])                      
                if average:
                    values.append(dataObj.getAvgEdgeWeightResponse() / lightness)
                else:
                    allEdgeCounts = dataObj.getAllEdgeWeightResponse()
                    for edgeCount in allEdgeCounts:
                        values.append(round(edgeCount / lightness, 3))              
        if average:
            return mean(values)
        else:
            return values

    def _getLightness(self, graph, costFunction = 0):
        request = parserManager.getRequestParser("Minimum Spanning Trees/Kruskals Algorithm")
        parameterFieldsData = {}
        parameterFieldsData['graph'] = graph
        parameterFieldsData['edgeCosts'] = 0
        parameterFieldsData['vertexCoordinates'] = '' 
        for key in parameterFieldsData:
            fieldData = parameterFieldsData[key]
            request.setFieldData(key, fieldData) 
        request.jobName = "mst_benchmark" 
        try:
            with Client(helper.getHost(), helper.getPort()) as client:
                client.sendJobRequest(request)
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
                        time.sleep(1)  
                    states = client.getJobStatus()
                    jobState = list(states.values())[-1]
                    jobId = jobState.jobId
                    job = statusManager.getJobState(jobId)                
                    status = self.STATUS_TEXTS.get(job.status, "status not supported")

            except (NetworkClientError, ParseError) as error:
                return -1
        
        try:
            with Client(helper.getHost(), helper.getPort()) as client:
                response = client.getJobResult(job.jobId)             
                mst = response.getGraph()
                lightness = 0
                for edgeID in range(mst.edgeCount()):
                    lightness += mst.costOfEdge(edgeID)
                return lightness    
                
        except (NetworkClientError, ParseError) as error:
            return -1
          

    def firstPartition(self, partitionType, parameterKey = None):
        """
        Creates the first partitioning of all data objects into a dictionary.

        :type partitionType: String
        :type parameterKey: String (only set if type is "Parameters")
        :returns dictionary
        """
        partition = {}

        if partitionType == "Graphs":
            allGraphs = self._getAllGraphs(self.benchmarkDOs)
            for i in range(len(allGraphs)):
                graphName = allGraphs[i][0]
                dataObjsForPartition = []
                for j in range(len(self.benchmarkDOs)):
                    dataObj = self.benchmarkDOs[j]
                    if dataObj.getGraphName() == graphName:
                        dataObjsForPartition.append(dataObj)
                partition[graphName] = dataObjsForPartition

        elif partitionType == "Algorithms":
            allAlgs = self._getAllAlgs(self.benchmarkDOs)
            for i in range(len(allAlgs)):
                algName = allAlgs[i]
                dataObjsForPartition = []
                for j in range(len(self.benchmarkDOs)):
                    dataObj = self.benchmarkDOs[j]
                    if dataObj.getAlgorithm() == algName:
                        dataObjsForPartition.append(dataObj)
                partition[algName] = dataObjsForPartition

        elif partitionType == "Parameter":
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
                        if graphAnalysis == "Edges":
                            axisEntry = allGraphs[i][1].edgeCount()
                        elif graphAnalysis == "Vertices":
                            axisEntry = allGraphs[i][1].vertexCount()
                        elif graphAnalysis == "Densities":
                            if allGraphs[i][1].edgeDirection == "Directed":
                                axisEntry = allGraphs[i][1].edgeCount() / (allGraphs[i][1].vertexCount()*(allGraphs[i][1].vertexCount()-1))
                            else:
                                axisEntry = (2 * allGraphs[i][1].edgeCount()) / (allGraphs[i][1].vertexCount()*(allGraphs[i][1].vertexCount()-1))
                        axisEntry = round(axisEntry,3)
                        partitionToSort[axisEntry] = dataObjsForPartition

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
