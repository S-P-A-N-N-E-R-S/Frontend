import os

from qgis.core import QgsSettings, QgsApplication, QgsProject

from .base import BaseController
from .. import mainPlugin
from ..exceptions import FieldRequiredError
from .. import helperFunctions as helper
from ..network import parserManager
from ..network import statusManager
from ..network.protocol.build.status_pb2 import StatusType
from ..models.benchmark.BenchmarkDataObjWrapper import BenchmarkDataObjWrapper
from ..models.benchmark.BenchmarkVisualisation import BenchmarkVisualisation

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError
import time

class BenchmarkController(BaseController):
    """
    Controller which does the calls to the server, collects the results and executes the 
    visualisation process. 
    """
    def __init__(self, view):
        """
        Constructor
        :type view: benchmarkView
        """
        super().__init__(view)

        self.STATUS_TEXTS = {
            StatusType.UNKNOWN_STATUS: self.tr("unknown"),
            StatusType.WAITING: self.tr("waiting"),
            StatusType.RUNNING: self.tr("running"),
            StatusType.SUCCESS: self.tr("success"),
            StatusType.FAILED: self.tr("failed"),
            StatusType.ABORTED: self.tr("aborted"),
        }

        self.settings = QgsSettings()
        self.authManager = QgsApplication.authManager()

        # add available analysis
        for requestKey, request in parserManager.getRequestParsers().items():
            self.view.addOGDFAlg(request.name)
        
        self.doWrapper = None 

    def _visualisationControl(self):
        
        visualisations = self.view.getVisualisation() 
        
        # go through all the benchmark requests created    
        for sIndex in range(len(self.view.getSelection1())):
            benchVis = BenchmarkVisualisation(self.view.getAnalysis()[sIndex])
            
            selectionList = self.view.getSelection1()[sIndex]
            if len(selectionList) > 0:
                selection = selectionList[0]
                partition = None
                if selection == "Graphs" or selection == "Algorithms":
                    partition = self.doWrapper.firstPartition(selection)             
                else:               
                    partition = self.doWrapper.firstPartition("Parameter", self.doWrapper.parameterKeyHash[selection])
                
                print(partition)
                print("---------------------------------------------------------------------------")
                
                for i in range(1,len(selectionList)):
                    selection = selectionList[i]
                    if selection == "Graphs" or selection == "Algorithms":
                        partition = self.doWrapper.partition(selection, partition)
                    else:
                        partition = self.doWrapper.partition("Parameter", partition, self.doWrapper.parameterKeyHash[selection])    
    
                    print(partition)
                    print("---------------------------------------------------------------------------")
            
                print("*****************************************************************************************")
                  
            else:
                
                partition = {"":self.doWrapper.benchmarkDOs}
                
            # at this point all the different to plot values are sorted out (all the value functions)
            
            # split the partition into individual dictionary entries
            for dictKey in partition.keys():
                            
                dictValue = partition[dictKey]
                
                if isinstance(dictKey, tuple):                    
                    zParameter = ""
                    for key in dictKey:
                        if zParameter == "":
                            zParameter = key
                        else:
                            zParameter = zParameter + " / " + key
                else:
                    zParameter = dictKey
                
                dictHelp = {dictKey : dictValue}            
                selectionList2 = self.view.getSelection2()[sIndex]
                for selection in selectionList2:
                    if selection == "Graphs" or selection == "Algorithms":
                        dictHelp = self.doWrapper.partition(selection, dictHelp)
                    else:
                        dictHelp = self.doWrapper.partition("Parameter", dictHelp, self.doWrapper.parameterKeyHash[selection])  
                
                # get all the analysis values and save them so they can be plotted later
                # store into dictHelp (same keys and transform DOs into numbers)
                xParameters = []
                xValues = []
                for dictKey2 in dictHelp:
                    
                    if isinstance(dictKey2, tuple):
                        parameterString = ""
                        for parameter in dictKey2[len(selectionList):]:
                            if parameterString == "":
                                parameterString = parameter
                            else:    
                                parameterString = parameterString + " / " + parameter
                        
                        xParameters.append(parameterString)
                    else:
                        xParameters.append(dictKey2)
                                    
                    xValues.append(self.doWrapper.getAnalysisValue(self.view.getAnalysis()[sIndex], dictHelp[dictKey2]))
            
                xLabel = ""
                
                for selection in selectionList2:
                    if xLabel == "":
                        xLabel = selection
                    else:    
                        xLabel = xLabel + "/" + selection
                         
                xParametersValues = []
                for p in range(len(xParameters)):
                    xParameters[p] = xParameters[p].replace(" ","")
                    diffParaSplit = xParameters[p].split("/")
                    axisValue = ""
                    for diffPara in diffParaSplit:                                     
                        if "#" in diffPara:   
                            if axisValue == "":
                                axisValue = diffPara.split("#")[1]
                            else:
                                axisValue = axisValue + " / " + diffPara.split("#")[1]
                                                                                   
                        else:
                            if axisValue == "":
                                axisValue = diffPara
                            else:
                                axisValue = axisValue + " / " + diffPara                         
            
                    xParametersValues.append(axisValue)
                    
                
                benchVis.setOnePlotData(xLabel, xParametersValues, zParameter, xValues)
                   
                       
            visCounter = 0            
            for vis in visualisations[sIndex]:
                if vis == "Points without connection":
                    benchVis.plotPoints(False, sIndex + visCounter)
                elif vis == "Points with connection":
                    benchVis.plotPoints(True, sIndex + visCounter)
                elif vis == "Bar chart":
                    benchVis.plotBarChart(sIndex + visCounter)
                elif vis == "Lines":
                    benchVis.plotLines(sIndex + visCounter)
                elif vis == "Box plot":         
                    benchVis.plotBoxPlot(sIndex + visCounter)
                visCounter+=1
            
    def runJob(self):
        # todo: pass authId to client
        print("RUN JOB START")
        authId = self.settings.value("ogdfplugin/authId")
        
        # create and get BenchmarkData objects
        benchmarkDOs = self.view.ogdfBenchmarkWidget.getBenchmarkDataObjects()  
        
        for benchmarkDO in benchmarkDOs:
            print("--------------------------")
            print(benchmarkDO.algorithm)
            print(benchmarkDO.graphName)
            print(benchmarkDO.parameters)
            
            requestKey = benchmarkDO.algorithm
            request = parserManager.getRequestParser(requestKey)
            request.resetData()
            
            for key in benchmarkDO.parameters:
                fieldData = benchmarkDO.parameters[key]
                request.setFieldData(key, fieldData)
                      
            try:
                with Client(helper.getHost(), helper.getPort()) as client:
                    client.sendJobRequest(request)
                    self.view.showSuccess("Job started!")                   
            except (NetworkClientError, ParseError) as error:
                self.view.showError(str(error), self.tr("Network Error"))          
            
            status = "waiting"    
            counter = 0         
            while status != "success":           
                try:
                    with Client(helper.getHost(), helper.getPort()) as client:
                        if counter == 0:
                            time.sleep(0.5) 
                            counter+=1
                        else:
                            time.sleep(1)    
                        states = client.getJobStatus()
                        jobState = list(states.values())[-1]                       
                        id = jobState.jobId                        
                        job = statusManager.getJobState(id)                                          
                        status = self.STATUS_TEXTS.get(job.status, "status not supported")
                        print(status)
        
                except (NetworkClientError, ParseError) as error:
                    self.view.showError(str(error), self.tr("Network Error"))
            
            for exe in range(self.view.getExecutions(benchmarkDO.algorithm)):                             
                try:
                    with Client(helper.getHost(), helper.getPort()) as client:
                    
                        response = client.getJobResult(job.jobId)
                        benchmarkDO.setServerResponse(response)
                        benchmarkDO.setResponseGraph(response.getGraph())

                except (NetworkClientError, ParseError) as error:
                    self.view.showError(str(error), self.tr("Network Error"))
                                
        self.doWrapper = BenchmarkDataObjWrapper(benchmarkDOs)              
        
        self._visualisationControl()   
            
