import time
from datetime import date, datetime

from qgis.core import QgsSettings, QgsApplication, QgsTask, QgsMessageLog, Qgis

from .base import BaseController
from .. import helperFunctions as helper
from ..network import parserManager
from ..network import statusManager
from ..network.protocol.build.status_pb2 import StatusType
from ..models.benchmark.BenchmarkDataObjWrapper import BenchmarkDataObjWrapper
from ..models.benchmark.BenchmarkVisualisation import BenchmarkVisualisation

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError, ServerError
from .. import helperFunctions as helper


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
        requestNameList = []
        for request in parserManager.getRequestParsers().values():
            requestNameList.append(request.name)

        self.view.addOGDFAlgs(requestNameList)

        self.doWrapper = None
        self.task = None

    def _visualisationControl(self):
        """
        Method partitions the benchmark data objects and calls the visualisation with matplotlib.
        The partitioning depends on the settings in the benchmark selection section of the benchmark view
        and the visualisation depends on the visualisation section in the view.
        """
        visualisations = self.view.getVisualisation()
        visCounter = 1

        analysisSelections = self.view.getAnalysis()
        legendSelections = self.view.getCreateLegendSelection()
        logSelections = self.view.getLogAxisSelection()
        tightSelections = self.view.getTightLayoutSelection()

        # go through all the benchmark requests created
        for sIndex in range(len(self.view.getSelection1())):
            benchVis = BenchmarkVisualisation(analysisSelections[sIndex], legendSelections[sIndex], logSelections[sIndex], tightSelections[sIndex])

            selectionList = self.view.getSelection1()[sIndex]
            if len(selectionList) > 0:
                selection = selectionList[0]
                partition = None
                if selection == "Graphs" or selection == "Algorithms":
                    partition = self.doWrapper.firstPartition(selection)
                else:
                    partition = self.doWrapper.firstPartition("Parameter", self.doWrapper.parameterKeyHash[selection])

                for i in range(1,len(selectionList)):
                    selection = selectionList[i]
                    if selection == "Graphs" or selection == "Algorithms":
                        partition = self.doWrapper.partition(selection, partition)
                    else:
                        partition = self.doWrapper.partition("Parameter", partition, self.doWrapper.parameterKeyHash[selection])
            else:
                partition = {"":self.doWrapper.benchmarkDOs}

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
                    if selection == "Algorithms" or selection == "Graphs":
                        dictHelp = self.doWrapper.partition(selection, dictHelp)

                    elif selection == "Graph Vertices" or selection == "Graph Edges" or selection == "Graph Densities":
                        dictHelp = self.doWrapper.partition("Graphs", dictHelp, graphAnalysis = selection.split(" ")[1])

                    else:
                        dictHelp = self.doWrapper.partition("Parameter", dictHelp, self.doWrapper.parameterKeyHash[selection])

                # get all the analysis values and save them so they can be plotted later
                # store into dictHelp (same keys and transform DOs into numbers)
                xParameters = []
                xValues = []
                xValuesBox = []
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

                    # check if box plot selected
                    boxPlotSel = False
                    for vis in visualisations[sIndex]:
                        if vis == "Box plot":
                            boxPlotSel = True

                    if boxPlotSel:
                        xValuesBox.append(self.doWrapper.getAnalysisValue(self.view.getAnalysis()[sIndex], dictHelp[dictKey2], False))
                    xValues.append(self.doWrapper.getAnalysisValue(self.view.getAnalysis()[sIndex], dictHelp[dictKey2], True))

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
                benchVis.setOneBoxPlotData(xLabel, xParametersValues, zParameter, xValuesBox)

            for vis in visualisations[sIndex]:
                if vis == "Points without connection":
                    benchVis.plotPoints(False, visCounter)
                elif vis == "Points with connection":
                    benchVis.plotPoints(True, visCounter)
                elif vis == "Bar chart":
                    benchVis.plotBarChart(visCounter)
                elif vis == "Lines":
                    benchVis.plotLines(visCounter)
                elif vis == "Box plot":
                    benchVis.plotBoxPlot(visCounter)
                visCounter+=1
                # create text file
                if self.view.getCsvCreationSelection():
                    benchVis.createTextFile(self.view.getTextFilePath(), vis == "Box plot")


    def _checkSelections(self):
        """
        Checks if the selections made in the view are correct and no selection is missing.
        Returns True if the selections are all correct and returns False if not.
        Additionally an error is shown if the selection is not correct.

        :return Boolean
        """
        selection1 = self.view.getSelection1()
        selection2 = self.view.getSelection2()
        analysisList = self.view.getAnalysis()
        visualisation = self.view.getVisualisation()

        if self.view.getNumberOfSelectedGraphs() == 0:
            self.view.showError(self.tr("Select at least one graph"), self.tr("Error in benchmark"))
            return False

        # check selection 2
        for counter, sel2 in enumerate(selection2):
            if len(sel2) == 0:
                self.view.showError(self.tr("Enter at least one parameter in selection 2"), self.tr("Error in benchmark number " + str(counter+1)))
                return False

        # check analysis selections
        if len(selection2) != len(analysisList):
            self.view.showError(self.tr("One analysis selection necessary"), self.tr("Error in benchmark"))
            return False

        # check no duplicate selections
        for counter, sel1  in enumerate(selection1):
            for checkedItem1 in sel1:
                for checkedItem2 in selection2[counter]:
                    if checkedItem1 == checkedItem2:
                        self.view.showError(self.tr("Duplicate selection"), self.tr("Error in benchmark number " + str(counter+1)))
                        return False

        for counter, vis in enumerate(visualisation):
            if len(vis) == 0:
                self.view.showError(self.tr("No visualisation selected"), self.tr("Error in benchmark number " + str(counter+1)))
                return False

        for counter, sel1  in enumerate(selection1):
            for checkedItem1 in sel1:
                for checkedItem2 in selection2[counter]:
                    if checkedItem1 == "Graphs" and (checkedItem2 == "Graph Edges" or checkedItem2 == "Graph Vertices" or checkedItem2 == "Graph Densities"):
                        self.view.showError(self.tr("No further graph attribute selection possible"), self.tr("Error in benchmark number " + str(counter+1)))
                        return False

        if self.view.getNumberOfSelectedGraphs() == 1:
            for counter, sel1  in enumerate(selection1):
                for sel in sel1:
                    if sel == "Graphs":
                        self.view.showError(self.tr("Select multiple graphs"), self.tr("Error in benchmark number " + str(counter+1)))
                        return False

            for counter, sel2  in enumerate(selection2):
                for sel in sel2:
                    if sel == "Graphs":
                        self.view.showError(self.tr("Select multiple graphs"), self.tr("Error in benchmark number " + str(counter+1)))
                        return False
        return True

    def runTask(self):
        # create and get BenchmarkData objects
        if self.task is None:
            self.benchmarkDOs = self.view.getOGDFBenchmarkWidget().getBenchmarkDataObjects()
            if not self._checkSelections():
                return
            task = QgsTask.fromFunction("Start benchmark process", self.runJob, on_finished=self.completed)
            self.task = task
            QgsApplication.taskManager().addTask(task)

    def completed(self, _exception, result=None):
        if not result is None:
            QgsMessageLog.logMessage("Exception: {}".format(result), "TaskFromFunction", Qgis.Critical)

        elif self.task is not None and not self.task.isCanceled():
            try:
                if self.view.getCsvCreationSelection():
                    path = self.view.getTextFilePath()
                    dateString = date.today().strftime("%b_%d_%Y_")
                    timeString = datetime.now().strftime("%H_%M_%S")
                    if path == "":
                        f = open(path + "Complete_Benchmark_Data_" + dateString + timeString + ".csv","w")
                    else:
                        f = open(path + "/" + "Complete_Benchmark_Data_" + dateString + timeString + ".csv","w")

                    # write header to file
                    f.write("Algorithm,Name of Graph")
                    allParameters = []
                    for benchmarkDO in self.benchmarkDOs:
                        for key in benchmarkDO.parameters.keys():
                            if not key in allParameters and key != "graph":
                                allParameters.append(key)
                    for paraKey in allParameters:
                        f.write("," + str(paraKey))

                    f.write(",Runtime,Number of Edges,Number of Vertices,Edges Difference,Vertices Difference,Average Degree,Sparseness,Lightness\n")

                    for benchmarkDO in self.benchmarkDOs:
                        # write all benchmark information into file
                        f.write(benchmarkDO.algorithm +  "," + benchmarkDO.graphName)
                        for paraKey in allParameters:
                            if paraKey in benchmarkDO.parameters.keys():
                                paraString = str(benchmarkDO.parameters[paraKey])
                                if "," in paraString and "(" in paraString:
                                    paraString = paraString.split(",")[0].replace("(","").replace("'","")
                                f.write("," + paraString)
                            else:
                                f.write(",?")
                        allNumberOfEdgesResponse = benchmarkDO.getAllNumberOfEdgesResponse()
                        f.write("," + str(benchmarkDO.getAvgRuntime()))
                        f.write("," + str(allNumberOfEdgesResponse).replace("[","").replace("]","").replace(",","/").replace(" ",""))
                        f.write("," + str(benchmarkDO.getAllNumberOfVerticesResponse()).replace("[","").replace("]","").replace(",","/").replace(" ",""))
                        edgeCountDiff = []

                        for edgeCount in allNumberOfEdgesResponse:
                            edgeCountDiff.append(abs(benchmarkDO.getGraph().edgeCount() - edgeCount))
                        f.write("," + str(edgeCountDiff).replace("[","").replace("]","").replace(",","/").replace(" ",""))
                        vertexCountDiff = []

                        for vertexCount in benchmarkDO.getAllNumberOfVerticesResponse():
                            vertexCountDiff.append(abs(benchmarkDO.getGraph().vertexCount() - vertexCount))
                        f.write("," + str(vertexCountDiff).replace("[","").replace("]","").replace(",","/").replace(" ",""))
                        allVertexCounts = benchmarkDO.getAllNumberOfVerticesResponse()
                        avgDegrees = []

                        for i in range(len(allNumberOfEdgesResponse)):
                            avgDegrees.append(round(allNumberOfEdgesResponse[i] / allVertexCounts[i],3))
                        f.write("," + str(avgDegrees).replace("[","").replace("]","").replace(",","/").replace(" ",""))
                        sparseness = []

                        for edgeCount in allNumberOfEdgesResponse:
                            sparseness.append(round(edgeCount / benchmarkDO.getGraph().edgeCount(),3))
                        f.write("," + str(sparseness).replace("[","").replace("]","").replace(",","/").replace(" ",""))
                        f.write("," + "0" + "\n")

            except Exception as inst:
                print(type(inst))
                print(inst)

            self._visualisationControl()

        self.task = None

    def abortTask(self):
        self.task.cancel()

    def runJob(self, _task):
        # todo: pass authId to client
        #authId = self.settings.value("ogdfplugin/authId")

        for benchmarkDO in self.benchmarkDOs:
            requestKey = benchmarkDO.algorithm
            request = parserManager.getRequestParser(requestKey)
            request.resetData()

            for key in benchmarkDO.parameters:
                fieldData = benchmarkDO.parameters[key]
                request.setFieldData(key, fieldData)

            for _ in range(self.view.getExecutions(benchmarkDO.algorithm)):
                try:
                    with Client(helper.getHost(), helper.getPort(), tlsOption=helper.getTlsOption()) as client:
                        client.sendJobRequest(request)
                except (NetworkClientError, ParseError, ServerError) as error:
                    return "Network Error: " + str(error)

                status = "waiting"
                counter = 0
                while status != "success":
                    if status == "failed":
                        return "Execution failed"
                    if self.task is not None and self.task.isCanceled():
                        return
                    try:
                        with Client(helper.getHost(), helper.getPort(), tlsOption=helper.getTlsOption()) as client:
                            if counter == 0:
                                time.sleep(0.5)
                                counter+=1
                            else:
                                time.sleep(1)
                            states = client.getJobStatus()
                            jobState = list(states.values())[-1]
                            jobId = jobState.jobId
                            job = statusManager.getJobState(jobId)

                            status = self.STATUS_TEXTS.get(job.status, "status not supported")

                    except (NetworkClientError, ParseError, ServerError) as error:
                        return "Network Error: " + str(error)
                try:
                    with Client(helper.getHost(), helper.getPort(), tlsOption=helper.getTlsOption()) as client:
                        response = client.getJobResult(job.jobId)
                        benchmarkDO.addServerResponse(response)
                        benchmarkDO.setResponseGraph(response.getGraph())
                        benchmarkDO.setRuntime(statusManager.getJobState(jobId).ogdfRuntime)
                except (NetworkClientError, ParseError, ServerError) as error:
                    return "Network Error: " + str(error)

            self.task.setProgress(self.task.progress() + 100/len(self.benchmarkDOs))

        self.doWrapper = BenchmarkDataObjWrapper(self.benchmarkDOs)
