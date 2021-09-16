from qgis.core import *
from AStarC import *
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
		minRasterValue = (self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).minimumValue
		meanRasterValue = (self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).mean
			
		#----------------------------------	
		
		self.aStarCObject = AStarC(readBand.ReadAsArray(), heuristicIndex, minRasterValue, meanRasterValue)	
	
		#----------------------------------
		
	
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
	    
	    #----------------------------------
	    
	    return self.aStarCObject.shortestPath(startPointRow,startPointCol, endPointRow, endPointCol)
	    
	    #----------------------------------
	 
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
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
