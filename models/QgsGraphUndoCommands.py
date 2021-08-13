from qgis.core import QgsProject
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

        self.mText = self.undoString
                    
        self.setText(self.mText)
        
        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer
    
    def id(self):
        return self.mVertexId

    def redo(self):
        # delete vertex again
        if self.mOperation == "Delete":
            deletedEdges = self.mLayer.mGraph.deleteVertex(self.mVertexId)
        
        # add vertex again
        elif self.mOperation == "Add":
            self.mVertexId = self.mLayer.mGraph.addVertex(self.mOldPoint)
        
        # move vertex again
        else:
            self.mLayer.mGraph.vertex(self.mVertexId).setNewPoint(self.mNewPoint)

        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()
    
    def undo(self):
        # add vertex again
        if self.mOperation == "Delete":
            # TODO: availableVertexIndices
            self.mVertexId = self.mLayer.mGraph.addVertex(self.mOldPoint, self.mVertexId)
        
        # delete vertex again
        elif self.mOperation == "Add":
            deletedEdges = self.mLayer.mGraph.deleteVertex(self.mVertexId)

        # move vertex back
        else:
            self.mLayer.mGraph.vertex(self.mVertexId).setNewPoint(self.mOldPoint)
        
        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def mergeWith(self, command):
        pass

class ExtEdgeUndoCommand(QUndoCommand):
    def __init__(self, layerId, edgeId, fromVertex, toVertex, deleted=True):
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
        super().__init__()
        
        self.mEdgeId = edgeId
        self.mFromVertex = fromVertex
        self.mToVertex = toVertex
        self.mDeleted = deleted

        self.redoString = "Redo: " + "Delete" if self.mDeleted else "Readd" + " edge " + str(self.mEdgeId) + " = (" + str(self.mFromVertex) + ", " + str(self.mToVertex) + ")"
        self.undoString = "Undo: " + "Readd" if self.mDeleted else "Delete" + " edge " + str(self.mEdgeId) + " = (" + str(self.mFromVertex) +  ", " +  str(self.mToVertex) + ")"
        self.mText = self.undoString
                    
        self.setText(self.mText)
        
        self.layerId = layerId
        mapLayers = QgsProject.instance().mapLayers()
        for layer in mapLayers.values():
            if layer.id() == self.layerId:
                self.mLayer = layer
    
    def id(self):
        return self.mEdgeId

    # TODO: also adapt features and other information
    def __deleteEdge(self):
        self.mLayer.mGraph.deleteEdge(self.mEdgeId)
        
        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def __addEdge(self):
        self.mEdgeId = self.mLayer.mGraph.addEdge(self.mFromVertex, self.mToVertex, self.mEdgeId)
        # TODO: remove edgeId from mGraph.__availableEdgeIndices

        self.mLayer.triggerRepaint()
        iface.mapCanvas().refresh()

    def redo(self):
        # delete edge again
        if self.mDeleted:
            self.__deleteEdge()
        
        # add edge again
        else:
            self.__addEdge()

        self.setText(self.undoString)

    def undo(self):
        # add edge again
        if self.mDeleted:
            self.__addEdge()
        
        # delete edge again
        else:
            self.__deleteEdge()

        self.setText(self.redoString)

    def mergeWith(self, command):
        pass