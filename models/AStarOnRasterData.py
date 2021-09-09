from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from osgeo import gdal
import numpy as np
import math
import heapq

class AStarOnRasterData:
	
	#TODO: RESIZE Raster data by checking point extend??
	
	def __init__(self, rLayer, band, sourceCrs):
		ds = gdal.Open(rLayer.source())
		readBand = ds.GetRasterBand(band)
		
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
		pixelHeight = -self.transform[5]
	
		self.matrix = np.array(readBand.ReadAsArray())
		self.matrixRowSize = self.matrix.shape[0]
		self.matrixColSize = self.matrix.shape[1]
		self.pixelWeights = None
		self.dictionary = {}
	
	def getShortestPathWeight(self, startPoint, endPoint, allowNotOptimal = True):	
	    # transform coordinates
	    startPointTransform = self.tr.transform(startPoint)
	    endPointTransform = self.tr.transform(endPoint)
	    
	    # get position of points in matrix   
	    startPointCol = int((startPointTransform.x() - self.xOrigin) / self.pixelWidth)
	    startPointRow = int((self.yOrigin - startPointTransform.y()) / self.pixelWidth)
	    endPointCol = int((endPointTransform.x() - self.xOrigin) / self.pixelWidth)
	    endPointRow = int((self.yOrigin - endPointTransform.y()) / self.pixelWidth)
	    print("CALL")
	    dimensions = (self.matrixRowSize, self.matrixColSize)
	    
	    # check startPoint and endPoint are inside the raster, if not return max value
	    
	    pq = []
	    heapq.heappush(pq, (0, (startPointRow,startPointCol)))
	    self.pixelWeights = np.full(dimensions,np.inf)    	     
	    
	    self.pixelWeights[startPointRow][startPointCol] = 0
	    while len(pq) > 0:
	    	# search runs in O(n)
	    	popResult = heapq.heappop(pq)	    		    	
	    	currentWeight = popResult[0]
	    	current = popResult[1]
	    	
	    	if current == (endPointRow,endPointCol):
	    		if not np.isinf(self.pixelWeights[current[0]][current[1]]):
	    			return str(self.pixelWeights[current[0]][current[1]])
	    		else:
	    			return str(sys.maxsize)
	    	if allowNotOptimal:
		    	if currentWeight - self.heuristic(current, (endPointRow,endPointCol))> self.pixelWeights[current[0]][current[1]]:
		    		continue
	    	else:
	    		if currentWeight > self.pixelWeights[current[0]][current[1]]:
		    		continue
	    	# check the neighbor pixels of current
	    	for neighbor in self.getNeighborIndices(current[0], current[1]):  		
	    		newDistance = self.pixelWeights[current[0]][current[1]] + self.matrix[current[0]][current[1]]		
	    		# check that the neighbor is not out of raster bounds
	    		if neighbor[0] > 0 and neighbor[1] > 0 and neighbor[0] < self.matrixRowSize and neighbor[1] < self.matrixColSize:
		    		if newDistance < self.pixelWeights[neighbor[0]][neighbor[1]]:	
		    			    			   			
		    			self.pixelWeights[neighbor[0]][neighbor[1]] = newDistance
		    			if allowNotOptimal:
		    				heapq.heappush(pq,(self.pixelWeights[neighbor[0]][neighbor[1]] + self.heuristic(neighbor, (endPointRow,endPointCol)), neighbor))
		    			else:
		    				heapq.heappush(pq,(self.pixelWeights[neighbor[0]][neighbor[1]], neighbor)) 				    		
	    		

	    print("Not found")		
	    return str(sys.maxsize)
	   
		
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
		# calculate distance in pixels
		
		euclDist = math.sqrt(pow(point1[0]-point2[0],2) + pow(point1[1]-point2[1],2))
		
		# get average of samples
		return euclDist
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	