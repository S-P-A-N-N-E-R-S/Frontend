import os
from enum import Enum
import html

from qgis.PyQt import uic, QtWidgets
from qgis.core import QgsVectorLayer

from PyQt5.QtCore import pyqtSignal, Qt, QVariant, QObject
from PyQt5.QtWidgets import QPushButton, QAbstractItemView
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from ...models.GraphBuilder import GraphBuilder


class QgsExpressionItem(QStandardItem):

    class ItemType(Enum):
        Expression = 0
        Group = 1

    def __init__(self, label, expressionText, helpText, itemType):
        """
        Tree View item which represents an expression
        :param label: label in the tree
        :param expressionText: text inserted in the code editor
        :param helpText: help text can be set as html string
        :param itemType: distinguish between group and expression items
        """
        super(QgsExpressionItem, self).__init__(label)
        self.label = label
        self.expressionText = expressionText
        self.helpText = helpText
        self.itemType = itemType

    def getExpressionText(self):
        return self.expressionText

    def getHelpText(self):
        return self.helpText

    def setHelpText(self, helpText):
        self.helpText = helpText

    def getItemType(self):
        return self.itemType


class QgsExpressionContext(QObject):
    """
    Expression context class which holds all information of available cost function expressions
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()

        # contains all expressions with editor texts and help texts organized by their groups
        self.groups = {
            "Conditionals": {
                "label": self.tr("Conditionals"),
                "helpText": self.tr("This group contains functions to handle conditional checks in expressions."),
                "expressions": [
                    {
                        "label": "if",
                        "expressionText": " if( ; ; ) ",
                        "helpText": self.tr("Tests a condition and returns a different result depending on the conditional "
                                            "check.")
                    },
                    {
                        "label": self.tr("crossesPolygon"),
                        "expressionText": "crossesPolygon",
                        "helpText": self.tr("Checks whether an edge crosses a polygon.")
                    },
                    {
                        "label": self.tr("insidePolygon"),
                        "expressionText": "insidePolygon",
                        "helpText": self.tr("Checks whether an edge is inside a polygon.")
                    },
                    {
                        "label": self.tr("pixelValue"),
                        "expressionText": "raster[]:pixelValue",
                        "helpText": self.tr("Check if one pixel value of a raster data satisfies the condition. Only usable with raster data")
                    },
                    {
                        "label": self.tr("percentOfValues"),
                        "expressionText": "raster[]:percentOfValues()",
                        "helpText": self.tr("Check if a specified percentage of pixel values satisfy the condition. Only usable with raster data")
                        
                    },
                ],
            },
            "Distances": {
                "label": self.tr("Distances"),
                "helpText": self.tr("This group contains distances to use in the cost calculation."),
                "expressions": [
                    {
                        "label": "euclidean",
                        "expressionText": "euclidean",
                        "helpText": self.tr("Calculates the euclidean metric.")
                    },
                    {
                        "label": "manhattan",
                        "expressionText": "manhattan",
                        "helpText": self.tr("Calculates the manhattan metric.")
                    },
                    {
                        "label": "geodesic",
                        "expressionText": "geodesic",
                        "helpText": self.tr("Calculates the geodesic metric.")
                    },
                    {
                        "label": "ellipsoidal",
                        "expressionText": "ellipsoidal",
                        "helpText": self.tr("Calculates the ellipsoidal distance")
                        
                    },
                ],
            },
            "Fields": {
                "label": self.tr("Fields"),
                "helpText": self.tr("This group contains numeric fields from the selected vector layer."),
                "expressions": [],
            },
            "Math": {
                "label": self.tr("Math"),
                "helpText": self.tr("This group contains math functions."),
                "expressions": [
                    {
                        "label": "acos",
                        "expressionText": " math.acos( )",
                        "helpText": self.tr("Returns the inverse cosine of a value in radians.")
                    },
                    {
                        "label": "acosh",
                        "expressionText": " math.acosh( )",
                        "helpText": self.tr("Returns the inverse hyperbolic cosine of a value in radians.")
                    },
                    {
                        "label": "asin",
                        "expressionText": " math.asin( )",
                        "helpText": self.tr("Returns the arc sine of a value in radians.")
                    },
                    {
                        "label": "asinh",
                        "expressionText": " math.asinh( )",
                        "helpText": self.tr("Returns the inverse hyperbolic sine of a value in radians.")
                    },
                    {
                        "label": "atan",
                        "expressionText": " math.atan( )",
                        "helpText": self.tr("Returns the arc tangent of a value in radians.")
                    },
                    {
                        "label": "atan2",
                        "expressionText": " math.atan2( )",
                        "helpText": self.tr("Returns the arc tangent of y, x values in radians.")
                    },
                    {
                        "label": "ceil",
                        "expressionText": " math.ceil( )",
                        "helpText": self.tr("Rounds a number upwards.")
                    },
                    {
                        "label": "comb",
                        "expressionText": " math.comb( )",
                        "helpText": self.tr("Returns number of ways to choose k items from n items without repetition and without "
                                    "order.")
                    },
                    {
                        "label": "copysign",
                        "expressionText": " math.copysign( )",
                        "helpText": self.tr("Return a float with the magnitude of x but the sign of y.")
                    },
                    {
                        "label": "cos",
                        "expressionText": " math.cos( )",
                        "helpText": self.tr("Returns cosine of an angle.")
                    },
                    {
                        "label": "cosh",
                        "expressionText": " math.cosh( )",
                        "helpText": self.tr("Returns the hyperbolic cosine of an angle.")
                    },
                    {
                        "label": "degrees",
                        "expressionText": " math.degrees( )",
                        "helpText": self.tr("Converts from radians to degrees.")
                    },
                    {
                        "label": "dist",
                        "expressionText": " math.dist( )",
                        "helpText": self.tr("Returns the Euclidean distance between two points.")
                    },
                    {
                        "label": "erf",
                        "expressionText": " math.erf( )",
                        "helpText": self.tr("Returns the error function of a value.")
                    },
                    {
                        "label": "erfc",
                        "expressionText": " math.erfc( )",
                        "helpText": self.tr("Returns the complementary error function of a value.")
                    },
                    {
                        "label": "exp",
                        "expressionText": " math.exp( )",
                        "helpText": self.tr("Returns exponential of an value.")
                    },
                    {
                        "label": "expm1",
                        "expressionText": " math.expm1( )",
                        "helpText": self.tr("Returns E**x - 1.")
                    },
                    {
                        "label": "fabs",
                        "expressionText": " math.fabs( )",
                        "helpText": self.tr("Returns the absolute value of a value.")
                    },
                    {
                        "label": "factorial",
                        "expressionText": " math.factorial( )",
                        "helpText": self.tr("Returns the factorial of a value.")
                    },
                    {
                        "label": "floor",
                        "expressionText": " math.floor( )",
                        "helpText": self.tr("Rounds a number downwards.")
                    },
                    {
                        "label": "fmod",
                        "expressionText": " math.fmod( )",
                        "helpText": self.tr("Returns the modulo of a value.")
                    },
                    {
                        "label": "frexp",
                        "expressionText": " math.frexp( )",
                        "helpText": self.tr("Returns the mantissa and the exponent of a value.")
                    },                   
                    {
                        "label": "gamma",
                        "expressionText": " math.gamma( )",
                        "helpText": self.tr("Returns the gamma function at x.")
                    },                                                 
                    {
                        "label": "isfinite",
                        "expressionText": " math.isfinite( )",
                        "helpText": self.tr("Checks whether a number is finite.")
                    },
                    {
                        "label": "isinf",
                        "expressionText": " math.isinf( )",
                        "helpText": self.tr("Checks whether a number is infinite.")
                    },
                    {
                        "label": "isnan",
                        "expressionText": " math.isnan( )",
                        "helpText": self.tr("Checks whether a value is NaN (not a number).")
                    },
                    {
                        "label": "isqrt",
                        "expressionText": " math.isqrt( )",
                        "helpText": self.tr("Rounds a square root number downwards to the nearest integer.")
                    },
                    {
                        "label": "ldexp",
                        "expressionText": " math.ldexp( )",
                        "helpText": self.tr("Returns the inverse of frexp() which is x * (2**i) of the given numbers x and i.")
                    },
                    {
                        "label": "lgamma",
                        "expressionText": " math.lgamma( )",
                        "helpText": self.tr("Returns the log gamma value of x.")
                    },
                    {
                        "label": "log",
                        "expressionText": " math.log( )",
                        "helpText": self.tr("Returns the value of the logarithm of the passed value and base.")
                    },
                    {
                        "label": "log10",
                        "expressionText": " math.log10( )",
                        "helpText": self.tr("Returns the value of the base 10 logarithm of the passed expression.")
                    },
                    {
                        "label": "log1p",
                        "expressionText": " math.log1p( )",
                        "helpText": self.tr("Returns the value of the natural logarithm of 1+x.")
                    },
                    {
                        "label": "log2",
                        "expressionText": " math.log2( )",
                        "helpText": self.tr("Returns the value of the base 2 logarithm.")
                    },                  
                    {
                        "label": "pow",
                        "expressionText": " math.pow( )",
                        "helpText": self.tr("Returns the value of x to the power of y")
                    },                  
                    {
                        "label": "radians",
                        "expressionText": " math.radians( )",
                        "helpText": self.tr("Converts from degrees to radians.")
                    },                    
                    {
                        "label": "remainder",
                        "expressionText": " math.remainder( )",
                        "helpText": self.tr("Returns the IEEE 754-style remainder of x with respect to y")
                    },
                    {
                        "label": "sin",
                        "expressionText": " math.sin( )",
                        "helpText": self.tr("Returns the sine of an angle.")
                    },
                    {
                        "label": "sinh",
                        "expressionText": " math.sinh( )",
                        "helpText": self.tr("Returns the hyperbolic sine of angle.")
                    },
                    {
                        "label": "sqrt",
                        "expressionText": " math.sqrt( )",
                        "helpText": self.tr("Returns square root of a value.")
                    },
                    {
                        "label": "tan",
                        "expressionText": " math.tan( )",
                        "helpText": self.tr("Returns the tangent of an angle.")
                    },
                    {
                        "label": "tanh",
                        "expressionText": " math.tanh( )",
                        "helpText": self.tr("Returns the hyperbolic tangent of an angle.")
                    },
                    {
                        "label": "trunc",
                        "expressionText": " math.trunc( )",
                        "helpText": self.tr("Returns the truncated integer part of a value.")
                    },
                ],
            },
            "Random": {
                "label": self.tr("Random value"), 
                "helpText": self.tr("Create a random value between two defined values"),
                "expressions": [
                    {
                        "label": "Random function",
                        "expressionText": "random(value1, value2)",
                        "helpText": self.tr("Random value between value1 and value2")
                    },                           
                ]
            },
            "Operators": {
                "label": self.tr("Operators"),
                "helpText": self.tr("This group contains several common operators."),
                "expressions": [
                    {
                        "label": "+",
                        "expressionText": " + ",
                        "helpText": self.tr("Addition of two values.")
                    },
                    {
                        "label": "-",
                        "expressionText": " - ",
                        "helpText": self.tr("Subtraction of two values.")
                    },
                    {
                        "label": "*",
                        "expressionText": " * ",
                        "helpText": self.tr("Multiplication of two values.")
                    },
                    {
                        "label": "/",
                        "expressionText": " / ",
                        "helpText": self.tr("Division of two values.")
                    },
                    {
                        "label": "[]",
                        "expressionText": "[ ]",
                        "helpText": self.tr("Index operator.")
                    },
                    {
                        "label": "(",
                        "expressionText": "(",
                        "helpText": self.tr("Opening round bracket.")
                    },
                    {
                        "label": ")",
                        "expressionText": ")",
                        "helpText": self.tr("Closing round bracket.")
                    },
                    {
                        "label": "and",
                        "expressionText": " and ",
                        "helpText": self.tr("Returns 1 when condition a and b are true.")
                    },
                    {
                        "label": "or",
                        "expressionText": " or ",
                        "helpText": self.tr("Returns 1 when condition a or b is true.")
                    },
                    {
                        "label": "<",
                        "expressionText": " < ",
                        "helpText": self.tr("Compares two values and evaluates to 1 if the left value is less than the right value.")
                    },
                    {
                        "label": ">",
                        "expressionText": " > ",
                        "helpText": self.tr("Compares two values and evaluates to 1 if the left value is greater than the right "
                                    "value.")
                    },
                    {
                        "label": "<=",
                        "expressionText": " <= ",
                        "helpText": self.tr("Compares two values and evaluates to 1 if the left value is less or equal to the right value.")                                               
                    },
                    {
                        "label": ">=",
                        "expressionText": " >= ",
                        "helpText": self.tr("Compares two values and evaluates to 1 if the left value is greater or equal to the right value.")   
                    },
                    {
                        "label": "==",
                        "expressionText": " == ",
                        "helpText": self.tr("Compares two values and evaluates to 1 if they are equal.")
                    },
                    {
                        "label": "!=",
                        "expressionText": " != ",
                        "helpText": self.tr("Compares two values and evaluates to 1 if they are unequal.")
                    },
                ],
            },
            "Polygons": {
                "label": self.tr("Polygons"),
                "helpText": self.tr("This group contains the selected polygon layers."),
                "expressions": [],
            },
            "Raster Data": {
                "label": self.tr("Raster Data"),
                "helpText": self.tr("This group contains the selected raster data."),
                "expressions": [],
            },
            "Raster": {
                "label": self.tr("Raster"),
                "helpText": self.tr("This group contains raster functions which calculate raster statistics and values for each edge."),
                "expressions": [
                    {
                        "label": "sum",
                        "expressionText": "sum",
                        "helpText": self.tr("Returns the raster sum of an edge.")
                    },
                    {
                        "label": "mean",
                        "expressionText": "mean",
                        "helpText": self.tr("Returns the raster mean of an edge.")
                    },
                    {
                        "label": "median",
                        "expressionText": "median",
                        "helpText": self.tr("Returns the raster median of an edge.")
                    },
                    {
                        "label": "min",
                        "expressionText": "min",
                        "helpText": self.tr("Returns the raster minimum of an edge.")
                    },
                    {
                        "label": "max",
                        "expressionText": "max",
                        "helpText": self.tr("Returns the raster maximum of an edge.")
                    },
                    {
                        "label": "variance",
                        "expressionText": "variance",
                        "helpText": self.tr("Returns the raster variance of an edge.")
                    },
                    {
                        "label": "standDev",
                        "expressionText": "standDev",
                        "helpText": self.tr("Returns the raster standard deviation of an edge.")
                    },
                    {
                        "label": "gradientSum",
                        "expressionText": "gradientSum",
                        "helpText": self.tr("Returns the raster gradient sum of an edge.")
                    },
                    {
                        "label": "gradientMin",
                        "expressionText": "gradientMin",
                        "helpText": self.tr("Returns the raster gradient minimum of an edge.")
                    },
                    {
                        "label": "gradientMax",
                        "expressionText": "gradientMax",
                        "helpText": self.tr("Returns the raster variance of an edge.")
                    },
                    {
                        "label": "ascent",
                        "expressionText": "ascent",
                        "helpText": self.tr("Returns the raster ascent of an edge.")
                    },
                    {
                        "label": "descent",
                        "expressionText": "descent",
                        "helpText": self.tr("Returns the raster descent of an edge.")
                    },
                    {
                        "label": "totalClimb",
                        "expressionText": "totalClimb",
                        "helpText": self.tr("Returns the raster total climb of an edge.")
                    },
                ],
            },
        }
        self.fieldHelpText = self.tr("Double-click to add field to expression editor.")
        self.polygonsHelpText = self.tr("Double-click to add polygon layer to expression editor.")
        self.rasterDataHelpText = self.tr("Double-click to add raster data to expression editor.")

    def getGroupExpressionItems(self, group):
        """
        Collects all expressions items of a group
        :param group:
        :return: list of QgsExpressionItem
        """
        groupExpressionItems = []
        for expression in self.groups.get(group, {}).get("expressions", []):
            label = expression.get("label", "")
            helpText = expression.get("helpText", "")
            expressionItem = QgsExpressionItem(label,
                                               expression.get("expressionText", ""),
                                               self.formatHelpText(group, label, helpText),
                                               QgsExpressionItem.ItemType.Expression
                                               )
            groupExpressionItems.append(expressionItem)

        return groupExpressionItems

    def getGroupItem(self, group):
        """
        Creates the corresponding group item
        :param group:
        :return:
        """
        groupLabel = self.groups.get(group, {}).get("label", group)
        return QgsExpressionItem(groupLabel, "", self.getGroupHelpText(group), QgsExpressionItem.ItemType.Group)

    def getFieldItem(self, group, field):
        """
        Returns a field expression item
        :param group: name of field group
        :param field: name of field
        :return:
        """
        return QgsExpressionItem(field, " field:" + field + " ",
                                 self.formatHelpText(group, field, self.fieldHelpText),
                                 QgsExpressionItem.ItemType.Expression)

    def getPolygonItem(self, group, label, polygonIndex):
        """
        Returns a polygon expression item
        :param polygonIndex: array index of polygon layer
        :param group: name of field group
        :param label: label of polygon
        :return:
        """
        return QgsExpressionItem(label, " polygon[{}]:".format(polygonIndex),
                                 self.formatHelpText(group, label, self.polygonsHelpText),
                                 QgsExpressionItem.ItemType.Expression)

    def getRasterDataItem(self, group, label, rasterIndex):
        """
        Returns a raster expression item
        :param rasterIndex: array index of raster data
        :param group: name of field group
        :param label: label of raster data
        :return:
        """
        return QgsExpressionItem(label, " raster[{}]:".format(rasterIndex),
                                 self.formatHelpText(group, label, self.rasterDataHelpText),
                                 QgsExpressionItem.ItemType.Expression)

    def formatHelpText(self, group, expression, helpText):
        """
        Formats the help text by appending a title to the text.
        :param expression: name of expression
        :param group:
        :param helpText:
        :return:
        """
        # set help title
        title = self.tr("expression {}").format(expression)
        if group == "Conditionals" or group == "Math" or group == "Raster":
            title = self.tr("function {}").format(expression)
        elif group == "Distances":
            title = self.tr("distance {}").format(expression)
        elif group == "Operators":
            title = self.tr("operator {}").format(expression)
        elif group == "Fields" or group == "Raster Data" or group == "Polygons":
            title = self.tr("group {}").format(group)

        return "<h2>{}</h2><p>{}</p>".format(html.escape(title), helpText)

    def getGroupHelpText(self, group):
        groupLabel = self.groups.get(group, {}).get("label", group)
        groupHelpText = self.groups.get(group, {}).get("helpText", "")
        title = self.tr("group {}").format(groupLabel)

        return "<h2>{}</h2><p>{}</p>".format(html.escape(title), groupHelpText)


QgsCostFunctionDialogUi, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'QgsCostFunctionDialog.ui'))


class QgsCostFunctionDialog(QtWidgets.QDialog, QgsCostFunctionDialogUi):
    """
    Advanced cost function editor
    """
    costFunctionChanged = pyqtSignal()

    def __init__(self, parent=None, vectorLayer=None, rasterData=None, polygonLayers=None):
        """
        Constructor
        :type rasterData: Array of raster inputs and each input is a tuple: (layer, band)
        :param parent:
        :param vectorLayer: Vector layer which fields are shown in the tree view
        """
        super(QgsCostFunctionDialog, self).__init__(parent)
        self.setupUi(self)

        self.vectorLayer = vectorLayer
        self.rasterData = rasterData
        self.polygonLayers = polygonLayers

        self.codeEditor.setWrapMode(QsciScintilla.WrapWord)

        # syntax highlighting
        # self.codeEditor.setLexer(QsciLexerPython())

        self.codeEditor.textChanged.connect(self.costFunctionChanged)
        # set up syntax check showing in status
        self.codeEditor.textChanged.connect(self._updateStatusText)

        operatorPushButtons = self.operatorButtonBox.findChildren(QPushButton)
        for operatorButton in operatorPushButtons:
            operatorButton.clicked.connect(self._operatorButtonClicked)

        # expression context
        self.expressionContext = QgsExpressionContext()

        # set up tree view
        self.treeModel = QStandardItemModel()
        self.expressionGroups = {}
        self.expressionTreeView.setModel(self.treeModel)
        self.expressionTreeView.setSortingEnabled(True)
        self.expressionTreeView.sortByColumn(0, Qt.AscendingOrder)
        self.expressionTreeView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.expressionTreeView.doubleClicked.connect(self._treeItemDoubleClicked)

        # change help text if item is changed
        self.expressionTreeView.selectionModel().currentChanged.connect(self._changeItemHelpText)
        self.setStatus("No function is set")

        # show initial help text
        self.setHelpText(
            """
            <h1>Cost Function Builder</h1>
            <p>The builder provides an easy method for creating cost functions.</p>
            <h2>Usage</h2>
            <p>On the left side there is the editor where the cost function can be entered. Below the editor are buttons 
            with the most common functions. In the center there is a list of all available expressions that can 
            be used in the cost function.</p>
            <h2>Example</h2>
            <p>if(field:ELEV > 100; raster[0]:sum; raster[0]:min)</p>
            """
        )

        self._loadTreeViewItems()

    def _updateStatusText(self):
        """
        Performs syntax check and shows status
        :return:
        """
        costFunction = self.costFunction()
        if not costFunction:
            statusText = "No function is set"
        else:
            fields = self.getVectorLayer().fields() if self.getVectorLayer() else []            
            if self.rasterData == None:
                numberOfRasterData = 100
            else:
                numberOfRasterData = len(self.rasterData)    
            polygonsSet = self.polygonLayers is not None
            statusText = GraphBuilder.syntaxCheck(costFunction, fields, numberOfRasterData, polygonsSet)[0]
        self.setStatus(statusText)

    def _treeItemDoubleClicked(self, modelIndex):
        """
        Inserts the corresponding expression code into the code editor
        :param modelIndex: Index of tree item
        :return:
        """
        item = self.treeModel.itemFromIndex(modelIndex)

        if not item:
            return

        if item.getItemType() is QgsExpressionItem.ItemType.Group:
            return

        self.insertEditorText(item.getExpressionText())

    def _addTreeItem(self, group, item, icon=None):
        """
        Adds an expression item to the tree view
        :param group: tree view group
        :param item: QgsExpressionItem to append
        :param icon: icon in tree view
        :return:
        """
        if icon:
            item.setIcon(icon)

        # if group already exists
        if group in self.expressionGroups:
            groupItem = self.expressionGroups[group]
            groupItem.appendRow(item)
        else:
            # otherwise create new group item
            groupItem = self.expressionContext.getGroupItem(group)
            self.expressionGroups[group] = groupItem
            groupItem.appendRow(item)
            self.treeModel.appendRow(groupItem)

    def _loadTreeViewItems(self):
        """
        Loads all expressions from the QgsExpressionContext class into the tree view
        :return:
        """
        self.treeModel.clear()
        self.expressionGroups.clear()

        # Conditionals
        group = "Conditionals"
        conditionalItems = self.expressionContext.getGroupExpressionItems(group)
        for item in conditionalItems:
            self._addTreeItem(group, item)

        # Distances
        group = "Distances"
        distanceItems = self.expressionContext.getGroupExpressionItems(group)
        for item in distanceItems:
            self._addTreeItem(group, item)

        # Vector Fields
        group = "Fields"
        if self.vectorLayer:
            fields = self.vectorLayer.fields()
            for index in range(fields.count()):
                field = fields.field(index)
                if field.type() != QVariant.String:
                    self._addTreeItem(group, self.expressionContext.getFieldItem(group, field.name()),
                                      fields.iconForField(index))

        # Math
        group = "Math"
        mathItems = self.expressionContext.getGroupExpressionItems(group)
        for item in mathItems:
            self._addTreeItem(group, item)

        group = "Random"
        randomItems = self.expressionContext.getGroupExpressionItems(group)
        for item in randomItems:
            self._addTreeItem(group, item)    


        # Operators
        group = "Operators"
        operatorItems = self.expressionContext.getGroupExpressionItems(group)
        for item in operatorItems:
            self._addTreeItem(group, item)

        # Polygons
        group = "Polygons"
        if self.polygonLayers:
            for index, layer in enumerate(self.polygonLayers):
                self._addTreeItem(group, self.expressionContext.getPolygonItem(group, layer.name(), index))

        # Raster Data
        group = "Raster Data"
        if self.rasterData:
            for index in range(len(self.rasterData)):
                rasterLayer, rasterBand = self.rasterData[index]
                self._addTreeItem(group, self.expressionContext.getRasterDataItem(group, "{layer} ({band})".format(
                    layer=rasterLayer.name(), band=rasterLayer.bandName(rasterBand)), index))

        # Raster Expressions
        group = "Raster"
        rasterItems = self.expressionContext.getGroupExpressionItems(group)
        for item in rasterItems:
            self._addTreeItem(group, item)

    def _operatorButtonClicked(self):
        """
        Handles the operator buttons
        :return:
        """
        button = self.sender()
        text = button.text()
        # add brackets to if text
        if "if" == text:
            text = "if( ; ; )"
        self.insertEditorText(" " + text + " ")

    def _changeItemHelpText(self, currentItemIndex, previousItemIndex):
        """
        Displays the help text of the selected expression
        :param currentItemIndex:
        :param previousItemIndex:
        :return:
        """
        item = self.treeModel.itemFromIndex(currentItemIndex)
        if not item:
            return

        self.setHelpText(item.getHelpText())

    def setVectorLayer(self, vectorLayer):
        self.vectorLayer = vectorLayer
        self._loadTreeViewItems()
        self._updateStatusText()

    def setRasterData(self, rasterData):
        """
        Sets the raster data
        :param rasterData: Raster data
        :type rasterData: Array of raster inputs and each input is a tuple: (layer, band)
        :return:
        """
        self.rasterData = rasterData
        self._loadTreeViewItems()

    def getVectorLayer(self):
        return self.vectorLayer

    def setPolygonLayers(self, polygonLayers):
        self.polygonLayers = polygonLayers
        self._loadTreeViewItems()

    def costFunction(self):
        return self.codeEditor.text()

    def setCostFunction(self, costFunction):
        self.codeEditor.setText(costFunction)
        self.codeEditor.setFocus()

    def insertEditorText(self, text):
        self.codeEditor.insertText(text)
        self.codeEditor.setFocus()

    def setHelpText(self, text):
        self.helpText.setText(text)

    def setStatus(self, text):
        """
        Sets an status information for the user
        :param text:
        :return:
        """
        self.statusText.setText(text)
