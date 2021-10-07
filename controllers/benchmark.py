import os

from qgis.core import QgsSettings, QgsApplication, QgsProject

from .base import BaseController
from .. import mainPlugin
from ..exceptions import FieldRequiredError
from .. import helperFunctions as helper
from ..network import parserManager

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError


class BenchmarkController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OGDFAnalysisView
        """
        super().__init__(view)

        self.settings = QgsSettings()
        self.authManager = QgsApplication.authManager()

        # add available analysis
        for requestKey, request in parserManager.getRequestParsers().items():
            self.view.addOGDFAlg(request.name)
          

    def runJob(self):
        # todo: pass authId to client
        print("RUN JOB START")
        
        authId = self.settings.value("ogdfplugin/authId")
        
        # create and get BenchmarkData object 
        benchmarksDOs = self.view.ogdfBenchmarkWidget.getBenchmarkDataObjects()  
        
        for benchmarkDO in benchmarksDOs:
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
            """    
            try:
                with Client(helper.getHost(), helper.getPort()) as client:
                    client.sendJobRequest(request)
                    self.view.showSuccess("Job started!")
        
            except (NetworkClientError, ParseError) as error:
                self.view.showError(str(error), self.tr("Network Error"))
        
            """
