#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  <name of author>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from osgeo import gdal
import numpy as np
import math
import heapq
import sys
import random


class AStar:
    def __init__(self, matrix, heuristicIndex, minValue, meanValue, createShortestPathMatrix):
        self.matrix = np.array(matrix)
        self.matrixRowSize = self.matrix.shape[0]
        self.matrixColSize = self.matrix.shape[1]

        self.heuristicIndex = heuristicIndex
        self.minValue = minValue
        self.meanValue = meanValue
        self.createShortestPathMatrix = createShortestPathMatrix
        self.diagonals = 0

        if createShortestPathMatrix:
            self.shortestPathMatrix1 = np.zeros((self.matrixRowSize, self.matrixColSize))
            self.shortestPathMatrix2 = np.zeros((self.matrixRowSize, self.matrixColSize))
            self.shortestPathMatrix3 = np.zeros((self.matrixRowSize, self.matrixColSize))

    def shortestPath(self, x1, y1, x2, y2):
        self.diagonals = 0
        pixelWeights = np.full((self.matrixRowSize, self.matrixColSize), np.inf)
        predMatrix = np.empty((self.matrixRowSize, self.matrixColSize), dtype=tuple)

        randomRed = random.randint(0, 255)
        randomGreen = random.randint(0, 255)
        randomBlue = random.randint(0, 255)

        pixelWeights[x1][y1] = 0

        startPoint = (x1, y1)
        endPoint = (x2, y2)

        pq = []
        heapq.heappush(pq, (0, startPoint))

        while len(pq) > 0:
            popResult = heapq.heappop(pq)
            currentWeight = popResult[0]
            current = popResult[1]
                
            if current == endPoint:
                shortestPathWeights = []
                u = (endPoint[0], endPoint[1])
                currPathPoint = (endPoint[0], endPoint[1])
                while currPathPoint != startPoint:
                    if self.createShortestPathMatrix:
                        self.shortestPathMatrix1[currPathPoint[0]][currPathPoint[1]] = (self.shortestPathMatrix1[currPathPoint[0]][currPathPoint[1]] + randomRed) / 2
                        self.shortestPathMatrix2[currPathPoint[0]][currPathPoint[1]] = (self.shortestPathMatrix2[currPathPoint[0]][currPathPoint[1]] + randomGreen) / 2
                        self.shortestPathMatrix3[currPathPoint[0]][currPathPoint[1]] = (self.shortestPathMatrix3[currPathPoint[0]][currPathPoint[1]] + randomBlue) / 2
                    shortestPathWeights.append(self.matrix[u[0]][u[1]])
                    prevX = u[0]
                    prevY = u[1]
                    u = predMatrix[u[0]][u[1]]
                    if u[0] != prevX and u[1] != prevY:
                        self.diagonals = self.diagonals + 1

                    currPathPoint = (u[0], u[1])
                shortestPathWeights.append(self.matrix[startPoint[0], startPoint[1]])
                if self.createShortestPathMatrix:
                    self.shortestPathMatrix1[startPoint[0]][startPoint[1]] = (self.shortestPathMatrix1[currPathPoint[0]][currPathPoint[1]] + randomRed) / 2
                    self.shortestPathMatrix2[startPoint[0]][startPoint[1]] = (self.shortestPathMatrix2[currPathPoint[0]][currPathPoint[1]] + randomGreen) / 2
                    self.shortestPathMatrix3[startPoint[0]][startPoint[1]] = (self.shortestPathMatrix3[currPathPoint[0]][currPathPoint[1]] + randomBlue) / 2
                return shortestPathWeights
            
            if currentWeight - self._heuristic(current, endPoint) > pixelWeights[current[0]][current[1]]:
                continue
            
            # check the neighbor pixels of current
            nIndexCounter = 0
            for neighbor in self._getNeighborIndices(current[0], current[1]):
                newDistance = pixelWeights[current[0]][current[1]] + self.matrix[current[0]][current[1]]

                # check that the neighbor is not out of raster bounds
                if neighbor[0] > 0 and neighbor[1] > 0 and neighbor[0] < len(self.matrix) and neighbor[1] < len(self.matrix[0]):
                    if newDistance < pixelWeights[neighbor[0]][neighbor[1]]:
                        predMatrix[neighbor[0]][neighbor[1]] = (current[0], current[1])
                        pixelWeights[neighbor[0]][neighbor[1]] = newDistance
                        if self.createShortestPathMatrix:
                            if self.shortestPathMatrix1[current[0]][current[1]] == 0 and self.shortestPathMatrix2[current[0]][current[1]] == 0 and self.shortestPathMatrix3[current[0]][current[1]] == 0:
                                self.shortestPathMatrix1[current[0]][current[1]] = 255
                                self.shortestPathMatrix2[current[0]][current[1]] = 255
                                self.shortestPathMatrix3[current[0]][current[1]] = 255
                        
                        heapq.heappush(pq, (pixelWeights[neighbor[0]][neighbor[1]] + self._heuristic(neighbor, endPoint), neighbor))
                nIndexCounter = nIndexCounter + 1

        return [sys.maxsize]

    def getShortestPathMatrix1(self):
        return self.shortestPathMatrix1

    def getShortestPathMatrix2(self):
        return self.shortestPathMatrix2

    def getShortestPathMatrix3(self):
        return self.shortestPathMatrix3

    def getNumberOfDiagonals(self):
        return self.diagonals

    def _getNeighborIndices(self, i, j):
        # non diagonal
        bm = (i-1, j)
        ml = (i, j-1)
        mr = (i, j+1)
        tm = (i+1, j)

        # diagonal
        bl = (i-1, j-1)
        br = (i-1, j+1)
        tl = (i+1, j-1)
        tr = (i+1, j+1)

        return [bm, ml, mr, tm, bl, br, tl, tr]

    def _heuristic(self, point1, point2):
        factor = 0
        if self.heuristicIndex == 0:
            factor = self.minValue
        else:
            if self.heuristicIndex == 1:
                factor = int(self.meanValue/4)
            elif self.heuristicIndex == 2:
                factor = int(self.meanValue/2)
            elif self.heuristicIndex == 3:
                factor = int(self.meanValue/1.5)
            elif self.heuristicIndex == 4:
                factor = int(self.meanValue/1.25)
            elif self.heuristicIndex == 5:
                factor = int(self.meanValue)
        print(factor)        
        return max(abs(point2[0]-point1[0]), abs(point2[1]-point1[1])) * factor





