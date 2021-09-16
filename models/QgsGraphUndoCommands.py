from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPoint
from qgis.utils import iface

from qgis.PyQt.QtWidgets import QUndoCommand

from .ExtGraph import ExtGraph

class ExtVertexUndoCommand(QUndoCommand):
    def __init__(self, layerId, vertexIdx, oldPoint, operation, newPoint=None):
        """
        A vertex command depends on the vertices properties
        and on the operation (delete or add or move) itself.

        :type layerId: Integer id of layer which contains the vertices graph
        :type vertexIdx: Integer
        :type oldPoint: QgsPointXY 
        :type operation: String "Delete", "Add", "Move"
        :type newPoint: QgsPointXY
        """
        # TODO: include all edge operations which also can happen during delete or add operations
        super().__init__()

        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer

        self.mVertexIdx = vertexIdx
        if operation != "Add":
            self.mVertexID = self.mLayer.mGraph.vertex(vertexIdx).id()
        self.mOldPoint = oldPoint
        self.mNewPoint = newPoint
        self.mOperation = operation

        self.undoString = "Undo: "
        if self.mOperation == "Delete":
            self.undoString += "Readd vertex " + str(self.mVertexID)
        elif self.mOperation == "Add":
            self.mVertexID = self.mLayer.mGraph.nextVertexID()
            self.undoString += "Delete vertex " + str(self.mVertexID)
        else:
            self.undoString += "Move vertex " + str(self.mVertexID) + " back"
        
        self.redoString = "Redo: " + self.mOperation + " vertex " + str(self.mVertexID)
                    
        self.setText(self.undoString)
    
    def __del__(self):
        del self.redoString
        del self.undoString

    def id(self):
        return self.mVertexID

    def _addVertex(self, readd=False):
        if readd:
            self.mVertexIdx = self.mLayer.mGraph.addVertex(self.mOldPoint, self.mVertexIdx, self.mVertexID)
        else:
            self.mVertexIdx = self.mLayer.mGraph.addVertex(self.mOldPoint)
            self.mVertexID = self.mLayer.mGraph.vertex(self.mVertexIdx).id()

        # feat = QgsFeature()
        # feat.setGeometry(QgsGeometry.fromPointXY(self.mOldPoint))

        # feat.setAttributes([self.mVertexID, self.mOldPoint.x(), self.mOldPoint.y()])
        # self.mLayer.dataProvider().addFeature(feat, True, self.mVertexIdx)

        # call childs commands undo in reverse order
        for i in range(self.childCount() - 1, -1, -1):
            childCommand = self.child(i)
            childCommand.undo()

    def _deleteVertex(self):
        delVertID = self.mLayer.mGraph.vertex(self.mVertexIdx).id()

        deletedEdges = self.mLayer.mGraph.deleteVertex(self.mVertexIdx, True)

        # self.mLayer.dataProvider().deleteFeature(self.mVertexIdx, True)

        if len(deletedEdges) > 0 and self.childCount() == 0:
            # call child commands redo in order
            for id in deletedEdges:
                edgeIdx = self.mLayer.mGraph.findEdgeByID(id)
                edge = self.mLayer.mGraph.edge(edgeIdx)
                
                fromVertexIdx = self.mLayer.mGraph.findVertexByID(edge.fromVertex())
                toVertexIdx = self.mLayer.mGraph.findVertexByID(edge.toVertex())
                
                # create child command and call its redo
                edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), edgeIdx, fromVertexIdx, toVertexIdx, True, self)
                edgeUndoCommand.setDeletedVertex(delVertID, self.mVertexIdx)
                edgeUndoCommand.redo()
        
        elif self.childCount() != 0:
            for i in range(self.childCount()):
                childCommand = self.child(i)
                childCommand.redo()

    def redo(self):

        # delete vertex again
        if self.mOperation == "Delete":
            self._deleteVertex()
        
        # add vertex again
        elif self.mOperation == "Add":
            self._addVertex()
        
        # move vertex again
        else:
            self.mLayer.mGraph.vertex(self.mVertexIdx).setNewPoint(self.mNewPoint)

        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()
    
    def undo(self):
        # add vertex again
        if self.mOperation == "Delete":
            self._addVertex(True)

        # delete vertex again
        elif self.mOperation == "Add":
            self._deleteVertex()

        # move vertex back
        else:
            self.mLayer.mGraph.vertex(self.mVertexIdx).setNewPoint(self.mOldPoint)
        
        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def mergeWith(self, command):
        return False

