#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Dennis Benz, Tim Hartmann
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
import numpy as np
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
        return max(abs(point2[0]-point1[0]), abs(point2[1]-point1[1])) * factor