# class AStarOnRasterData:
#
#     def __init__(self, rLayer, band, sourceCrs, heuristicIndex, createResultAsMatrix = False):
#         self.createResultAsMatrix = createResultAsMatrix
#         self.heuristicIndex = heuristicIndex
#         ds = gdal.Open(rLayer.source())
#         readBand = ds.GetRasterBand(band)
#         self.bandID = band
#         self.rLayer = rLayer
#         self.sourceCrs = sourceCrs
#         self.destCrs = self.rLayer.crs()
#         self.tr = QgsCoordinateTransform(self.sourceCrs, self.destCrs, QgsProject.instance())
#
#         self.cols = ds.RasterXSize
#         self.rows = ds.RasterYSize
#         self.transform = ds.GetGeoTransform()
#         self.xOrigin = self.transform[0]
#         self.yOrigin = self.transform[3]
#         self.pixelWidth = self.transform[1]
#         self.pixelHeight = -self.transform[5]
#
#         self.matrix = np.array(readBand.ReadAsArray())
#
#         self.matrixRowSize = self.matrix.shape[0]
#         self.matrixColSize = self.matrix.shape[1]
#         if createResultAsMatrix == True:
#             self.shortestPathMatrix = np.zeros((self.matrixRowSize, self.matrixColSize))
#         self.predMatrix = None
#
#         self.pixelWeights = None
#         self.dictionary = {}
#
#     def getShortestPathWeight(self, startPoint, endPoint):
#         # transform coordinates
#         startPointTransform = self.tr.transform(startPoint)
#         endPointTransform = self.tr.transform(endPoint)
#
#         self.predMatrix = np.empty((self.matrixRowSize, self.matrixColSize), dtype=object)
#
#         # get position of points in matrix
#         startPointCol = int((startPointTransform.x() - self.xOrigin) / self.pixelWidth)
#         startPointRow = int((self.yOrigin - startPointTransform.y()) / self.pixelHeight)
#         endPointCol = int((endPointTransform.x() - self.xOrigin) / self.pixelWidth)
#         endPointRow = int((self.yOrigin - endPointTransform.y()) / self.pixelHeight)
#
#         dimensions = (self.matrixRowSize, self.matrixColSize)
#         # check startPoint and endPoint are inside the raster, if not return max value
#         if startPointCol > self.matrixColSize or startPointCol < 0 or startPointRow < 0 or startPointRow > self.matrixRowSize:
#             return [sys.maxsize]
#         if endPointCol > self.matrixColSize or endPointCol < 0 or endPointRow < 0 or endPointRow > self.matrixRowSize:
#             return [sys.maxsize]
#
#         pq = []
#         heapq.heappush(pq, (0, (startPointRow,startPointCol)))
#         self.pixelWeights = np.full(dimensions,np.inf)
#
#         self.pixelWeights[startPointRow][startPointCol] = 0
#         while len(pq) > 0:
#             popResult = heapq.heappop(pq)
#             currentWeight = popResult[0]
#             current = popResult[1]
#             if current == (endPointRow,endPointCol):
#                 shortestPathWeights = []
#                 u = (endPointRow,endPointCol)
#                 while u != None:
#                     if self.createResultAsMatrix == True:
#                         self.shortestPathMatrix[u[0]][u[1]] = 100
#                     shortestPathWeights.append(self.matrix[u[0]][u[1]])
#                     u = self.predMatrix[u[0]][u[1]]
#
#                 if not np.isinf(self.pixelWeights[current[0]][current[1]]):
#                     return shortestPathWeights
#                     #return str(self.pixelWeights[current[0]][current[1]])
#                 else:
#                     return str(sys.maxsize)
#             if currentWeight - self.heuristic(current, (endPointRow,endPointCol)) > self.pixelWeights[current[0]][current[1]]:
#                 continue
#
#             # check the neighbor pixels of current
#             for neighbor in self.getNeighborIndices(current[0], current[1]):
#                 newDistance = self.pixelWeights[current[0]][current[1]] + self.matrix[current[0]][current[1]]
#                 # check that the neighbor is not out of raster bounds
#                 if neighbor[0] > 0 and neighbor[1] > 0 and neighbor[0] < self.matrixRowSize and neighbor[1] < self.matrixColSize:
#                     if newDistance < self.pixelWeights[neighbor[0]][neighbor[1]]:
#
#                         self.predMatrix[neighbor[0]][neighbor[1]] = (current[0], current[1])
#                         if self.createResultAsMatrix == True:
#                             if not self.shortestPathMatrix[current[0]][current[1]] == 100:
#                                 self.shortestPathMatrix[current[0]][current[1]] = 50
#
#                         self.pixelWeights[neighbor[0]][neighbor[1]] = newDistance
#                         heapq.heappush(pq,(self.pixelWeights[neighbor[0]][neighbor[1]] + self.heuristic(neighbor, (endPointRow,endPointCol)), neighbor))
#
#         return [sys.maxsize]
#
#
#     def getNeighborIndices(self, i, j):
#         # return list of neighbor indices
#         bl = (i-1,j-1)
#         bm = (i-1,j)
#         br = (i-1,j+1)
#         ml = (i,j-1)
#         mr = (i,j+1)
#         tl = (i+1,j-1)
#         tm = (i+1,j)
#         tr = (i+1,j+1)
#
#         return [bl,bm,br,ml,mr,tl,tm,tr]
#
#     def heuristic(self, point1, point2):
#         # calculate heuristic value depended on the defined heuristic index
#         if self.heuristicIndex == 0:
#             minRasterValue = (self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).minimumValue
#             heurValue = max(abs(point2[0]-point1[0]), abs(point2[1]-point1[1])) * minRasterValue
#         else:
#             meanRasterValue = (self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).mean
#             if self.heuristicIndex == 1:
#                 factor = (meanRasterValue/4)
#             elif self.heuristicIndex == 2:
#                 factor = (meanRasterValue/2)
#             elif self.heuristicIndex == 3:
#                 factor = (meanRasterValue/1.5)
#             elif self.heuristicIndex == 4:
#                 factor = (meanRasterValue/1.25)
#             elif self.heuristicIndex == 5:
#                 factor = meanRasterValue
#
#             heurValue = max(abs(point2[0]-point1[0]), abs(point2[1]-point1[1])) * factor
#
#         return heurValue


