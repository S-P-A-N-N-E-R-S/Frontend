import os
from enum import Enum

from qgis.PyQt import uic, QtWidgets
from qgis.core import QgsVectorLayer

from PyQt5.QtCore import pyqtSignal, Qt, QVariant, QObject
from PyQt5.QtWidgets import QPushButton, QAbstractItemView
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from ...models.AdvancedCostCalculator import AdvancedCostCalculator


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
        self.expressions = {
            "Conditionals": [
                {
                    "label": "if",
                    "expressionText": " if( ) ",
                    "helpText": "Tests a condition and returns a different result depending on the conditional check."
                },
            ],
            "Distances": [
                {
                    "label": "euclidean",
                    "expressionText": "euclidean ",
                    "helpText": "Calculates the euclidean metric."
                },
                {
                    "label": "manhattan",
                    "expressionText": "manhattan ",
                    "helpText": "Calculates the manhattan metric."
                },
                {
                    "label": "geodesic",
                    "expressionText": "geodesic ",
                    "helpText": "Calculates the geodesic metric."
                },
            ],
            "Math": [
                {
                    "label": "acos",
                    "expressionText": " math.acos( ) ",
                    "helpText": "Returns the inverse cosine of a value in radians."
                },
                {
                    "label": "acosh",
                    "expressionText": " math.acosh( ) ",
                    "helpText": "Returns the inverse hyperbolic cosine of a value in radians."
                },
                {
                    "label": "asin",
                    "expressionText": " math.asin( ) ",
                    "helpText": "Returns the arc sine of a value in radians."
                },
                {
                    "label": "asinh",
                    "expressionText": " math.asinh( ) ",
                    "helpText": "Returns the inverse hyperbolic sine of a value in radians."
                },
                {
                    "label": "atan",
                    "expressionText": " math.atan( ) ",
                    "helpText": "Returns the arc tangent of a value in radians."
                },
                {
                    "label": "atan2",
                    "expressionText": " math.atan2( ) ",
                    "helpText": "Returns the arc tangent of y, x values in radians."
                },
                {
                    "label": "ceil",
                    "expressionText": " math.ceil( ) ",
                    "helpText": "Rounds a number upwards."
                },
                {
                    "label": "comb",
                    "expressionText": " math.comb( ) ",
                    "helpText": "Returns number of ways to choose k items from n items without repetition and without "
                                "order."
                },
                {
                    "label": "copysign",
                    "expressionText": " math.copysign( ) ",
                    "helpText": "Return a float with the magnitude of x but the sign of y."
                },
                {
                    "label": "cos",
                    "expressionText": " math.cos( ) ",
                    "helpText": "Returns cosine of an angle."
                },
                {
                    "label": "cosh",
                    "expressionText": " math.cosh( ) ",
                    "helpText": "Returns the hyperbolic cosine of an angle."
                },
                {
                    "label": "degrees",
                    "expressionText": " math.degrees( ) ",
                    "helpText": "Converts from radians to degrees."
                },
                {
                    "label": "dist",
                    "expressionText": " math.dist( ) ",
                    "helpText": "Returns the Euclidean distance between two points."
                },
                {
                    "label": "erf",
                    "expressionText": " math.erf( ) ",
                    "helpText": "Returns the error function of a value."
                },
                {
                    "label": "erfc",
                    "expressionText": " math.erfc( ) ",
                    "helpText": "Returns the complementary error function of a value."
                },
                {
                    "label": "exp",
                    "expressionText": " math.exp( ) ",
                    "helpText": "Returns exponential of an value."
                },
                {
                    "label": "expm1",
                    "expressionText": " math.expm1( ) ",
                    "helpText": "Returns E**x - 1."
                },
                {
                    "label": "fabs",
                    "expressionText": " math.fabs( ) ",
                    "helpText": "Returns the absolute value of a value."
                },
                {
                    "label": "factorial",
                    "expressionText": " math.factorial( ) ",
                    "helpText": "Returns the factorial of a value."
                },
                {
                    "label": "floor",
                    "expressionText": " math.floor( ) ",
                    "helpText": "Rounds a number downwards."
                },
                {
                    "label": "fmod",
                    "expressionText": " math.fmod( ) ",
                    "helpText": "Returns the modulo of a value."
                },
                {
                    "label": "frexp",
                    "expressionText": " math.frexp( ) ",
                    "helpText": "Returns the mantissa and the exponent of a value."
                },
                {
                    "label": "fsum",
                    "expressionText": " math.fsum( ) ",
                    "helpText": "Returns the sum of all items in an iterable."
                },
                {
                    "label": "gamma",
                    "expressionText": " math.gamma( ) ",
                    "helpText": "Returns the gamma function at x."
                },
                {
                    "label": "gcd",
                    "expressionText": " math.gcd( ) ",
                    "helpText": "Returns the greatest common divisor of two integers."
                },
                {
                    "label": "hypot",
                    "expressionText": " math.hypot( ) ",
                    "helpText": "Returns the Euclidean norm."
                },
                {
                    "label": "isclose",
                    "expressionText": " math.isclose( ) ",
                    "helpText": "Checks whether two values are close to each other, or not."
                },
                {
                    "label": "isfinite",
                    "expressionText": " math.isfinite( ) ",
                    "helpText": "Checks whether a number is finite."
                },
                {
                    "label": "isinf",
                    "expressionText": " math.isinf( ) ",
                    "helpText": "Checks whether a number is infinite."
                },
                {
                    "label": "isnan",
                    "expressionText": " math.isnan( ) ",
                    "helpText": "Checks whether a value is NaN (not a number)."
                },
                {
                    "label": "isqrt",
                    "expressionText": " math.isqrt( ) ",
                    "helpText": "Rounds a square root number downwards to the nearest integer."
                },
                {
                    "label": "ldexp",
                    "expressionText": " math.ldexp( ) ",
                    "helpText": "Returns the inverse of frexp() which is x * (2**i) of the given numbers x and i."
                },
                {
                    "label": "lgamma",
                    "expressionText": " math.lgamma( ) ",
                    "helpText": "Returns the log gamma value of x."
                },
                {
                    "label": "log",
                    "expressionText": " math.log( ) ",
                    "helpText": "Returns the value of the logarithm of the passed value and base."
                },
                {
                    "label": "log10",
                    "expressionText": " math.log10( ) ",
                    "helpText": "Returns the value of the base 10 logarithm of the passed expression."
                },
                {
                    "label": "log1p",
                    "expressionText": " math.log1p( ) ",
                    "helpText": "Returns the value of the natural logarithm of 1+x."
                },
                {
                    "label": "log2",
                    "expressionText": " math.log2( ) ",
                    "helpText": "Returns the value of the base 2 logarithm."
                },
                {
                    "label": "perm",
                    "expressionText": " math.perm( ) ",
                    "helpText": "Return the number of ways to choose k items from n items with order and without "
                                "repetition."
                },
                {
                    "label": "pow",
                    "expressionText": " math.pow( ) ",
                    "helpText": "Returns the value of x to the power of y"
                },
                {
                    "label": "prod",
                    "expressionText": " math.prod( ) ",
                    "helpText": "Returns the product of all the elements in an iterable."
                },
                {
                    "label": "radians",
                    "expressionText": " math.radians( ) ",
                    "helpText": "Converts from degrees to radians."
                },
                {
                    "label": "random",
                    "expressionText": " random ( ) ",
                    "helpText": "Returns a random number.",
                },
                {
                    "label": "remainder",
                    "expressionText": " math.remainder( ) ",
                    "helpText": "Returns the IEEE 754-style remainder of x with respect to y"
                },
                {
                    "label": "sin",
                    "expressionText": " math.sin( ) ",
                    "helpText": "Returns the sine of an angle."
                },
                {
                    "label": "sinh",
                    "expressionText": " math.sinh( ) ",
                    "helpText": "Returns the hyperbolic sine of angle."
                },
                {
                    "label": "sqrt",
                    "expressionText": " math.sqrt( ) ",
                    "helpText": "Returns square root of a value."
                },
                {
                    "label": "tan",
                    "expressionText": " math.tan( ) ",
                    "helpText": "Returns the tangent of an angle."
                },
                {
                    "label": "tanh",
                    "expressionText": " math.tanh( ) ",
                    "helpText": "Returns the hyperbolic tangent of an angle."
                },
                {
                    "label": "trunc",
                    "expressionText": " math.trunc( ) ",
                    "helpText": "Returns the truncated integer part of a value."
                },
            ],
            "Operators": [
                {
                    "label": "+",
                    "expressionText": " + ",
                    "helpText": "Addition of two values."
                },
                {
                    "label": "-",
                    "expressionText": " - ",
                    "helpText": "Subtraction of two values."
                },
                {
                    "label": "*",
                    "expressionText": " * ",
                    "helpText": "Multiplication of two values."
                },
                {
                    "label": "/",
                    "expressionText": " / ",
                    "helpText": "Division of two values."
                },
                {
                    "label": "[]",
                    "expressionText": "[ ]",
                    "helpText": "Index operator."
                },
                {
                    "label": "(",
                    "expressionText": " ( ",
                    "helpText": "Opening round bracket."
                },
                {
                    "label": ")",
                    "expressionText": " ) ",
                    "helpText": "Closing round bracket."
                },
                {
                    "label": "and",
                    "expressionText": " and ",
                    "helpText": "Returns 1 when condition a and b are true."
                },
                {
                    "label": "or",
                    "expressionText": " or ",
                    "helpText": "Returns 1 when condition a or b is true."
                },
                {
                    "label": "not",
                    "expressionText": " not ",
                    "helpText": "Negates a condition."
                },
                {
                    "label": "<",
                    "expressionText": " < ",
                    "helpText": "Compares two values and evaluates to 1 if the left value is less than the right value."
                },
                {
                    "label": ">",
                    "expressionText": " > ",
                    "helpText": "Compares two values and evaluates to 1 if the left value is greater than the right "
                                "value."
                },
                {
                    "label": "==",
                    "expressionText": " == ",
                    "helpText": "Compares two values and evaluates to 1 if they are equal."
                },
                {
                    "label": "!=",
                    "expressionText": " != ",
                    "helpText": "Compares two values and evaluates to 1 if they are unequal."
                },
            ],
            "Raster": [
                {
                    "label": "sum",
                    "expressionText": "sum ",
                    "helpText": "Returns the raster sum of an edge."
                },
                {
                    "label": "mean",
                    "expressionText": "mean ",
                    "helpText": "Returns the raster mean of an edge."
                },
                {
                    "label": "median",
                    "expressionText": "median ",
                    "helpText": "Returns the raster median of an edge."
                },
                {
                    "label": "min",
                    "expressionText": "min ",
                    "helpText": "Returns the raster minimum of an edge."
                },
                {
                    "label": "max",
                    "expressionText": "max ",
                    "helpText": "Returns the raster maximum of an edge."
                },
                {
                    "label": "variance",
                    "expressionText": "variance ",
                    "helpText": "Returns the raster variance of an edge."
                },
                {
                    "label": "standDev",
                    "expressionText": "standDev ",
                    "helpText": "Returns the raster standard deviation of an edge."
                },
                {
                    "label": "gradientSum",
                    "expressionText": "gradientSum ",
                    "helpText": "Returns the raster gradient sum of an edge."
                },
                {
                    "label": "gradientMin",
                    "expressionText": "gradientMin ",
                    "helpText": "Returns the raster gradient minimum of an edge."
                },
                {
                    "label": "gradientMax",
                    "expressionText": "gradientMax ",
                    "helpText": "Returns the raster variance of an edge."
                },
                {
                    "label": "ascent",
                    "expressionText": "ascent ",
                    "helpText": "Returns the raster ascent of an edge."
                },
                {
                    "label": "descent",
                    "expressionText": "descent ",
                    "helpText": "Returns the raster descent of an edge."
                },
                {
                    "label": "totalClimb",
                    "expressionText": "totalClimb ",
                    "helpText": "Returns the raster total climb of an edge."
                },
            ],
        }
        self.fieldHelpText = "Double-click to add field to expression editor."
        self.groupHelpTexts = {
            "Conditionals": "This group contains functions to handle conditional checks in expressions.",
            "Distances": "This group contains distances to use in the cost calculation.",
            "Fields": "This group contains numeric fields from the selected vector layer.",
            "Math": "This group contains math functions.",
            "Operators": "This group contains several common operators.",
            "Raster": "This group contains raster functions which calculate raster statistics and values for each edge.",
        }

    def getGroupExpressionItems(self, group):
        """
        Collects all expressions items of a group
        :param group:
        :return: list of QgsExpressionItem
        """
        groupExpressionItems = []
        for expression in self.expressions.get(group, []):
            label = expression.get("label", "")
            expressionItem = QgsExpressionItem(label,
                                               expression.get("expressionText", ""),
                                               self.formatHelpText(group, label, expression.get("helpText", "")),
                                               QgsExpressionItem.ItemType.Expression
                                               )
            groupExpressionItems.append(expressionItem)

        return groupExpressionItems

    def getFieldItem(self, group, field):
        """
        Returns a field expression item
        :param group: name of field group
        :param field: name of field
        :return:
        """
        return QgsExpressionItem(field, self.getFieldExpressionText(field), self.getFieldHelpText(group),
                                 QgsExpressionItem.ItemType.Expression)

    def getFieldExpressionText(self, field):
        return " field:" + field + " "

    def formatHelpText(self, group, expression, helpText):
        """
        Formats the help text by appending a title to the text.
        :param group:
        :param helpText:
        :return:
        """
        # set help title
        title = "expression {}".format(expression)
        if group == "Conditionals" or group == "Math" or group == "Raster":
            title = "function {}".format(expression)
        elif group == "Distances":
            title = "distance {}".format(expression)
        elif group == "Operators":
            title = "operator {}".format(expression)

        return "<h2>{}</h2><p>{}</p>".format(title, helpText)

    def getFieldHelpText(self, group):
        return "<h2>group {}</h2><p>{}</p>".format(group.lower(), self.fieldHelpText)

    def getGroupHelpText(self, group):
        return "<h2>group {}</h2><p>{}</p>".format(group.lower(), self.groupHelpTexts.get(group, ""))


