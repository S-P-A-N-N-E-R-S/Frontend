#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz
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

import os
from enum import Enum

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QAbstractItemView, QTreeView

from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel


class AnalysisItem(QStandardItem):

    class ItemType(Enum):
        ANALYSIS = 0
        GROUP = 1

    def __init__(self, label, itemType, analysis=None, userData=None):
        """
        Tree View item which represents an analysis or group
        :param label: label in the tree
        :param itemType: distinguish between group and expression items
        :param analysis: analysis name or path. None in Group Items.
        :param userData: arbitrary user data. None in Group Items.
        """
        super().__init__(label)
        self.label = label
        self.itemType = itemType
        self.analysis = analysis
        self.userData = userData

        if self.itemType == self.ItemType.GROUP:
            self.setSelectable(False)

    def getLabel(self):
        return self.label

    def getUserData(self):
        return self.userData

    def getItemType(self):
        return self.itemType

    def getAnalysis(self):
        return self.analysis


class AnalysisTreeView(QTreeView):
    """
    Displays OGDF Analysis in a tree view grouped by type
    """

    analysisSelected = pyqtSignal(str)
    analysisDeselected = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.rootGroups = {}

        # set up tree view
        self.treeModel = QStandardItemModel()
        self.setModel(self.treeModel)
        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.selectionModel().currentChanged.connect(self._itemChanged)

    def _itemChanged(self, currentItemIndex, _previousItemIndex):
        """Emits signal if analysis is changed"""
        item = self.treeModel.itemFromIndex(currentItemIndex)
        if item is not None:
            if item.getItemType() == AnalysisItem.ItemType.ANALYSIS:
                self.analysisSelected.emit(item.getAnalysis())
            else:
                self.analysisDeselected.emit()

    def addAnalysis(self, analysis, userData=None):
        """
        Add analysis to tree view. Paths in the tree can be created with slashes in the name.
        :param analysis: analysis or path
        :type analysis: str
        :param userData:
        :return:
        """
        groups, analysisName = os.path.split(analysis)
        groups = groups.split("/") if groups else []

        # search for last existing group/node in tree
        currentTreeGroups = [self.treeModel.item(row) for row in range(self.treeModel.rowCount())]
        lastGroupItem = None
        lastGroupIndex = -1
        for index, group in enumerate(groups):
            foundGroupItem = None
            # search group in available tree groups on same depth
            for treeGroup in currentTreeGroups:
                if group == treeGroup.getLabel():
                    foundGroupItem = treeGroup

            if foundGroupItem is not None:
                # save last found group
                lastGroupItem = foundGroupItem
                lastGroupIndex = index
                # get tree groups of next depth
                currentTreeGroups = [foundGroupItem.child(row) for row in range(foundGroupItem.rowCount())]
            else:
                # current group not found in tree
                break

        # if not all groups found, create missing groups
        if lastGroupIndex < len(groups)-1:
            for index in range(lastGroupIndex+1, len(groups)):
                newGroup = AnalysisItem(groups[index], AnalysisItem.ItemType.GROUP)
                if lastGroupItem is None:
                    self.treeModel.appendRow(newGroup)
                else:
                    lastGroupItem.appendRow(newGroup)
                lastGroupItem = newGroup

        # append new analysis
        analysisItem = AnalysisItem(analysisName, AnalysisItem.ItemType.ANALYSIS, analysis, userData)
        if lastGroupItem is None:
            # if not a path or no group existing
            self.treeModel.appendRow(analysisItem)
        else:
            lastGroupItem.appendRow(analysisItem)

    def getAnalysis(self):
        """
        Returns selected analysis or None if none or group is selected
        :return:
        """
        selectedItem = self.treeModel.itemFromIndex(self.currentIndex())
        if selectedItem is not None and selectedItem.getItemType() == AnalysisItem.ItemType.ANALYSIS:
            return selectedItem.getAnalysis(), selectedItem.getUserData()

        return None, None

    def removeAllAnalysis(self):
        self.treeModel.clear()
