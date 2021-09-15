from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from osgeo import gdal
import numpy as np
import math
import heapq
import sys

class AStarOnRasterData:
	
	def __init__(self, rLayer, band, sourceCrs, heuristicIndex, createResultAsMatrix = False):
		self.createResultAsMatrix = createResultAsMatrix
		self.heuristicIndex = heuristicIndex
		ds = gdal.Open(rLayer.source())
		readBand = ds.GetRasterBand(band)
		self.bandID = band
		self.rLayer = rLayer
		self.sourceCrs = sourceCrs
		self.destCrs = self.rLayer.crs()
		self.tr = QgsCoordinateTransform(self.sourceCrs, self.destCrs, QgsProject.instance())
		
		self.cols = ds.RasterXSize
		self.rows = ds.RasterYSize
		self.transform = ds.GetGeoTransform()
		self.xOrigin = self.transform[0]
		self.yOrigin = self.transform[3]
		self.pixelWidth = self.transform[1]
		self.pixelHeight = -self.transform[5]
	
		self.matrix = np.array(readBand.ReadAsArray())
		
		self.matrixRowSize = self.matrix.shape[0]
		self.matrixColSize = self.matrix.shape[1]
		if createResultAsMatrix == True:
			self.shortestPathMatrix = np.zeros((self.matrixRowSize, self.matrixColSize))
		self.predMatrix = None
		
		self.pixelWeights = None
		self.dictionary = {}
	
	def getShortestPathWeight(self, startPoint, endPoint):	
	    # transform coordinates
	    startPointTransform = self.tr.transform(startPoint)
	    endPointTransform = self.tr.transform(endPoint)
	    
	    self.predMatrix = np.empty((self.matrixRowSize, self.matrixColSize), dtype=object)
	    
	    # get position of points in matrix   
	    startPointCol = int((startPointTransform.x() - self.xOrigin) / self.pixelWidth)
	    startPointRow = int((self.yOrigin - startPointTransform.y()) / self.pixelHeight)
	    endPointCol = int((endPointTransform.x() - self.xOrigin) / self.pixelWidth)
	    endPointRow = int((self.yOrigin - endPointTransform.y()) / self.pixelHeight)
	    	      	   
	    dimensions = (self.matrixRowSize, self.matrixColSize)
	    # check startPoint and endPoint are inside the raster, if not return max value
	    if startPointCol > self.matrixColSize or startPointCol < 0 or startPointRow < 0 or startPointRow > self.matrixRowSize:
	    	return [sys.maxsize]
	    if endPointCol > self.matrixColSize or endPointCol < 0 or endPointRow < 0 or endPointRow > self.matrixRowSize:
	    	return [sys.maxsize]
	    
	    pq = []
	    heapq.heappush(pq, (0, (startPointRow,startPointCol)))
	    self.pixelWeights = np.full(dimensions,np.inf)    	     
	    
	    self.pixelWeights[startPointRow][startPointCol] = 0
	    while len(pq) > 0:
	    	popResult = heapq.heappop(pq)	    		    	
	    	currentWeight = popResult[0]
	    	current = popResult[1]	    		    	
	    	if current == (endPointRow,endPointCol):	  		  		
    			shortestPathWeights = []
	    		u = (endPointRow,endPointCol)
	    		while u != None:
	    			if self.createResultAsMatrix == True:
	    				self.shortestPathMatrix[u[0]][u[1]] = 100	    			
	    			shortestPathWeights.append(self.matrix[u[0]][u[1]])
	    			u = self.predMatrix[u[0]][u[1]]	    			
	    		    			    		
	    		if not np.isinf(self.pixelWeights[current[0]][current[1]]):
	    			return shortestPathWeights
	    			#return str(self.pixelWeights[current[0]][current[1]])
	    		else:
	    			return str(sys.maxsize)
	    		if currentWeight - self.heuristic(current, (endPointRow,endPointCol)) > self.pixelWeights[current[0]][current[1]]:
		    		continue
	    	
	    	# check the neighbor pixels of current
	    	for neighbor in self.getNeighborIndices(current[0], current[1]):  		
	    		newDistance = self.pixelWeights[current[0]][current[1]] + self.matrix[current[0]][current[1]]		
	    		# check that the neighbor is not out of raster bounds
	    		if neighbor[0] > 0 and neighbor[1] > 0 and neighbor[0] < self.matrixRowSize and neighbor[1] < self.matrixColSize:
		    		if newDistance < self.pixelWeights[neighbor[0]][neighbor[1]]:	
	    			
		    			self.predMatrix[neighbor[0]][neighbor[1]] = (current[0], current[1])
		    			if self.createResultAsMatrix == True:
			    			if not self.shortestPathMatrix[current[0]][current[1]] == 100:
			    				self.shortestPathMatrix[current[0]][current[1]] = 50   			   			
		    			
		    			self.pixelWeights[neighbor[0]][neighbor[1]] = newDistance	    			
		    			heapq.heappush(pq,(self.pixelWeights[neighbor[0]][neighbor[1]] + self.heuristic(neighbor, (endPointRow,endPointCol)), neighbor))
    			    	
	    return [sys.maxsize]
	   
		
	def getNeighborIndices(self, i, j):
		# return list of neighbor indices		
		bl = (i-1,j-1)
		bm = (i-1,j)
		br = (i-1,j+1)
		ml = (i,j-1)
		mr = (i,j+1)
		tl = (i+1,j-1)
		tm = (i+1,j)
		tr = (i+1,j+1)
		
		return [bl,bm,br,ml,mr,tl,tm,tr]
	 
	def heuristic(self, point1, point2): 				
		# calculate heuristic value depended on the defined heuristic index
		if self.heuristicIndex == 0:
			minRasterValue = (self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).minimumValue
			heurValue = max(abs(point2[0]-point1[0]), abs(point2[1]-point1[1])) * minRasterValue
		else:
			meanRasterValue = (self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).mean
			if self.heuristicIndex == 1:
				factor = (meanRasterValue/4)
			elif self.heuristicIndex == 2:
				factor = (meanRasterValue/2)
			elif self.heuristicIndex == 3:
				factor = (meanRasterValue/1.5)
			elif self.heuristicIndex == 4:
				factor = (meanRasterValue/1.25)
			elif self.heuristicIndex == 5:
				factor = meanRasterValue				
						
			heurValue = max(abs(point2[0]-point1[0]), abs(point2[1]-point1[1])) * factor
		
		return heurValue
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