QgsCostFunctionDialogUi, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'QgsCostFunctionDialog.ui'))


class QgsCostFunctionDialog(QtWidgets.QDialog, QgsCostFunctionDialogUi):
    """
    Advanced cost function editor
    """
    costFunctionChanged = pyqtSignal()

    def __init__(self, parent=None, vectorLayer=None):
        """
        Constructor
        :param parent:
        :param vectorLayer: Vector layer which fields are shown in the tree view
        """
        super(QgsCostFunctionDialog, self).__init__(parent)
        self.setupUi(self)

        self.vectorLayer = vectorLayer

        self.codeEditor.setWrapMode(QsciScintilla.WrapWord)

        # syntax highlighting
        # self.codeEditor.setLexer(QsciLexerPython())

        self.codeEditor.textChanged.connect(self.costFunctionChanged)

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

        self._loadTreeViewItems()

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
            groupItem = QgsExpressionItem(group, "", self.expressionContext.getGroupHelpText(group),
                                          QgsExpressionItem.ItemType.Group)
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

        # Operators
        group = "Operators"
        operatorItems = self.expressionContext.getGroupExpressionItems(group)
        for item in operatorItems:
            self._addTreeItem(group, item)

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
            text = "if [ ]"
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

    def getVectorLayer(self):
        return self.vectorLayer

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
