#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Tim Hartmann
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
import sys

try:
    from ..lib.AStarC import AStar
except ImportError:
    # use non-performant pure Python implementation
    from .AStarPython import AStar


class AStarOnRasterData:

    def __init__(self, rLayer, band, sourceCrs, heuristicIndex, createShortestPathMatrix, rasterID, heursticID):
        self.heuristicIndex = heuristicIndex
        ds = gdal.Open(rLayer.source())
        readBand = ds.GetRasterBand(band)
        self.bandID = band
        self.rLayer = rLayer
        self.sourceCrs = sourceCrs
        self.destCrs = self.rLayer.crs()
        self.tr = QgsCoordinateTransform(self.sourceCrs, self.destCrs, QgsProject.instance())
        self.rasterID = rasterID
        self.heuristicID = heursticID

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
        self.predMatrix = None

        self.pixelWeights = None
        minRasterValue = int((self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).minimumValue)
        meanRasterValue = int((self.rLayer.dataProvider().bandStatistics(self.bandID, QgsRasterBandStats.All)).mean)

        #----------------------------------

        self.aStarObject = AStar(readBand.ReadAsArray(), heuristicIndex, minRasterValue, meanRasterValue,
                                   createShortestPathMatrix)

        # ----------------------------------

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

        return self.aStarObject.shortestPath(startPointRow, startPointCol, endPointRow, endPointCol)

        #----------------------------------

    def getShortestPathMatrix1(self):
        numpyTransform = np.matrix(self.aStarObject.getShortestPathMatrix1())
        return numpyTransform

    def getShortestPathMatrix2(self):
        numpyTransform = np.matrix(self.aStarObject.getShortestPathMatrix2())
        return numpyTransform

    def getShortestPathMatrix3(self):
        numpyTransform = np.matrix(self.aStarObject.getShortestPathMatrix3())
        return numpyTransform

    def getNumberOfDiagonals(self):
        return self.aStarObject.getNumberOfDiagonals()
