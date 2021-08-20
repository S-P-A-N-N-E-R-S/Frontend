from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPoint
from qgis.utils import iface

from qgis.PyQt.QtWidgets import QUndoCommand

from .ExtGraph import ExtGraph

class ExtVertexUndoCommand(QUndoCommand):
    def __init__(self, layerId, vertexId, oldPoint, operation, newPoint=None):
        """
        A vertex command depends on the vertices properties
        and on the operation (delete or add or move) itself.

        :type layerId: Integer id of layer which contains the vertices graph
        :type vertexId: Integer
        :type oldPoint: QgsPointXY 
        :type operation: String "Delete", "Add", "Move"
        :type newPoint: QgsPointXY
        """
        # TODO: include all edge operations which also can happen during delete or add operations
        super().__init__()
        self.mVertexId = vertexId
        self.mOldPoint = oldPoint
        self.mNewPoint = newPoint
        self.mOperation = operation

        self.redoString = "Redo: " + self.mOperation + " vertex " + str(self.mVertexId)
        self.undoString = "Undo: "
        if self.mOperation == "Delete":
            self.undoString += "Readd vertex " + str(self.mVertexId)
        elif self.mOperation == "Add":
            self.undoString += "Delete vertex " + str(self.mVertexId)
        else:
            self.undoString += "Move vertex " + str(self.mVertexId) + " back"
                    
        self.setText(self.undoString)
        
        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer
    
    def __del__(self):
        del self.redoString
        del self.undoString

    def id(self):
        return self.mVertexId

    def _addVertex(self, readd=False):
        if readd:
            self.mVertexId = self.mLayer.mGraph.addVertex(self.mOldPoint, self.mVertexId)
        else:
            self.mVertexId = self.mLayer.mGraph.addVertex(self.mOldPoint)

        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(self.mOldPoint))

        feat.setAttributes([self.mVertexId, self.mOldPoint.x(), self.mOldPoint.y()])
        self.mLayer.dataProvider().addFeature(feat, True)

        # call childs commands undo in reverse order
        for i in range(self.childCount() - 1, -1, -1):
            childCommand = self.child(i)
            childCommand.undo()

    def _deleteVertex(self):
        deletedEdges = self.mLayer.mGraph.deleteVertex(self.mVertexId, True)

        self.mLayer.dataProvider().deleteFeature(self.mVertexId, True)

        if len(deletedEdges) > 0 and self.childCount() == 0:
            # call child commands redo in order
            for i in deletedEdges:
                edge = self.mLayer.mGraph.edge(i)
                fromVertex = edge.fromVertex()
                toVertex = edge.toVertex()

                # create child command and call its redo
                edgeUndoCommand = ExtEdgeUndoCommand(self.mLayer.id(), i, fromVertex, toVertex, True, self)
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
            self.mLayer.mGraph.vertex(self.mVertexId).setNewPoint(self.mNewPoint)

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
            self.mLayer.mGraph.vertex(self.mVertexId).setNewPoint(self.mOldPoint)
        
        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def mergeWith(self, command):
        pass

class ExtEdgeUndoCommand(QUndoCommand):
    def __init__(self, layerId, edgeId, fromVertex, toVertex, deleted=True, parentCommand=None):
        """
        An edge command depends on the edges properties
        and on the command (delete or add) itself.

        :type layerId: Integer id of layer which contains the edges graph
        :type edgeId: Integer
        :type fromVertex: Integer
        :type toVertex: Integer
        :type deleted: Bool True if the command was a deletion, an addition otherwise
        """
        # TODO: also include all cost functions adn highlights
        super().__init__(parentCommand)
        
        self.mEdgeId = edgeId
        self.mFromVertex = fromVertex
        self.mToVertex = toVertex
        self.mDeleted = deleted

        self.redoString = "Redo: " + "Delete" if self.mDeleted else "Readd" + " edge " + str(self.mEdgeId) + " = (" + str(self.mFromVertex) + ", " + str(self.mToVertex) + ")"
        self.undoString = "Undo: " + "Readd" if self.mDeleted else "Delete" + " edge " + str(self.mEdgeId) + " = (" + str(self.mFromVertex) +  ", " +  str(self.mToVertex) + ")"
                    
        self.setText(self.undoString)
        
        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer

        if self.mLayer.mGraph.distanceStrategy == "Advanced":
            self.mOldCosts = []
            for functionIdx in range(self.mLayer.mGraph.amountOfEdgeCostFunctions()):
                self.mOldCosts.append(self.mLayer.mGraph.costOfEdge(self.mEdgeId, functionIdx))

        self.mUpdateCosts = False
        self.mCostsChanged = False
        if self.mFromVertex == -1 and self.mToVertex == -1:
            # only costs of edge have changed -> expect call of setNewCosts
            self.mUpdateCosts = True 
    
    def __del__(self):
        del self.redoString
        del self.undoString
        if self.mOldCosts:
            del self.mOldCosts
        if self.mNewCosts:
            del self.mNewCosts

    def id(self):
        return self.mEdgeId

    def __deleteEdge(self):
        self.mLayer.mGraph.deleteEdge(self.mEdgeId)

        self.mLayer.dataProvider().deleteFeature(self.mEdgeId, False)
        
        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def __addEdge(self):
        self.mEdgeId = self.mLayer.mGraph.addEdge(self.mFromVertex, self.mToVertex, self.mEdgeId)

        if self.mLayer.mGraph.distanceStrategy == "Advanced":
            # on Advanced costs new edges will be initiated with 0 costs on every function index
            amountEdgeCostFunctions = self.mLayer.mGraph.amountOfEdgeCostFunctions()
            for idx in range(amountEdgeCostFunctions):
                self.mLayer.mGraph.setCostOfEdge(self.mEdgeId, idx, 0)

        feat = QgsFeature()
        fromVertex = self.mLayer.mGraph.vertex(self.mFromVertex).point()
        toVertex = self.mLayer.mGraph.vertex(self.mToVertex).point()
        feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(fromVertex), QgsPoint(toVertex)]))

        feat.setAttributes([self.mEdgeId, self.mFromVertex, self.mToVertex, self.mLayer.mGraph.costOfEdge(self.mEdgeId)])

        self.mLayer.dataProvider().addFeature(feat, False)

        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def setNewCosts(self, newCosts):
        """
        Changing costs of edge instead of adding or deleting an edge.

        :type newCosts: Float[]
        """
        self.mNewCosts = []
        for i in range(len(newCosts)):
            self.mNewCosts.append(newCosts[i])
        self.mCostsChanged = True

    def redo(self):
        # set new costs again
        if self.mUpdateCosts or self.mCostsChanged:
            for i in range(len(self.mNewCosts)):
                self.mLayer.mGraph.setCostOfEdge(self.mEdgeId, i, self.mNewCosts[i])
            self.undoString = "Set Costs of Edge " + str(self.mEdgeId) + " again."

        # delete edge again
        elif self.mDeleted:
            self.__deleteEdge()
        
        # add edge again
        else:
            self.__addEdge()

        self.setText(self.undoString)

    def undo(self):
        # set old costs again
        if self.mUpdateCosts or self.mCostsChanged:
            for i in range(len(self.mOldCosts)):
                self.mLayer.mGraph.setCostOfEdge(self.mEdgeId, i, self.mOldCosts[i])
            self.redoString = "Reset new Costs of Edge " + str(self.mEdgeId) + "."

        # add edge again
        elif self.mDeleted:
            self.__addEdge()
        
        # delete edge again
        else:
            self.__deleteEdge()

        self.setText(self.redoString)

    def mergeWith(self, command):
        return False