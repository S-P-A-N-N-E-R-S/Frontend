#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Tim Hartmann
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

from qgis.core import QgsApplication, QgsProject, QgsPluginLayer

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QToolButton, QListWidget, QListWidgetItem, QRadioButton, QTreeWidgetItem, QSizePolicy, QTabWidget

from .baseView import BaseView
from .widgets.QgsOgdfBenchmarkWidget import QgsOGDFBenchmarkWidget
from ..controllers.benchmark import BenchmarkController
from ..network import parserManager
from ..network.protocol.build.available_handlers_pb2 import FieldInformation


class BenchmarkView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.benchmarkAnalysisCounter = 1
        addButton = QToolButton()
        addButton.setObjectName("new_benchmark")
        addButton.setText("➕")
        addButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        addButton.setMaximumSize(25, 25)
        addButton.setIcon(QgsApplication.getThemeIcon("symbologyAdd.svg"))
        addButton.clicked.connect(self._newBenchmarkSelection)
        self.dialog.analysis_visualisation.layout().addWidget(addButton, *(0,2))

        self._createNewBenchmarkSelections(True)

        # get controller (this calls the addOGDFAlg method)
        self.controller = BenchmarkController(self)

        self.dialog.benchmark_add_all_graphs.setIcon(QgsApplication.getThemeIcon("mIconModelOutput.svg"))

        self.dialog.benchmark_refresh_btn.clicked.connect(self.controller.refreshView)
        self.dialog.benchmark_clear_graph_selection.clicked.connect(self._clearGraphSelection)
        self.dialog.benchmark_start_benchmark.clicked.connect(self.controller.runTask)
        self.dialog.benchmark_add_all_graphs.clicked.connect(self._addAllGraphs)
        self.dialog.benchmark_abort_benchmark.clicked.connect(self.controller.abortTask)

        self.dialog.benchmark_graph_selection.model().rowsInserted.connect(self._updateOGDFParameters)

        self.dialog.benchmark_all_graphs.itemDoubleClicked.connect(self._addItemToSelected)
        self.dialog.benchmark_graph_selection.itemDoubleClicked.connect(self._deleteItem)

        # load parameters for every selected ogdf algorithm
        self.ogdfBenchmarkWidget = QgsOGDFBenchmarkWidget(self.dialog)

        self.dialog.benchmark_ogdf_parameters.setLayout(self.ogdfBenchmarkWidget.layout)
        self.dialog.benchmark_ogdf_algorithms.itemChanged.connect(self._updateOGDFParameters)
        self.dialog.benchmark_ogdf_algorithms.itemChanged.connect(self._createNewBenchmarkSelections)

        self.FIELD_TYPES = [
            FieldInformation.FieldType.BOOL,
            FieldInformation.FieldType.INT,
            FieldInformation.FieldType.DOUBLE,
            FieldInformation.FieldType.STRING,
            FieldInformation.FieldType.CHOICE,
            FieldInformation.FieldType.EDGE_COSTS,
            FieldInformation.FieldType.VERTEX_COSTS,
            FieldInformation.FieldType.EDGE_ID,
            FieldInformation.FieldType.VERTEX_ID
        ]

    def getOGDFBenchmarkWidget(self):
        return self.ogdfBenchmarkWidget

    def _createNewBenchmarkSelections(self, initial = False):
        # delete all widgets
        copy = self.benchmarkAnalysisCounter
        for i in reversed(range(1, copy+1)):
            self._clearOneBenchmarkSelection(i, initial)
        # create the same amount of updated widgets
        for i in range(1,copy+1):
            self._newBenchmarkSelection()

    def _newBenchmarkSelection(self):
        self.benchmarkAnalysisCounter+=1
        tabBenchmarkWidget = QTabWidget()


        self.dialog.analysis_visualisation.layout().addWidget(tabBenchmarkWidget,*(self.benchmarkAnalysisCounter,0))

        ogdfAlgs = self.getSelectedAlgs()
        requests = []

        # get field information for all selected algorithms
        for alg in ogdfAlgs:
            request = parserManager.getRequestParser(alg)
            if request:
                requests.append(request.getFieldInfo())

        itemsToAdd = ["Graphs", "Graph Edges", "Graph Vertices", "Graph Densities", "Graph Min Fragility",
                     "Graph Max Fragility", "Graph Avg Fragility", "Graph Diameter", "Graph Radius",
                     "Graph Girth (unit weights)", "Graph Girth", "Graph Node Connectivity",
                     "Graph Edge Connectivity", "Graph Reciprocity", "Algorithms"]


        colorCat = QListWidget()
        colorCat.setMinimumSize(380, 192)
        colorCat.setObjectName("colour_selection_" + str(self.benchmarkAnalysisCounter))
        for item in itemsToAdd:
            self._addItemToWidget(colorCat, item)
        # add field of selected algorithms
        self._addParameterFields(colorCat, requests)
        tabBenchmarkWidget.addTab(colorCat, "Colour Cat")

        xAxisCat = QListWidget()
        xAxisCat.setMinimumSize(380, 192)
        xAxisCat.setObjectName("xAxis_selection_" + str(self.benchmarkAnalysisCounter))
        for item in itemsToAdd:
            self._addItemToWidget(xAxisCat, item)
        # add field of selected algorithms
        self._addParameterFields(xAxisCat, requests)
        tabBenchmarkWidget.addTab(xAxisCat, "x-axis Cat")

        analysisSel = QListWidget()
        analysisSel.setMinimumSize(380, 192)
        analysisSel.setObjectName("analysis_selection_" + str(self.benchmarkAnalysisCounter))
        itemsToAdd = ["Runtime (seconds)", "Number of Edges", "Number of Vertices", "Edges Difference",
                      "Vertices Difference", "Average Degree", "Sparseness", "Lightness",
                      "Min Fragility", "Max Fragility", "Avg Fragility", "Diameter", "Radius",
                      "Girth (unit weights)", "Girth", "Node Connectivity", "Edge Connectivity", "Reciprocity"]
        for item in itemsToAdd:
            self._addRadioButtonToWidget(analysisSel, item)
        tabBenchmarkWidget.addTab(analysisSel, "Analysis")

        # visualization widget
        listWidgetVisualisation = QListWidget()
        listWidgetVisualisation.setMinimumSize(380,192)
        listWidgetVisualisation.setObjectName("visualisation_"+ str(self.benchmarkAnalysisCounter))
        self.dialog.analysis_visualisation.layout().addWidget(listWidgetVisualisation,*(self.benchmarkAnalysisCounter,1))

        # fill widget
        itemsToAdd = ["Points without connection", "Points with connection", "Bar chart", "Lines", "Box plot"]
        for item in itemsToAdd:
            self._addItemToWidget(listWidgetVisualisation, item)

        item = QListWidgetItem("------------------------------Additional Options------------------------------")
        listWidgetVisualisation.addItem(item)
        itemsToAdd = ["Logarithmic y-axis", "Create legend", "Tight layout"]
        for item in itemsToAdd:
            self._addItemToWidget(listWidgetVisualisation, item)

        removeButton = QToolButton()
        removeButton.setText("➖")
        removeButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        removeButton.setMaximumSize(25, 25)
        removeButton.setIcon(QgsApplication.getThemeIcon("symbologyRemove.svg"))
        removeButton.clicked.connect(lambda: self._clearOneBenchmarkSelection(self.benchmarkAnalysisCounter))
        self.dialog.analysis_visualisation.layout().addWidget(removeButton, *(self.benchmarkAnalysisCounter,2))

    def _addParameterFields(self, widget, requests):
        alreadyAddedLabels = []
        for fields in requests:
            for key in fields:
                field = fields[key]
                if field.get("type") not in self.FIELD_TYPES:
                    continue
                if not field.get("label") in alreadyAddedLabels:
                    alreadyAddedLabels.append(field.get("label"))
                    item = QListWidgetItem(field.get("label"))
                    item.setCheckState(Qt.Unchecked)
                    widget.addItem(item)

    def _addItemToWidget(self, widget, itemName):
        item = QListWidgetItem(itemName)
        item.setCheckState(Qt.Unchecked)
        widget.addItem(item)

    def _addRadioButtonToWidget(self, widget, itemName):
        item = QListWidgetItem()
        widget.addItem(item)
        widget.setItemWidget(item, QRadioButton(itemName))

    def _clearOneBenchmarkSelection(self, row, initial = False):
        self.benchmarkAnalysisCounter-=1
        rangeEnd = 3
        if initial:
            rangeEnd = 2
        for i in reversed(range(rangeEnd)):
            self.dialog.analysis_visualisation.layout().itemAtPosition(row, i).widget().setParent(None)

    def _updateOGDFParameters(self):
        if self.dialog.benchmark_graph_selection.count() > 0:
            ogdfAlgs = self.getSelectedAlgs()
            requests = []

            # get field information for all selected algorithms
            for alg in ogdfAlgs:
                request = parserManager.getRequestParser(alg)
                if request:
                    requests.append(request.getFieldInfo())

            # set the parameter fields so the widgets can be created
            self.ogdfBenchmarkWidget.setParameterFields(requests)

        else:
            self.ogdfBenchmarkWidget.clearWidgets()

    def _getOGDFParameters(self):
        self.ogdfBenchmarkWidget.getBenchmarkDataObjects()

    def updateAllGraphs(self):
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsPluginLayer) and not self.dialog.benchmark_all_graphs.findItems(layer.name(), Qt.MatchExactly):
                self.dialog.benchmark_all_graphs.addItem(layer.name())

    def _addAllGraphs(self):
        for i in range(self.dialog.benchmark_all_graphs.count()):
            self.dialog.benchmark_graph_selection.addItem(self.dialog.benchmark_all_graphs.item(i).text())

    def _addItemToSelected(self, item):
        self.dialog.benchmark_graph_selection.addItem(item.text())

    def _deleteItem(self, item):
        self.dialog.benchmark_graph_selection.takeItem(self.dialog.benchmark_graph_selection.row(item))
        self._updateOGDFParameters()

    def _clearGraphSelection(self):
        self.dialog.benchmark_graph_selection.clear()
        self._updateOGDFParameters()

    def addOGDFAlg(self, analysis):
        item = QTreeWidgetItem(self.dialog.benchmark_ogdf_algorithms)
        item.setText(0, analysis)
        item.setCheckState(0,Qt.Unchecked)
        self.dialog.benchmark_ogdf_algorithms.insertTopLevelItem(0,item)

    def addOGDFAlgs(self, analysisList):
        groups = {}
        for analysis in analysisList:
            try:
                groups[analysis.split("/")[0]]
            except:
                groups[analysis.split("/")[0]] = []

            groups[analysis.split("/")[0]].append(analysis.split("/")[1])

        items = []
        for key, values in groups.items():
            item = QTreeWidgetItem([key])
            for value in values:
                child = QTreeWidgetItem([value])
                child.setCheckState(0, Qt.Unchecked)
                item.addChild(child)
            items.append(item)

        self.dialog.benchmark_ogdf_algorithms.insertTopLevelItems(0, items)

    def resetOGDFAlgs(self):
        self.dialog.benchmark_ogdf_algorithms.clear()

    def getSelectedAlgs(self):
        checked = []
        root = self.dialog.benchmark_ogdf_algorithms.invisibleRootItem()
        childCount = root.childCount()

        for i in range(childCount):
            child = root.child(i)
            numChildren = child.childCount()

            for n in range(numChildren):
                child2 = child.child(n)
                if child2.checkState(0) == Qt.Checked:
                    checked.append(child.text(0) + "/" + child2.text(0))
        return checked

    def getSelection1(self):
        """
        Method to get the first selections of all the benchmark_visualisation QtListWidgets.
        These selections are used in the first partitioning step.

        :returns 2D list
        """
        grid = self.dialog.analysis_visualisation.layout()
        selection1 = []
        for c in range(1,self.benchmarkAnalysisCounter+1):
            benchmarkSelWidget = grid.itemAtPosition(c,0).widget().widget(0)
            oneSelection = []
            for i in range(benchmarkSelWidget.count()):
                if benchmarkSelWidget.item(i).checkState() == Qt.Checked:
                    oneSelection.append(benchmarkSelWidget.item(i).text())
            selection1.append(oneSelection)

        return selection1

    def getSelection2(self):
        """
        Method to get the first selections of all the benchmark_visualisation QtListWidgets.
        These selections are used in the second partitioning step.

        :returns 2D list
        """
        grid = self.dialog.analysis_visualisation.layout()
        selection2 = []

        for c in range(1,self.benchmarkAnalysisCounter+1):
            benchmarkSelWidget = grid.itemAtPosition(c,0).widget().widget(1)
            oneSelection = []
            sectionFound = False
            for i in range(benchmarkSelWidget.count()):
                if benchmarkSelWidget.item(i).checkState() == Qt.Checked:
                    oneSelection.append(benchmarkSelWidget.item(i).text())
            selection2.append(oneSelection)

        return selection2

    def getAnalysis(self):
        """
        Method to get the analysis of all the benchmark_visualisation QtListWidgets.
        The selection is used to perform a specified analysis like number of edges or sparseness.

        :returns list
        """
        grid = self.dialog.analysis_visualisation.layout()
        analysis = []

        for c in range(1,self.benchmarkAnalysisCounter+1):
            benchmarkSelWidget = grid.itemAtPosition(c,0).widget().widget(2)
            sectionFound = False
            for i in range(benchmarkSelWidget.count()):
                radioB = benchmarkSelWidget.itemWidget(benchmarkSelWidget.item(i))
                if radioB.isChecked():
                    analysis.append(radioB.text())
        return analysis

    def getVisualisation(self):
        """
        Method to get the selected visualisations of all the benchmark requests.

        :returns 2D list
        """
        grid = self.dialog.analysis_visualisation.layout()
        visualisation = []

        for c in range(1,self.benchmarkAnalysisCounter+1):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            oneSelection = []
            for i in range(visualisationSelWidget.count()):
                if "Additional Options" in visualisationSelWidget.item(i).text():
                    break
                if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                    oneSelection.append(visualisationSelWidget.item(i).text())
            visualisation.append(oneSelection)

        return visualisation


    def getExecutions(self, algName):
        for i in range(self.dialog.benchmark_ogdf_parameters.layout().count()):
            widget = self.dialog.benchmark_ogdf_parameters.layout().itemAt(i).widget()
            if widget.objectName() == "Executions_" + algName:
                return widget.value()

        return -1

    def getCreateLegendSelection(self):
        legendSelections = []
        grid = self.dialog.analysis_visualisation.layout()
        for c in range(1,self.benchmarkAnalysisCounter+1):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            for i in range(visualisationSelWidget.count()):
                if visualisationSelWidget.item(i).text() == "Create legend":
                    if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                        legendSelections.append(True)
                    else:
                        legendSelections.append(False)

        return legendSelections

    def getLogAxisSelection(self):
        logSelections = []
        grid = self.dialog.analysis_visualisation.layout()
        for c in range(1,self.benchmarkAnalysisCounter+1):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            for i in range(visualisationSelWidget.count()):
                if visualisationSelWidget.item(i).text() == "Logarithmic y-axis":
                    if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                        logSelections.append(True)
                    else:
                        logSelections.append(False)

        return logSelections

    def getTightLayoutSelection(self):
        tightSelections = []
        grid = self.dialog.analysis_visualisation.layout()
        for c in range(1,self.benchmarkAnalysisCounter+1):
            visualisationSelWidget = grid.itemAtPosition(c,1).widget()
            for i in range(visualisationSelWidget.count()):
                if visualisationSelWidget.item(i).text() == "Tight layout":
                    if visualisationSelWidget.item(i).checkState() == Qt.Checked:
                        tightSelections.append(True)
                    else:
                        tightSelections.append(False)

        return tightSelections

    def getNumberOfRequestedBenchmarks(self):
        return self.benchmarkAnalysisCounter

    def getTextFilePath(self):
        return self.dialog.benchmark_txt_path.filePath()

    def getCsvCreationSelection(self):
        return self.dialog.benchmark_create_as_txt.checkState() == Qt.Checked

    def getCompleteAnalysisSelection(self):
        return self.dialog.benchmark_complete_analysis.checkState() == Qt.Checked

    def getNumberOfSelectedGraphs(self):
        return self.dialog.benchmark_graph_selection.count()

    def setNetworkButtonsEnabled(self, enabled):
        self.dialog.benchmark_refresh_btn.setEnabled(enabled)