class ExtEdgeUndoCommand(QUndoCommand):
    def __init__(self, layerId, edgeIdx, fromVertexIdx, toVertexIdx, deleted=True, parentCommand=None):
        """
        An edge command depends on the edges properties
        and on the command (delete or add) itself.

        :type layerId: Integer id of layer which contains the edges graph
        :type edgeIdx: Integer
        :type fromVertexIdx: Integer
        :type toVertexIdx: Integer
        :type deleted: Bool True if the command was a deletion, an addition otherwise
        """
        super().__init__(parentCommand)
        
        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer

        self.mEdgeIdx = edgeIdx
        if deleted:
            self.mEdgeID = self.mLayer.mGraph.edge(edgeIdx).id()
        else:
            self.mEdgeID = self.mLayer.mGraph.nextEdgeID()

        self.mFromVertexIdx = fromVertexIdx
        self.mToVertexIdx = toVertexIdx

        self.mFromVertexID = self.mLayer.mGraph.vertex(fromVertexIdx).id()
        self.mToVertexID = self.mLayer.mGraph.vertex(toVertexIdx).id()
        self.mDeleted = deleted

        self.redoString = "Redo: " + "Delete" if self.mDeleted else "Readd" + " edge " + str(self.mEdgeID) + " = (" + str(self.mFromVertexID) + ", " + str(self.mToVertexID) + ")"
        self.undoString = "Undo: " + "Readd" if self.mDeleted else "Delete" + " edge " + str(self.mEdgeID) + " = (" + str(self.mFromVertexID) +  ", " +  str(self.mToVertexID) + ")"
                    
        self.setText(self.undoString)

        if self.mLayer.mGraph.distanceStrategy == "Advanced":
            self.mOldCosts = []
            for functionIdx in range(self.mLayer.mGraph.amountOfEdgeCostFunctions()):
                self.mOldCosts.append(self.mLayer.mGraph.costOfEdge(self.mEdgeIdx, functionIdx))

        self.mUpdateCosts = False
        self.mCostsChanged = False
        if self.mFromVertexID == -1 and self.mToVertexID == -1:
            # only costs of edge have changed -> expect call of setNewCosts
            self.mUpdateCosts = True 
    
    def __del__(self):
        del self.redoString
        del self.undoString
        if self.mOldCosts:
            del self.mOldCosts
        if hasattr(self, "mNewCosts"):
            del self.mNewCosts

    def id(self):
        return self.mEdgeID

    def __deleteEdge(self):
        self.mLayer.mGraph.deleteEdge(self.mEdgeIdx)

        # self.mLayer.dataProvider().deleteFeature(self.mEdgeIdx, False)

    def __addEdge(self):
        self.mEdgeIdx = self.mLayer.mGraph.addEdge(self.mFromVertexID, self.mToVertexID, self.mEdgeIdx, self.mEdgeID)

        if self.mLayer.mGraph.distanceStrategy == "Advanced":
            # on Advanced costs new edges will be initiated with 0 costs on every function index
            amountEdgeCostFunctions = self.mLayer.mGraph.amountOfEdgeCostFunctions()
            for functionIdx in range(amountEdgeCostFunctions):
                self.mLayer.mGraph.setCostOfEdge(self.mEdgeIdx, functionIdx, 0)

        # feat = QgsFeature()
        # fromVertex = self.mLayer.mGraph.vertex(self.mFromVertexIdx).point()
        # toVertex = self.mLayer.mGraph.vertex(self.mToVertexIdx).point()
        # feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

        # feat.setAttributes([self.mEdgeID, self.mFromVertexID, self.mToVertexID, self.mLayer.mGraph.costOfEdge(self.mEdgeIdx)])

        # self.mLayer.dataProvider().addFeature(feat, False, self.mEdgeIdx)

    def setNewCosts(self, newCosts):
        """
        Changing costs of edge instead of adding or deleting an edge.

        :type newCosts: Float[]
        """
        self.mNewCosts = []
        for i in range(len(newCosts)):
            self.mNewCosts.append(newCosts[i])
        self.mCostsChanged = True
    
    def setDeletedVertex(self, id, idx):
        if self.mFromVertexIdx == -1:
            self.mFromVertexIdx = idx
            self.mFromVertexID = id
        
        elif self.mToVertexIdx == -1:
            self.mToVertexIdx = idx
            self.mToVertexID = id

        self.redoString = "Redo: " + "Delete" if self.mDeleted else "Readd" + " edge " + str(self.mEdgeID) + " = (" + str(self.mFromVertexID) + ", " + str(self.mToVertexID) + ")"
        self.undoString = "Undo: " + "Readd" if self.mDeleted else "Delete" + " edge " + str(self.mEdgeID) + " = (" + str(self.mFromVertexID) +  ", " +  str(self.mToVertexID) + ")"
                    
        self.setText(self.undoString)

    def redo(self):
        # set new costs again
        if self.mUpdateCosts or self.mCostsChanged:
            for i in range(len(self.mNewCosts)):
                self.mLayer.mGraph.setCostOfEdge(self.mEdgeIdx, i, self.mNewCosts[i])
            self.undoString = "Set Costs of Edge " + str(self.mEdgeID) + " again."

        # delete edge again
        elif self.mDeleted:
            self.__deleteEdge()
        
        # add edge again
        else:
            self.__addEdge()

        self.setText(self.undoString)

        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def undo(self):
        # set old costs again
        if self.mUpdateCosts or self.mCostsChanged:
            for i in range(len(self.mOldCosts)):
                self.mLayer.mGraph.setCostOfEdge(self.mEdgeIdx, i, self.mOldCosts[i])
            self.redoString = "Reset new Costs of Edge " + str(self.mEdgeID) + "."

        # add edge again
        elif self.mDeleted:
            self.__addEdge()
        
        # delete edge again
        else:
            self.__deleteEdge()

        self.setText(self.redoString)

        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def mergeWith(self, command):
        return False