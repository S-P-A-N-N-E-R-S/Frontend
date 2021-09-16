import os
from enum import Enum
import html

from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal, Qt, QVariant, QObject
from qgis.PyQt.QtWidgets import QPushButton, QAbstractItemView
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel, QColor
from qgis.PyQt.Qsci import QsciScintilla, QsciLexerPython

from qgis.core import QgsVectorLayer

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
                "description": self.tr("This group contains functions to handle conditional checks in expressions."),
                "expressions": [
                    {
                        "label": "if",
                        "expressionText": " if( ; ; ) ",
                        "description": self.tr("Tests a condition and returns a different result depending on the conditional check."),
                        "syntax": self.tr("if(condition; exprIfTrue; exprIfFalse)"),
                        "example": self.tr("if[field:ELEV > 100, raster[0]:sum, raster[0]:min]")
                    },
                    {
                        "label": self.tr("crossesPolygon"),
                        "expressionText": "crossesPolygon",
                        "description": self.tr("Checks whether an edge crosses a polygon.")
                    },
                    {
                        "label": self.tr("insidePolygon"),
                        "expressionText": "insidePolygon",
                        "description": self.tr("Checks whether an edge is inside a polygon.")
                    },
                    {
                        "label": self.tr("pixelValue"),
                        "expressionText": "raster[]:pixelValue",
                        "description": self.tr("Check if one pixel value of a raster data satisfies the condition. Only usable with raster data")
                    },
                    {
                        "label": self.tr("percentOfValues"),
                        "expressionText": "raster[]:percentOfValues()",
                        "description": self.tr("Check if a specified percentage of pixel values satisfy the condition. Only usable with raster data")
                        
                    },
                ],
            },
            "Distances": {
                "label": self.tr("Distances"),
                "description": self.tr("This group contains distances to use in the cost calculation."),
                "expressions": [
                    {
                        "label": "euclidean",
                        "expressionText": "euclidean",
                        "description": self.tr("Calculates the euclidean metric.")
                    },
                    {
                        "label": "manhattan",
                        "expressionText": "manhattan",
                        "description": self.tr("Calculates the manhattan metric.")
                    },
                    {
                        "label": "geodesic",
                        "expressionText": "geodesic",
                        "description": self.tr("Calculates the geodesic metric.")
                    },
                    {
                        "label": "ellipsoidal",
                        "expressionText": "ellipsoidal",
                        "description": self.tr("Calculates the ellipsoidal distance")
                        
                    },
                ],
            },
            "Fields": {
                "label": self.tr("Fields"),
                "description": self.tr("This group contains numeric fields from the selected vector layer."),
                "expressions": [],
            },
            "Math": {
                "label": self.tr("Math"),
                "description": self.tr("This group contains math functions."),
                "expressions": [
                    {
                        "label": "acos",
                        "expressionText": " math.acos( )",
                        "description": self.tr("Returns the inverse cosine of a value in radians."),
                        "syntax": self.tr("acos(value)"),
                        "example": self.tr("acos(0.5) → 1.0471975511966"),
                    },
                    {
                        "label": "acosh",
                        "expressionText": " math.acosh( )",
                        "description": self.tr("Returns the inverse hyperbolic cosine of a value in radians."),
                        "syntax": self.tr("acosh(value)"),
                        "example": self.tr("acosh(50) → 4.6050701709847"),
                    },
                    {
                        "label": "asin",
                        "expressionText": " math.asin( )",
                        "description": self.tr("Returns the arc sine of a value in radians."),
                        "syntax": self.tr("asin(value)"),
                        "example": self.tr("asin(1.0) → 1.5707963267949"),
                    },
                    {
                        "label": "asinh",
                        "expressionText": " math.asinh( )",
                        "description": self.tr("Returns the inverse hyperbolic sine of a value in radians."),
                        "syntax": self.tr("asinh(value)"),
                        "example": self.tr("asinh(50) → 4.6052701709914"),
                    },
                    {
                        "label": "atan",
                        "expressionText": " math.atan( )",
                        "description": self.tr("Returns the arc tangent of a value in radians."),
                        "syntax": self.tr("atan(value)"),
                        "example": self.tr("atan(0.5) → 0.463647609000806"),
                    },
                    {
                        "label": "atan2",
                        "expressionText": " math.atan2( )",
                        "description": self.tr("Returns the arc tangent of y, x values in radians."),
                        "syntax": self.tr("atan2(dy,dx)"),
                        "example": self.tr("atan2(1.0, 1.732) → 0.523611477769969"),
                    },
                    {
                        "label": "ceil",
                        "expressionText": " math.ceil( )",
                        "description": self.tr("Rounds a number upwards."),
                        "syntax": self.tr("ceil(value)"),
                        "example": self.tr("ceil(4.9) → 5"),
                    },
                    {
                        "label": "comb",
                        "expressionText": " math.comb( )",
                        "description": self.tr("Returns number of ways to choose k items from n items without repetition and without "
                                    "order."),
                        "syntax": self.tr("comb(n,k)"),
                        "example": self.tr("comb(7, 5) → 21"),
                    },
                    {
                        "label": "copysign",
                        "expressionText": " math.copysign( )",
                        "description": self.tr("Return a float with the magnitude of x but the sign of y."),
                        "syntax": self.tr("copysign(x,y)"),
                        "example": self.tr("copysign(-20, 14.75) → 20.0"),
                    },
                    {
                        "label": "cos",
                        "expressionText": " math.cos( )",
                        "description": self.tr("Returns cosine of an angle."),
                        "syntax": self.tr("cos(angle)"),
                        "example": self.tr("cos(1.571) → 0.000796326710733263"),
                    },
                    {
                        "label": "cosh",
                        "expressionText": " math.cosh( )",
                        "description": self.tr("Returns the hyperbolic cosine of an angle."),
                        "syntax": self.tr("cosh(angle)"),
                        "example": self.tr("cosh(1.571) → 2.5096472436284736"),
                    },
                    {
                        "label": "degrees",
                        "expressionText": " math.degrees( )",
                        "description": self.tr("Converts from radians to degrees."),
                        "syntax": self.tr("degrees(radians)"),
                        "example": self.tr("degrees(3.14159) → 180"),
                    },
                    {
                        "label": "dist",
                        "expressionText": " math.dist( )",
                        "description": self.tr("Returns the Euclidean distance between two points."),
                        "syntax": self.tr("dist(point1,point2)"),
                        "example": self.tr("dist([3,3], [6,12]) → 9.486832980505138"),
                    },
                    {
                        "label": "erf",
                        "expressionText": " math.erf( )",
                        "description": self.tr("Returns the error function of a value."),
                        "syntax": self.tr("erf(value)"),
                        "example": self.tr("erf(0.5) → 0.5204998778130465"),
                    },
                    {
                        "label": "erfc",
                        "expressionText": " math.erfc( )",
                        "description": self.tr("Returns the complementary error function of a value."),
                        "syntax": self.tr("erfc(value)"),
                        "example": self.tr("erfc(0.5) → 0.4795001221869535"),
                    },
                    {
                        "label": "exp",
                        "expressionText": " math.exp( )",
                        "description": self.tr("Returns exponential of an value."),
                        "syntax": self.tr("exp(value)"),
                        "example": self.tr("exp(1.0) → 2.71828182845905"),
                    },
                    {
                        "label": "expm1",
                        "expressionText": " math.expm1( )",
                        "description": self.tr("Returns exponential value of a value - 1."),
                        "syntax": self.tr("expm1(value)"),
                        "example": self.tr("expm1(10) → 22025.465794806718"),
                    },
                    {
                        "label": "fabs",
                        "expressionText": " math.fabs( )",
                        "description": self.tr("Returns the absolute value of a value."),
                        "syntax": self.tr("fabs(value)"),
                        "example": self.tr("fabs(-12.21) → 12.21"),
                    },
                    {
                        "label": "factorial",
                        "expressionText": " math.factorial( )",
                        "description": self.tr("Returns the factorial of a value."),
                        "syntax": self.tr("factorial(value)"),
                        "example": self.tr("factorial(7) → 5040"),
                    },
                    {
                        "label": "floor",
                        "expressionText": " math.floor( )",
                        "description": self.tr("Rounds a number downwards."),
                        "syntax": self.tr("floor(value)"),
                        "example": self.tr("floor(4.9) → 4"),
                    },
                    {
                        "label": "fmod",
                        "expressionText": " math.fmod( )",
                        "description": self.tr("Returns the modulo of x divided by y."),
                        "syntax": self.tr("fmod(x,y)"),
                        "example": self.tr("fmod(14, 4) → 2.0"),
                    },
                    {
                        "label": "frexp",
                        "expressionText": " math.frexp( )",
                        "description": self.tr("Returns the mantissa and the exponent of a value."),
                        "syntax": self.tr("frexp(value)"),
                        "example": self.tr("frexp(6) → (0.75, 3)"),
                    },                   
                    {
                        "label": "gamma",
                        "expressionText": " math.gamma( )",
                        "description": self.tr("Returns the gamma function at x."),
                        "syntax": self.tr("gamma(x)"),
                        "example": self.tr("gamma(10) → 362880.0"),
                    },                                                 
                    {
                        "label": "isfinite",
                        "expressionText": " math.isfinite( )",
                        "description": self.tr("Checks whether a number is finite."),
                        "syntax": self.tr("isfinite(number)"),
                        "example": self.tr("isfinite(float('inf')) → False"),
                    },
                    {
                        "label": "isinf",
                        "expressionText": " math.isinf( )",
                        "description": self.tr("Checks whether a number is infinite."),
                        "syntax": self.tr("isinf(number)"),
                        "example": self.tr("isfinite(float('inf')) → True"),
                    },
                    {
                        "label": "isnan",
                        "expressionText": " math.isnan( )",
                        "description": self.tr("Checks whether a value is NaN (not a number)."),
                        "syntax": self.tr("isnan(value)"),
                        "example": self.tr("isnan(20)) → False"),
                    },
                    {
                        "label": "isqrt",
                        "expressionText": " math.isqrt( )",
                        "description": self.tr("Rounds a square root number downwards to the nearest integer."),
                        "syntax": self.tr("isqrt(value)"),
                        "example": self.tr("isqrt(10)) → 3"),
                    },
                    {
                        "label": "ldexp",
                        "expressionText": " math.ldexp( )",
                        "description": self.tr("Returns the inverse of frexp() which is x * (2**i) of the given numbers x and i."),
                        "syntax": self.tr("ldexp(x,i)"),
                        "example": self.tr("ldexp(5, 3)) → 40.0"),
                    },
                    {
                        "label": "lgamma",
                        "expressionText": " math.lgamma( )",
                        "description": self.tr("Returns the log gamma value of x."),
                        "syntax": self.tr("lgamma(x)"),
                        "example": self.tr("lgamma(5)) → 3.178053830347945"),
                    },
                    {
                        "label": "log",
                        "expressionText": " math.log( )",
                        "description": self.tr("Returns the value of the logarithm of the passed value and base."),
                        "syntax": self.tr("log(base,value)"),
                        "example": self.tr("log(2, 32) → 5"),
                    },
                    {
                        "label": "log10",
                        "expressionText": " math.log10( )",
                        "description": self.tr("Returns the value of the base 10 logarithm of the passed expression."),
                        "syntax": self.tr("log10(value)"),
                        "example": self.tr("log10(1) → 0"),
                    },
                    {
                        "label": "log1p",
                        "expressionText": " math.log1p( )",
                        "description": self.tr("Returns the value of the natural logarithm of 1+x."),
                        "syntax": self.tr("log1p(x)"),
                        "example": self.tr("log1p(3) → 1.3862943611198906"),
                    },
                    {
                        "label": "log2",
                        "expressionText": " math.log2( )",
                        "description": self.tr("Returns the value of the base 2 logarithm of a value."),
                        "syntax": self.tr("log2(value)"),
                        "example": self.tr("log2(5) → 2.321928094887362"),
                    },                  
                    {
                        "label": "pow",
                        "expressionText": " math.pow( )",
                        "description": self.tr("Returns the value of x to the power of y"),
                        "syntax": self.tr("pow(x,y)"),
                        "example": self.tr("pow(4, 3) → 64.0"),
                    },                  
                    {
                        "label": "radians",
                        "expressionText": " math.radians( )",
                        "description": self.tr("Converts from degrees to radians."),
                        "syntax": self.tr("radians(degrees)"),
                        "example": self.tr("radians(180) → 3.14159"),
                    },                    
                    {
                        "label": "remainder",
                        "expressionText": " math.remainder( )",
                        "description": self.tr("Returns the IEEE 754-style remainder of x with respect to y"),
                        "syntax": self.tr("remainder(x,y)"),
                        "example": self.tr("remainder(5, 2) → 1.0"),
                    },
                    {
                        "label": "sin",
                        "expressionText": " math.sin( )",
                        "description": self.tr("Returns the sine of an angle."),
                        "syntax": self.tr("sin(angle)"),
                        "example": self.tr("sin(1.571) → 0.999999682931835"),
                    },
                    {
                        "label": "sinh",
                        "expressionText": " math.sinh( )",
                        "description": self.tr("Returns the hyperbolic sine of angle."),
                        "syntax": self.tr("sinh(angle)"),
                        "example": self.tr("sinh(0.4) → 0.4107523258028155"),
                    },
                    {
                        "label": "sqrt",
                        "expressionText": " math.sqrt( )",
                        "description": self.tr("Returns square root of a value."),
                        "syntax": self.tr("sqrt(value)"),
                        "example": self.tr("sqrt(9) → 3"),
                    },
                    {
                        "label": "tan",
                        "expressionText": " math.tan( )",
                        "description": self.tr("Returns the tangent of an angle."),
                        "syntax": self.tr("tan(angle)"),
                        "example": self.tr("tan(1.0) → 1.5574077246549"),
                    },
                    {
                        "label": "tanh",
                        "expressionText": " math.tanh( )",
                        "description": self.tr("Returns the hyperbolic tangent of an angle."),
                        "syntax": self.tr("tanh(angle)"),
                        "example": self.tr("tanh(1.0) → 0.7615941559557649"),
                    },
                    {
                        "label": "trunc",
                        "expressionText": " math.trunc( )",
                        "description": self.tr("Returns the truncated integer part of a value."),
                        "syntax": self.tr("trunc(value)"),
                        "example": self.tr("trunc(2.45) → 2"),
                    },
                ],
            },
            "Random": {
                "label": self.tr("Random value"), 
                "description": self.tr("Create a random value between two defined values"),
                "expressions": [
                    {
                        "label": "Random function",
                        "expressionText": "random(value1, value2)",
                        "description": self.tr("Random value between value1 and value2"),
                        "syntax": self.tr("random(value1,value2)"),
                        "example": self.tr("random(5, 60) → 6.4803846462162"),
                    },                           
                ]
            },
            "Operators": {
                "label": self.tr("Operators"),
                "description": self.tr("This group contains several common operators."),
                "expressions": [
                    {
                        "label": "+",
                        "expressionText": " + ",
                        "description": self.tr("Addition of two values.")
                    },
                    {
                        "label": "-",
                        "expressionText": " - ",
                        "description": self.tr("Subtraction of two values.")
                    },
                    {
                        "label": "*",
                        "expressionText": " * ",
                        "description": self.tr("Multiplication of two values.")
                    },
                    {
                        "label": "/",
                        "expressionText": " / ",
                        "description": self.tr("Division of two values.")
                    },
                    {
                        "label": "[]",
                        "expressionText": "[ ]",
                        "description": self.tr("Index operator.")
                    },
                    {
                        "label": "(",
                        "expressionText": "(",
                        "description": self.tr("Opening round bracket.")
                    },
                    {
                        "label": ")",
                        "expressionText": ")",
                        "description": self.tr("Closing round bracket.")
                    },
                    {
                        "label": "and",
                        "expressionText": " and ",
                        "description": self.tr("Returns 1 when condition a and b are true.")
                    },
                    {
                        "label": "or",
                        "expressionText": " or ",
                        "description": self.tr("Returns 1 when condition a or b is true.")
                    },
                    {
                        "label": "<",
                        "expressionText": " < ",
                        "description": self.tr("Compares two values and evaluates to 1 if the left value is less than the right value.")
                    },
                    {
                        "label": ">",
                        "expressionText": " > ",
                        "description": self.tr("Compares two values and evaluates to 1 if the left value is greater than the right "
                                    "value.")
                    },
                    {
                        "label": "<=",
                        "expressionText": " <= ",
                        "description": self.tr("Compares two values and evaluates to 1 if the left value is less or equal to the right value.")
                    },
                    {
                        "label": ">=",
                        "expressionText": " >= ",
                        "description": self.tr("Compares two values and evaluates to 1 if the left value is greater or equal to the right value.")
                    },
                    {
                        "label": "==",
                        "expressionText": " == ",
                        "description": self.tr("Compares two values and evaluates to 1 if they are equal.")
                    },
                    {
                        "label": "!=",
                        "expressionText": " != ",
                        "description": self.tr("Compares two values and evaluates to 1 if they are unequal.")
                    },
                ],
            },
            "Polygons": {
                "label": self.tr("Polygons"),
                "description": self.tr("This group contains the selected polygon layers."),
                "expressions": [],
            },
            "Raster Data": {
                "label": self.tr("Raster Data"),
                "description": self.tr("This group contains the selected raster data."),
                "expressions": [],
            },
            "Raster": {
                "label": self.tr("Raster"),
                "description": self.tr("This group contains raster functions which calculate raster statistics and values for each edge."),
                "expressions": [
                    {
                        "label": "sum",
                        "expressionText": "sum",
                        "description": self.tr("Returns the raster sum of an edge.")
                    },
                    {
                        "label": "mean",
                        "expressionText": "mean",
                        "description": self.tr("Returns the raster mean of an edge.")
                    },
                    {
                        "label": "median",
                        "expressionText": "median",
                        "description": self.tr("Returns the raster median of an edge.")
                    },
                    {
                        "label": "min",
                        "expressionText": "min",
                        "description": self.tr("Returns the raster minimum of an edge.")
                    },
                    {
                        "label": "max",
                        "expressionText": "max",
                        "description": self.tr("Returns the raster maximum of an edge.")
                    },
                    {
                        "label": "variance",
                        "expressionText": "variance",
                        "description": self.tr("Returns the raster variance of an edge.")
                    },
                    {
                        "label": "standDev",
                        "expressionText": "standDev",
                        "description": self.tr("Returns the raster standard deviation of an edge.")
                    },
                    {
                        "label": "gradientSum",
                        "expressionText": "gradientSum",
                        "description": self.tr("Returns the raster gradient sum of an edge.")
                    },
                    {
                        "label": "gradientMin",
                        "expressionText": "gradientMin",
                        "description": self.tr("Returns the raster gradient minimum of an edge.")
                    },
                    {
                        "label": "gradientMax",
                        "expressionText": "gradientMax",
                        "description": self.tr("Returns the raster variance of an edge.")
                    },
                    {
                        "label": "ascent",
                        "expressionText": "ascent",
                        "description": self.tr("Returns the raster ascent of an edge.")
                    },
                    {
                        "label": "descent",
                        "expressionText": "descent",
                        "description": self.tr("Returns the raster descent of an edge.")
                    },
                    {
                        "label": "totalClimb",
                        "expressionText": "totalClimb",
                        "description": self.tr("Returns the raster total climb of an edge.")
                    },
                ],
            },
        }
        self.fieldDescription = self.tr("Double-click to add field to expression editor.")
        self.polygonsDescription = self.tr("Double-click to add polygon layer to expression editor.")
        self.rasterDataDescription = self.tr("Double-click to add raster data to expression editor.")

    def getGroupExpressionItems(self, group):
        """
        Collects all expressions items of a group
        :param group:
        :return: list of QgsExpressionItem
        """
        groupExpressionItems = []
        for expression in self.groups.get(group, {}).get("expressions", []):
            label = expression.get("label", "")
            description = expression.get("description", "")
            syntax = expression.get("syntax", "")
            example = expression.get("example", "")
            expressionItem = QgsExpressionItem(label,
                                               expression.get("expressionText", ""),
                                               self.formatHelpText(group, label, description, syntax, example),
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
                                 self.formatHelpText(group, field, self.fieldDescription),
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
                                 self.formatHelpText(group, label, self.polygonsDescription),
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
                                 self.formatHelpText(group, label, self.rasterDataDescription),
                                 QgsExpressionItem.ItemType.Expression)

    def formatHelpText(self, group, expression, description, syntax="", example=""):
        """
        Formats the help text by appending a title to the text.
        :param expression: name of expression
        :param group:
        :param description:
        :return:
        """
        helpText = ""

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
        helpText += "<h2>" + html.escape(title) + "</h2>"

        # add description
        helpText += "<p>" + description + "</p>"

        if syntax:
            helpText += "<h3>Syntax</h3><p>" + syntax + "</p>"

        if example:
            helpText += "<h3>Example</h3><p>" + example + "</p>"

        return helpText

    def getGroupHelpText(self, group):
        groupLabel = self.groups.get(group, {}).get("label", group)
        groupDescription = self.groups.get(group, {}).get("description", "")
        title = self.tr("group {}").format(groupLabel)

        return "<h2>{}</h2><p>{}</p>".format(html.escape(title), groupDescription)


