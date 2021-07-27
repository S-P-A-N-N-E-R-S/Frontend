from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
from .ExtGraph import ExtGraph
from .AdvancedCostCalculator import AdvancedCostCalculator
from .QgsGraphLayer import QgsGraphLayer
import random
from qgis import processing
import math
import re
from ..lib.kdtree import kdtree


class GraphBuilder:
    """
    The GraphBuilder offers the possibility to build different graphs in QGIS. Define the desired graph
    by setting options and layers before calling the makeGraph method.

    Options:
        - connectionType: None, Complete, Nearest neighbor, ClusterComplete, ClusterNN, DistanceNN
        - neighborNumber: int
        - distance: float (euclidean distance)
        - nnAllowDoubleEdges": True, False
        - clusterNumber": int
        - edgeDirection: Undirected, Directed (do not use undirected with Nearest neighbor connectionType)
        - distanceStrategy: Euclidean, Manhattan, Geodesic, Advanced
        - createGraphAsLayers: False, True
        - createRandomGraph: False, True
        - usePolygonsAsForbidden: False, True

    Random options:
        - numberOfVertices: int
        - area: Area of the globe you want the random Graph to be in. Can be one of the specified countries or user defined
        

    """    
    def __init__(self):
        """
        Constructor:
        Initial setting for the GraphBuilder. If no additional options or layers are set, a random
        graph with a nearest neighbor connection is generated.
        """
        self.graph = ExtGraph()
        self.vLayer = QgsVectorLayer()
        self.rLayers = []
        self.forbiddenAreas = QgsVectorLayer()       
        self.additionalPointLayer = QgsVectorLayer()
        self.costFunctions = []
        self.rasterBands = []
        self.polygonsForCostFunction = QgsVectorLayer()
        self.kdTree = None
        self.layerWithClusterIDS = None
        # is set if graph builder is running as task
        self.task = None

        self.__options = {
            "connectionType": "Nearest neighbor",            
            "neighborNumber": 2,
            "distance": 0.3,
            "nnAllowDoubleEdges": False,
            "clusterNumber": 5,
            "edgeDirection": "Directed",
            "distanceStrategy": "Euclidean",
            "useRasterData": False,
            "createGraphAsLayers": True,
            "createRandomGraph": True,          
            "usePolygonsAsForbidden": False,
            "useAdditionalPoints": False
        }

        self.__randomOptions = {
            "numberOfVertices": 100,
            "area": "Germany"
        }

    def setPolygonsForCostFunction(self, vectorLayer):
        if vectorLayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise TypeError("Not a polygon geometry")
        
        self.__options["usePolygonsInCostFunction"] = True
        self.polygonsForCostFunction = vectorLayer
    
    def setForbiddenAreas(self, vectorLayer):
        """
        All edges crossing the polygon will be deleted from the graph
        
        :type vectorLayer: QgsVectorLayer containing polygons
        """
        if vectorLayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise TypeError("Not a polygon geometry")
        
        self.__options["usePolygonsAsForbidden"] = True
        self.forbiddenAreas = vectorLayer

    def setAdditionalPointLayer(self, vectorLayer):
        """
        Additional points to a given line layer. The points will be added in addition to the
        network generated for the line layer and connected to the nearest point

        :type vectorLayer: QgsVectorLayer containing points
        """
        if vectorLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point geometry")

        self.__options["useAdditionalPoints"] = True
        self.additionalPointLayer = vectorLayer

    def setVectorLayer(self, vectorLayer):
        """
        Set the basis vector layer for the graph creation.

        :type vectorLayer: QgsVectorLayer containing lines or points
        """
        if vectorLayer.geometryType() != QgsWkbTypes.LineGeometry and vectorLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point or line geometry")

        self.__options["createRandomGraph"] = False
        self.vLayer = vectorLayer    

    def setRasterLayer(self, rasterLayer, band = 1):
        """
        Set raster data to be used in the AdvancedCostCalculator class.

        :type QgsRasterLayer
        """
        self.__options["useRasterData"] = True
        self.rasterBands.append(band)
        self.rLayers.append(rasterLayer)

    def addCostFunction(self, function):
        """
        Set the cost function for an advanced distance strategy. Returns if the
        function has a valid format and the function is set.

        :type function: String
        :return Boolean
        """       
        self.__options["distanceStrategy"] = "Advanced"
        function = self.__replaceBrackets(function)                
        syntaxCheckResult = self.syntaxCheck(function, self.vLayer.fields())        
        if syntaxCheckResult == "Valid function":
            self.costFunctions.append(function)
            
        return syntaxCheckResult
    
    def __replaceBrackets(self,function):
       # replace if brackets with []
        found = True
        while(found):
            found = False    
            index =  function.find("if(")
            if index != -1:
                found = True
                function = function[0:index] + function[index:].replace(")","]",1)
                function = function.replace("if(","if[",1)
         
        # same for random 
        found = True
        while(found):
            found = False    
            index =  function.find("random(")
            if index != -1:
                found = True
                function = function[0:index] + function[index:].replace(")","]",1)
                function = function.replace("random(","random[",1) 
          
        # replace math brackets      
        found = True
        while(found):
            found = False    
            regex = re.compile(r'math.[a-z]+\(')            
            res = regex.search(function)            
            if res != None:
                index = res.start()                                      
                found = True                
                function = function[0:index] + function[index:].replace(")","]",1)                              
                function = function[0:index] + function[index:].replace("(","[",1)
        
        return function 
    
    @staticmethod                   
    def syntaxCheck(function, fields):
        costFunction = function.replace(" ", "").replace('"', '').replace("(","").replace(")","")
        formulaParts = re.split("\+|-|\*|/", costFunction)
        possibleMetrics = ["euclidean", "manhattan", "geodesic"]
        possibleRasterAnalysis = ["sum", "mean", "median", "min", "max", "variance",
                                  "standDev", "gradientSum", "gradientMin", "gradientMax"]
               
        # check parentheses
        openList = ["[","("]
        closeList = ["]",")"]
        stack = []
        for i in function:
            if i in openList:
                stack.append(i)
            elif i in closeList:
                pos = closeList.index(i)
                if((len(stack)>0) and openList[pos] == stack[len(stack)-1]):
                    stack.pop()
                else:
                    return "Unbalanced parentheses"    
        if len(stack) != 0:
            return "Unbalanced parentheses"
               
        # check no operation in if/math/random construct
        operatorRegex = re.compile(r'\+|-|\*|/')                           
        for i in range(len(function)):
            c = function[i]
            if c == "[":
                endOfBracket = 0
                rasterBracket = False
                for j in range(i,len(function)):
                    if function[j] == "[":
                        rasterBracket = True
                    elif function[j] == "]" and rasterBracket:
                        rasterBracket = False    
                    elif function[j] == "]" and not rasterBracket:                       
                        endOfBracket = j   
                        break
                                                        
                res =  operatorRegex.search(function[i:endOfBracket])
                if res != None:
                    return "Operator inside inner function" 
                
                res = function[i:endOfBracket].find("math.")
                if res != -1:
                    return "Math function inside inner function"

        # check operands
        for i in range(len(formulaParts)):
            var = formulaParts[i]
            if not (var in possibleMetrics or var.isnumeric() or "." in var or "if" in var or "field:" in var or "math." in var or "raster[" in var or "random[" in var):
                return "Invalid operand"

            if "raster[" in var:
                analysisType = re.split("<|>|,|\)", var.split("]:")[1])[0]                
                if not analysisType in possibleRasterAnalysis:
                    return "Invalid raster analysis"                       
        
            # check fields
            possibleFields = []
            for field in fields:
                possibleFields.append(field.name())
                
            if "field:" in var:
                fieldName= re.split("<|>|,|\)", var.split("field:")[1])[0]  
                if not fieldName in possibleFields:
                    return "Invalid field name"
                               
        return "Valid function"
    
    def getCostFunction(self, index):
        return self.costFunctions[index]

    def setOption(self, optionType, value):
        if not optionType in self.__options:
            raise KeyError("Option not found")
        self.__options[optionType] = value
    
    def setRandomOption(self, optionType, value):
        if not optionType in self.__randomOptions:
            raise KeyError("Option not found")
        self.__randomOptions[optionType] = value        
    
    def __createRandomVertices(self):
        for i in range(self.__randomOptions["numberOfVertices"]):
            if self.task is not None and self.task.isCanceled():
                break
            if self.__randomOptions["area"] == "Germany":
                self.graph.addVertex(QgsPointXY(random.uniform(6.803,13.480), random.uniform(47.420,55.000)))
            elif self.__randomOptions["area"] == "France":
                self.graph.addVertex(QgsPointXY(random.uniform(-3.163,6.426), random.uniform(43.830,50.055)))
            elif self.__randomOptions["area"] == "Osnabrueck":
                self.graph.addVertex(QgsPointXY(random.uniform(8.01050,8.09776), random.uniform(52.24311,52.30802)))
            elif self.__randomOptions["area"] == "United States":
                self.graph.addVertex(QgsPointXY(random.uniform(-122.892,-74.157), random.uniform(33.725,46.052)))
            elif self.__randomOptions["area"] == "Rome":
                self.graph.addVertex(QgsPointXY(random.uniform(12.40009,12.57946), random.uniform(41.83013,41.97905)))
            elif self.__randomOptions["area"] == "Australia":
                self.graph.addVertex(QgsPointXY(random.uniform(115.157,150.167), random.uniform(-37.211,-14.210)))
            elif isinstance(self.__randomOptions["area"], tuple):
                rectangleExtent, _ = self.__randomOptions["area"]
                self.graph.addVertex(QgsPointXY(random.uniform(rectangleExtent.xMinimum(), rectangleExtent.xMaximum()),
                                                random.uniform(rectangleExtent.yMinimum(), rectangleExtent.yMaximum())))
                
    def __createVerticesForPoints(self):
        for feat in self.vLayer.getFeatures():
            if self.task is not None and self.task.isCanceled():
                break
            geom = feat.geometry()
            self.graph.addVertex(geom.asPoint())
            
    def __createComplete(self):
        for i in range(self.graph.vertexCount()-1):
            for j in range(i+1, self.graph.vertexCount()):
                if self.task is not None and self.task.isCanceled():
                    return
                self.graph.addEdge(i, j)

    def __createNearestNeighbor(self):      
        points = []
        for i in range(self.graph.vertexCount()):
            point = self.graph.vertex(i).point()
            points.append([point.x(),point.y(),i])

        self.kdTree = kdtree.create(points)

        for i in range(self.graph.vertexCount()):
            if self.task is not None and self.task.isCanceled():
                return
            
            point = self.graph.vertex(i).point()
            
            if self.__options["connectionType"] == "Nearest neighbor":
                listOfNeighbors = self.kdTree.search_knn([point.x(),point.y(),i],self.__options["neighborNumber"]+1)
            elif self.__options["connectionType"] == "DistanceNN":
                listOfNeighbors = self.kdTree.search_nn_dist([point.x(),point.y(),i], pow(self.__options["distance"],2))    
            
            for j in range(1,len(listOfNeighbors)):
                if self.__options["connectionType"] == "Nearest neighbor":
                    neighborPoint = listOfNeighbors[j][0].data
                elif self.__options["connectionType"] == "DistanceNN":    
                    neighborPoint = listOfNeighbors[j]
                self.graph.addEdge(i,neighborPoint[2])
            
            if self.__options["nnAllowDoubleEdges"] == False:
                self.kdTree = self.kdTree.remove([point.x(),point.y(),i])

    def __createCluster(self):
        # if a random graph was created the vLayer has to be set manually
        if self.__options["createRandomGraph"] == True:

            self.vLayer = QgsVectorLayer("Point", "TempVertexLayer", "memory")
            dpVerticeLayer = self.vLayer.dataProvider()

            for i in range(self.graph.vertexCount()):
                newFeature = QgsFeature()
                newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))
                dpVerticeLayer.addFeature(newFeature)
            
        # change so you only go throw the features ones and store in 2d array
        result = processing.run("qgis:kmeansclustering", {"INPUT":self.vLayer, "CLUSTERS": self.__options["clusterNumber"], "OUTPUT": "memory:"})
        self.layerWithClusterIDS = result["OUTPUT"]

        for cluster in range(self.__options["clusterNumber"]):
            allPointsInCluster = []
            featureCounter = 0
            for feature in self.layerWithClusterIDS.getFeatures(): 
                if feature["CLUSTER_ID"] == cluster:                             
                    allPointsInCluster.append(featureCounter)
                featureCounter+=1
            
            if self.__options["connectionType"] == "ClusterNN":
                points = []
                for i in range(len(allPointsInCluster)):
                    point = self.graph.vertex(allPointsInCluster[i]).point()
                    points.append([point.x(),point.y(),allPointsInCluster[i]])

                # build kd tree
                self.kdTree = kdtree.create(points)
                count = 0
                for i in range(len(allPointsInCluster)):
                    if self.task is not None and self.task.isCanceled():
                        return
                    if len(allPointsInCluster)>1:
                        vertex = self.graph.vertex(allPointsInCluster[i]).point()
                        nearestPoints = self.kdTree.search_knn([vertex.x(),vertex.y(), allPointsInCluster[i]],self.__options["neighborNumber"]+1)
                        for t in range(1,len(nearestPoints)):
                            neighborPoint = nearestPoints[t][0].data
                            self.graph.addEdge(allPointsInCluster[i],neighborPoint[2])
                        if self.__options["nnAllowDoubleEdges"] == False:
                            self.kdTree = self.kdTree.remove([vertex.x(),vertex.y(), allPointsInCluster[i]])

            elif self.__options["connectionType"] == "ClusterComplete":
                for i in range(len(allPointsInCluster)-1):
                    if self.task is not None and self.task.isCanceled():
                        return
                    for j in range(i+1,len(allPointsInCluster)):
                         self.graph.addEdge(allPointsInCluster[i],allPointsInCluster[j])

    def __createDistanceNN(self):
        points = []
        for i in range(self.graph.vertexCount()):
            point = self.graph.vertex(i).point()
            points.append([point.x(),point.y(),i])

        self.kdTree = kdtree.create(points)

        for i in range(self.graph.vertexCount()):
            if self.task is not None and self.task.isCanceled():
                return
            point = self.graph.vertex(i).point()
            listOfNeighbors = self.kdTree.search_nn_dist([point.x(),point.y(),i], pow(self.__options["distance"],2))
            
            for j in range(1,len(listOfNeighbors)):
                neighborPoint = listOfNeighbors[j]
                self.graph.addEdge(i,neighborPoint[2])
            
            if self.__options["nnAllowDoubleEdges"] == False:
                self.kdTree = self.kdTree.remove([point.x(),point.y(),i])

    def __createGraphForLineGeometry(self):
        """
        Method is called if the input consists of lines. Every start and end of
        very edge is a vertex in the graph and an edge is added between them.
        """
        # get all the lines and set end nodes as vertices and connections as edges
        for feature in self.vLayer.getFeatures():
            if self.task is not None and self.task.isCanceled():
                return
            geom = feature.geometry()
            if QgsWkbTypes.isMultiType(geom.wkbType()):
                for part in geom.asMultiPolyline():
                    for i in range(len(part)):
                        addedID = self.graph.addVertex(part[i]) 
                        if i!=0:                               
                            self.graph.addEdge(addedID-1, addedID)
                            self.graph.featureMatchings.append(feature)

            else:                        
                vertices = geom.asPolyline()                       
                for i in range(len(vertices)-1):
                    startVertex = vertices[i]
                    endVertex = vertices[i+1]
                    id1 = self.graph.addVertex(startVertex)
                    id2 = self.graph.addVertex(endVertex)                    
                    self.graph.addEdge(id1, id2)
                    self.graph.featureMatchings.append(feature)

        # add points and connection to network if additional points are given
        # use kd tree to get the nearest point
        if self.__options["useAdditionalPoints"] == True:
            points = []
            for i in range(self.graph.vertexCount()):
                point = self.graph.vertex(i).point()
                points.append([point.x(),point.y(),i])

            # build kd tree
            self.kdTree = kdtree.create(points)
            counter = 0
            for feature in self.additionalPointLayer.getFeatures():
                if self.task is not None and self.task.isCanceled():
                    return
                counter+=1
                geom = feature.geometry()
                pointID = self.graph.addVertex(geom.asPoint())
                nearestPointID = self.kdTree.search_knn([self.graph.vertex(pointID).point().x(),self.graph.vertex(pointID).point().y(), counter],2)[1][0].data[2]
                self.graph.addEdge(pointID, nearestPointID)

    def __removeIntersectingEdges(self):
        # create the current edge layer
        currentEdges = self.createEdgeLayer(False,True)
        # call QGIS tool to extract all the edges which cross the polygon
        result1 = processing.run("native:extractbylocation", {"INPUT": currentEdges, "PREDICATE": 2, "INTERSECT": self.forbiddenAreas, "OUTPUT": "memory:"})
        layerWithDelEdges = result1["OUTPUT"]
        
        # copy the result of the QGIS tool into a new graph
        newGraph = ExtGraph()
        for feature in layerWithDelEdges.getFeatures():
            if self.task is not None and self.task.isCanceled():
                return
            geom = feature.geometry()
                                            
            vertices = geom.asPolyline()                       
            for i in range(len(vertices)-1):
                startVertex = vertices[i]
                endVertex = vertices[i+1]
                id1 = newGraph.addVertex(startVertex)
                id2 = newGraph.addVertex(endVertex)                    
                newGraph.addEdge(id1, id2)
        
        newGraph.setDistanceStrategy(self.graph.distanceStrategy)
        self.graph = newGraph

    def createVertexLayer(self, addToCanvas):
        """
        Method creates a QgsVectorLayer containing points. The points are the vertices of the graph.

        :type addToCanvas: Boolean
        :return QgsVectorLayer
        """
        if self.task is not None and self.task.isCanceled():
            return
        graphLayerVertices = QgsVectorLayer("Point", "GraphVertices", "memory")
        dpVerticeLayer = graphLayerVertices.dataProvider()
        dpVerticeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("X", QVariant.Double), QgsField("Y", QVariant.Double)])
        graphLayerVertices.updateFields()  
        
        if self.__options["createRandomGraph"] == False:            
            graphLayerVertices.setCrs(self.vLayer.crs())  
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayerVertices.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayerVertices.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    
        #add the vertices and edges to the layers
        for i in range(self.graph.vertexCount()):
            if self.task is not None and self.task.isCanceled():
                return
            newFeature = QgsFeature()
            newFeature.setGeometry(QgsGeometry.fromPointXY(self.graph.vertex(i).point()))  
            newFeature.setAttributes([i, self.graph.vertex(i).point().x(), self.graph.vertex(i).point().y()])
            dpVerticeLayer.addFeature(newFeature)
            
            
        if addToCanvas == True:
            QgsProject.instance().addMapLayer(graphLayerVertices)

        return graphLayerVertices

    def createEdgeLayer(self, addToCanvas, skipEdgeCosts=False):
        """
        Method creates a QgsVectorLayer containing lines. The lines are the edges of the graph. The weights are
        visible by creating labels.

        :type addToCanvas: Boolean
        :return QgsVectorLayer
        """
        if self.task is not None and self.task.isCanceled():
            return
        graphLayerEdges = QgsVectorLayer("LineString", "GraphEdges", "memory")
        dpEdgeLayer = graphLayerEdges.dataProvider()
        dpEdgeLayer.addAttributes([QgsField("ID", QVariant.Int), QgsField("fromVertex",QVariant.Double), QgsField("toVertex",QVariant.Double),QgsField("weight", QVariant.Double)])
        graphLayerEdges.updateFields() 

        if self.__options["createRandomGraph"] == False:
            graphLayerEdges.setCrs(self.vLayer.crs())  
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayerEdges.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayerEdges.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        for i in range(self.graph.edgeCount()):
            if self.task is not None and self.task.isCanceled():
                return
            newFeature = QgsFeature()
            fromVertex = self.graph.vertex(self.graph.edge(i).fromVertex()).point()
            toVertex = self.graph.vertex(self.graph.edge(i).toVertex()).point()
            newFeature.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))
            if skipEdgeCosts == True:
                newFeature.setAttributes([i, self.graph.edge(i).fromVertex(), self.graph.edge(i).toVertex(), 0])
            else:
                newFeature.setAttributes([i, self.graph.edge(i).fromVertex(), self.graph.edge(i).toVertex(), self.graph.costOfEdge(i)])

            dpEdgeLayer.addFeature(newFeature)

        if addToCanvas == True:
            layer_settings  = QgsPalLayerSettings()
            text_format = QgsTextFormat()
    
            text_format.setFont(QFont("Arial", 12))
            text_format.setSize(12)
    
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(0.1)
            buffer_settings.setColor(QColor("black"))
    
            text_format.setBuffer(buffer_settings)
            layer_settings.setFormat(text_format)
    
            layer_settings.fieldName = "weight"
            layer_settings.placement = 2
    
            layer_settings.enabled = True
    
            layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
            graphLayerEdges.setLabelsEnabled(True)
            graphLayerEdges.setLabeling(layer_settings)
            graphLayerEdges.triggerRepaint()
            QgsProject.instance().addMapLayer(graphLayerEdges)
       
        # make sure output is valid
        result = processing.run("qgis:checkvalidity", {"INPUT_LAYER": graphLayerEdges, "METHOD": 1, "VALID_OUTPUT": "memory:"})
        graphLayerEdges = result["VALID_OUTPUT"]

        return graphLayerEdges

    def createGraphLayer(self, addToCanvas):
        """
        Create graph layer from created graph
        :param addToCanvas:
        :return:
        """
        graphLayer = QgsGraphLayer()

        if self.__options["createRandomGraph"] == False:
            graphLayer.setCrs(self.vLayer.crs())
        else:
            if isinstance(self.__randomOptions["area"], tuple):
                _, inputCRS = self.__randomOptions["area"]
                graphLayer.setCrs(QgsCoordinateReferenceSystem(inputCRS))
            else:
                graphLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

        graphLayer.setGraph(self.graph)

        if addToCanvas == True:
            QgsProject.instance().addMapLayer(graphLayer)

        return graphLayer

    def getNearestVertex(self, vertexIndex):
        vertex = self.graph.vertex(vertexIndex).point()
        currentVertex = self.graph.vertex(0).point()
        shortestDist = math.sqrt(pow(vertex.x()-currentVertex.x(),2) + pow(vertex.y()-currentVertex.y(),2)) 
        shortestIndex = []
        for v in range(self.graph.vertexCount()):
            if v != vertexIndex:
                currentVertex = self.graph.vertex(v).point()
                currentDist = math.sqrt(pow(vertex.x()-currentVertex.x(),2) + pow(vertex.y()-currentVertex.y(),2)) 
                if currentDist < shortestDist:
                    shortestDist = currentDist
                    shortestIndex = v
                     
        return shortestIndex
        
    def addVertices(self, vertexLayer):
        """
        Add multiple points by using a vectorLayer
        
        :type vertexLayer: QgsVectorLayer containing points
        """
        if self.vLayer.geometryType() != QgsWkbTypes.PointGeometry:
            raise TypeError("Not a point geometry")
        for feat in vertexLayer.getFeatures():            
            geom = feat.geometry()
            self.graph.addVertexWithEdges([geom.asPoint().x(),geom.asPoint().y()])

    def getGraph(self):
        return self.graph   

    def setGraph(self, graph):
        self.graph = graph  
         
    def makeGraph(self):
        """
        If this method is called the creation of the graph starts. The set options are read and
        methods are called accordingly.

        :return ExtGraph
        """
        self.graph = ExtGraph()
        # set distance strategy
        self.graph.setDistanceStrategy(self.__options["distanceStrategy"])
        self.graph.setConnectionType(self.__options["connectionType"])
        self.graph.setGraphBuilderInformation(self.__options["neighborNumber"], self.__options["edgeDirection"],
                                            self.__options["clusterNumber"], self.__options["nnAllowDoubleEdges"],
                                            self.__options["distance"])

        if self.__options["createRandomGraph"] == True:
            self.__createRandomVertices()
        else:          
            if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry:
                self.__createVerticesForPoints()

        # create vertices and edges
        if self.vLayer.geometryType() == QgsWkbTypes.PointGeometry or self.__options["createRandomGraph"] == True:                          
            if self.__options["connectionType"] == "Complete":
                self.__createComplete()
            elif self.__options["connectionType"] == "Nearest neighbor" or self.__options["connectionType"] == "DistanceNN":
                self.__createNearestNeighbor()
            elif self.__options["connectionType"] == "ClusterComplete" or self.__options["connectionType"] == "ClusterNN":
                self.__createCluster()
                          
        # user gives lines as input
        elif self.vLayer.geometryType() == QgsWkbTypes.LineGeometry:      
            self.__createGraphForLineGeometry()

        # add every edge again in opposite direction if its an undirected graph
        if self.__options["edgeDirection"] == "Undirected":
            if self.task is not None and self.task.isCanceled():
                return
            eCount = self.graph.edgeCount()
            for i in range(eCount):
                edge = self.graph.edge(i)
                self.graph.addEdge(edge.toVertex(), edge.fromVertex())  

        # remove edges that cross the polygons
        if self.__options["usePolygonsAsForbidden"] == True:
            self.__removeIntersectingEdges()

        # call AdvancedCostCalculations methods
        if self.__options["distanceStrategy"] == "Advanced":
            # create AdvancedCostCalculator object with the necessary parameters
            costCalculator = AdvancedCostCalculator(self.rLayers, self.vLayer, self.graph, self.polygonsForCostFunction, self.__options["usePolygonsAsForbidden"], self.rasterBands)

            # call the setEdgeCosts method of the AdvancedCostCalculator for every defined cost function
            # the costCalculator returns a ExtGraph where costs are assigned multiple weights if more then one cost function is defined
            for func in self.costFunctions:
                self.graph = costCalculator.setEdgeCosts(func)

        # create the layers for QGIS
        if self.__options["createGraphAsLayers"] == True:
            self.createVertexLayer(True)
            self.createEdgeLayer(True)

        return self.graph

    def makeGraphTask(self, task, graphLayer, graphName=""):
        """
        Task function of makeGraph() to build a graph in the background
        :param task: own QgsTask instance
        :return:
        """
        QgsMessageLog.logMessage('Started task {}'.format(task.description()), level=Qgis.Info)
        # save task in instance for usage in other methods
        self.task = task

        # build graph
        graph = self.makeGraph()

        # set graph to graph layer
        graphLayer.setGraph(self.graph)

        if self.task.isCanceled():
            # if task is canceled by User or QGIS
            QgsMessageLog.logMessage('Task {} cancelled'.format(task.description()), level=Qgis.Info)
            self.task = None
            return None
        else:
            QgsMessageLog.logMessage("Make graph finished", level=Qgis.Info)
            self.task = None
            return {"graph": graph, "graphLayer": graphLayer, "graphName": graphName}
