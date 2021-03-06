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

from datetime import date, datetime

import matplotlib.pyplot as plt
import numpy as np


class BenchmarkVisualisation():

    def __init__(self, yLabel, createLegend, logSelected, tightLayout):
        # xLabels and values are 2D
        # zLabels is 1D
        self.xParameters = []
        self.yLabel = yLabel
        self.zLabels = []
        self.values = []
        self.xParametersBoxPlot = []
        self.zLabelsBoxPlot = []
        self.valuesBoxPlot = []
        self.createLegend = createLegend
        self.logSelected = logSelected
        self.tightLayout = tightLayout

    def setOneBoxPlotData(self, xLabel, xParameters, zLabel, values):
        self.xParametersBoxPlot.append(xParameters)
        self.zLabelsBoxPlot.append(zLabel)
        self.valuesBoxPlot.append(values)
        self.xLabel = xLabel

    def setOnePlotData(self, xLabel, xParameters, zLabel, values):
        self.xParameters.append(xParameters)
        self.zLabels.append(zLabel)
        self.values.append(values)
        self.xLabel = xLabel

    def createTextFile(self, path, boxPlot):
        dateString = date.today().strftime("%b_%d_%Y_")
        timeString = datetime.now().strftime("%H_%M_%S_%f")
        if path == "":
            filename = f"{path}BenchmarkResult_{dateString}{timeString}.csv"
        else:
            filename = f"{path}/BenchmarkResult_{dateString}{timeString}.csv"

        with open(filename, "w") as f:
            longestParasIndex = 0
            longestParasLength = len(self.xParameters[0])
            for counter, xParaList in enumerate(self.xParameters):
                if longestParasLength < len(xParaList):
                    longestParasIndex = counter
                    longestParasLength = len(xParaList)

            if len(self.zLabels) > 1:
                f.write(self.xLabel + ",")

            for index, parameter in enumerate(self.xParameters[longestParasIndex]):
                if not boxPlot:
                    if index == 0:
                        f.write(parameter)
                    else:
                        f.write("," + parameter)
                else:
                    for i in range(len(self.valuesBoxPlot[0][index])):
                        if index == 0 and i == 0:
                            f.write(parameter + "_" + str(i))
                        else:
                            f.write("," + parameter + "_" + str(i))

            f.write("\n")

            for i in range(len(self.zLabels)):
                if len(self.zLabels[i]) > 0:
                    f.write(self.zLabels[i] + ",")
                if not boxPlot:
                    for index, value in enumerate(self.values[i]):
                        if index == 0:
                            f.write(str(value))
                        else:
                            f.write("," + str(value))
                else:
                    valueListForPlot = self.valuesBoxPlot[i]
                    for index, valueList in enumerate(valueListForPlot):
                        for index2, value in enumerate(valueList):
                            if index == 0 and index2 == 0:
                                f.write(str(value))
                            else:
                                f.write("," + str(value))
                f.write("\n")

    def plotPoints(self, withLines, callNumber):
        plt.figure(callNumber)

        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]

            if withLines is True:
                plt.plot(self.xParameters[i], self.values[i], marker="o", label=zLabel, linestyle='-')
            else:
                plt.scatter(self.xParameters[i], self.values[i], label=zLabel)

        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        if self.createLegend:
            plt.legend(loc="best")

        if self.logSelected:
            plt.yscale("log")

        if self.tightLayout:
            plt.tight_layout()
        plt.show()

    def plotLines(self, callNumber):
        plt.figure(callNumber)

        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]

            plt.plot(self.xParameters[i], self.values[i], label=zLabel, linestyle='-')

        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        if self.createLegend:
            plt.legend(loc="best")

        if self.logSelected:
            plt.yscale("log")

        if self.tightLayout:
            plt.tight_layout()

        plt.show()

    def plotBarChart(self, callNumber):
        plt.figure(callNumber)

        width = 0.15

        # get longest xParameters
        longestParaIndex = 0
        longestPara = len(self.xParameters[0])
        for i in range(len(self.xParameters)):
            if len(self.xParameters[i]) > longestPara:
                longestParaIndex = i
                longestPara = len(self.xParameters[i])

        x = np.arange(longestPara)

        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]

            plt.bar(x, self.values[i], label=zLabel, width=width)

            x = [br + width for br in x]

        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        plt.xticks([r + ((width/2)*(len(self.zLabels)-1)) for r in range(len(self.xParameters[longestParaIndex]))],
                   self.xParameters[longestParaIndex])
        if self.createLegend:
            plt.legend(loc="best")

        if self.logSelected:
            plt.yscale("log")

        if self.tightLayout:
            plt.tight_layout()

        plt.show()

    def plotBoxPlot(self, _callNumber):
        _fig, ax = plt.subplots()
        boxes = []
        boxPlots = []
        colors = ["blue", "green", "purple", "tan", "pink", "red"]

        for i in range(len(self.zLabelsBoxPlot)):
            bp = ax.boxplot(self.valuesBoxPlot[i], labels=self.xParametersBoxPlot[i], patch_artist=True)
            for patch in bp["boxes"]:
                patch.set(facecolor=colors[i])
            boxes.append(bp["boxes"][0])
            boxPlots.append(bp)

        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        if self.createLegend:
            plt.legend(boxes, self.zLabelsBoxPlot, loc="best")
        if self.logSelected:
            ax.set_yscale("log")

        if self.tightLayout:
            plt.tight_layout()

        plt.show()