QgsCostFunctionDialogUi, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'QgsCostFunctionDialog.ui'))


class QgsCostFunctionDialog(QtWidgets.QDialog, QgsCostFunctionDialogUi):
    """
    Advanced cost function editor
    """
    costFunctionChanged = pyqtSignal()

    def __init__(self, parent=None, vectorLayer=None, rasterData=[], polygonLayers=[]):
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

        # set error indicator
        self.Error_INDICATOR_ID = 8
        self.codeEditor.indicatorDefine(QsciScintilla.SquiggleIndicator, self.Error_INDICATOR_ID)
        self.codeEditor.setIndicatorForegroundColor(QColor("red"), self.Error_INDICATOR_ID)

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
        Performs syntax check and shows status and error indicator
        :return:
        """
        costFunction = self.costFunction()
        self.clearErrorIndicator()
        if not costFunction:
            statusText = "No function is set"
        else:
            fields = self.getVectorLayer().fields() if self.getVectorLayer() else []            
           
            numberOfRasterData = len(self.rasterData)   
            statusText = GraphBuilder.syntaxCheck(costFunction, fields, numberOfRasterData, len(self.polygonLayers))[0]

            # todo: set indicator range with fillIndicatorRange (int lineFrom, int indexFrom, int lineTo, int indexTo, int indicatorNumber)
            # more details: https://www.riverbankcomputing.com/static/Docs/QScintilla/classQsciScintilla.html#a44d1c322098eb0cf44cf78e866ed80cb

            # self.codeEditor.fillIndicatorRange(0, 0, 0, 10, self.Error_INDICATOR_ID)

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

    def clearErrorIndicator(self):
        """ Removes all error indicators in editor"""
        numLines = self.codeEditor.lines()
        lengthLastLine= len(self.codeEditor.text(numLines-1))
        self.codeEditor.clearIndicatorRange(0, 0, numLines-1, lengthLastLine-1, self.Error_INDICATOR_ID)

    def setStatus(self, text):
        """
        Sets an status information for the user
        :param text:
        :return:
        """
        self.statusText.setText(text)
