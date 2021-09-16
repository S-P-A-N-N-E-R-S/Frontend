from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
import re


def __findClosingBracketIndex(functionPart, startIndex):
    stack = []
    closingBracketIndex = startIndex
    for i in functionPart:
        if i == "(":
            stack.append(i)
        elif i == ")":                                          
            stack.pop()    
            if len(stack) == 0:
                return closingBracketIndex                        
                  
        closingBracketIndex+=1

def formulaCheck(function, fields, numberOfRasterData, numberOfPolygons):
    """
    Checks if the function is valid and exchanges the brackets with other
    symbols to enable future analysis
    
    :type function: string
    :type fields: list of QgsFields
    :type numberOfRasterData: amount of raster layers used
    :type numberOfPolygons: amount of polygon layers used
    :return tuple (Error message, adjusted formula if valid else empty string)
    """
    costFunction = function.replace(" ", "").replace('"', '')
    
    function = function.replace(" ", "").replace('"', '')
    formulaParts = re.split("\+|-|\*|/", costFunction)
    possibleMetrics = ["euclidean", "manhattan", "geodesic", "ellipsoidal"]
    possibleRasterAnalysis = ["sum", "mean", "median", "min", "max", "variance", "standDev", "gradientSum", "gradientMin", "gradientMax", 
                               "ascent", "descent", "totalClimb", "spSum", "spMean", "spMedian",
                              "spMin", "spMax", "spVariance", "spStandDev",
                              "spGradientSum", "spGradientMin", "spGradientMax",
                              "spAscent", "spDescent", "spTotalClimb"]
    comparisonOperators = ["<",">","==",]
           
    possibleFields = []
    for field in fields:
        possibleFields.append(field.name())
    
    # check for invalid operands
    partCounter = 1            
    for i in range(len(formulaParts)):
        var = formulaParts[i]           
        if not (var in possibleMetrics or var.isnumeric() or "." in var or "if(" in var or "field:" in var or "math." in var or "raster[" in var or "random(" in var):
            toReturn = "Error at position " + str(partCounter) + ": Invalid operand "
            return (toReturn, "")          
        partCounter+=1
                                    
    # check parentheses
    openList = ["[","("]
    closeList = ["]",")"]
    stack = []
    for i in function:
        if i in openList:
            stack.append(i)
        elif i in closeList:
            pos = closeList.index(i)
            if((len(stack)>0) and openList[pos] == stack[len(stack)-1]):
                stack.pop()
            else:
                return ("Unbalanced parentheses", "")    
    if len(stack) != 0:
        return ("Unbalanced parentheses", "")        
        
    # check all random operands   
    partCounter = 1 
    found = True
    while(found):
        found = False    
        index = function.find("random(")
        if index != -1:
            found = True
            # replace brackets
            closingBracketIndex = __findClosingBracketIndex(function[index:], index)
            function = function[0:closingBracketIndex] + "&" + function[closingBracketIndex+1:]                                                        
            function = function.replace("random(","rnd?",1)               
            function = function[:index] + function[index:closingBracketIndex-2].replace(",","§") + function[closingBracketIndex-2:]                 
            searchMath = re.finditer('math\.[a-z]+\(.+?§.+?\)', function[index:closingBracketIndex])
            for matchObj in searchMath:                  
                function = function[:matchObj.start()] + function[matchObj.start():matchObj.end()].replace("§",",") + function[matchObj.end():]                          
            if not "§" in function[index:closingBracketIndex]:
                toReturn = "Error in random function " + str(partCounter) + ": Two values necessary"
                return (toReturn, "")
            randomRangeValues = function[index+4:closingBracketIndex-3].split("§")
            for v in randomRangeValues:                                  
                if not v.isnumeric() and not "." in v and not v in possibleMetrics and not "raster[" in v and not "math." in v and not "if(" in v:
                    toReturn = "Error in random function " + str(partCounter) + ": Invalid upper or lower bound"
                    return (toReturn, "")
            partCounter+=1
    
    # check all if constructs
    partCounter = 1 
    found = True
    while(found):
        found = False    
        index =  function.find("if(")
        if index != -1:
            found = True
            closingBracketIndex = __findClosingBracketIndex(function[index:], index)             
            function = function[0:closingBracketIndex] + "}" + function[closingBracketIndex+1:]                                                                                                                                               
            function = function[0:index] + function[index:].replace("(","{",1)                                              
            ifParts = function[index:closingBracketIndex].split(";")
            
            if "if(" in function[index:closingBracketIndex]:
                toReturn = 'Error in if construct ' + str(partCounter) + ': Nested if construct not allowed. Use "and/or" instead'
                return (toReturn, "")
            
            if not len(ifParts) == 3:
                toReturn = "Error in if construct " + str(partCounter) + ": Two values in if function necessary"
                return (toReturn, "")                             
                                     
            for part in ifParts:
                if len(part) == 0:
                    toReturn = "Error in if construct " + str(partCounter) + ": Values in if function necessary"
                    return (toReturn, "") 
                         
            compOpSearch = re.compile(r'<|>|==')
            res = compOpSearch.search(ifParts[0])
            if res == None:
                toReturn = "Error in if construct " + str(partCounter) + ": Missing comparison operator"               
                return (toReturn,"")
    
            # check percentOfValues operator
            findPercentOfValuesRegex = re.compile(r'percentOfValues\(?[0-9]*\)?')
            percentParts = findPercentOfValuesRegex.findall(ifParts[0])
            for percentPart in percentParts:
                if not "(" in percentPart or not ")" in percentPart:
                    toReturn = "Error in if construct " + str(partCounter) + ": Percentage value missing"   
                    return (toReturn, "")
                percent = percentPart.split("(")[1].split(")")[0]
                if not percent.isnumeric() or int(percent) < 0 or int(percent) > 100:
                    toReturn = "Error in if construct " + str(partCounter) + ": No valid integer number as percentage" 
                    return (toReturn, "")                                            
            
            andOrSeperatedParts = re.split("or|and", ifParts[0])
            for andOrPart in andOrSeperatedParts:              
                comparedOperands = re.split(r'<|>|==', andOrPart)
                
                if len(comparedOperands) != 2:
                    toReturn = "Error in if construct " + str(partCounter) + ": Missing comparison value" 
                    return (toReturn, "")
                if "if{" in comparedOperands[0]:
                    firstOperand = comparedOperands[0].split("if{")[1]
                else:
                    firstOperand = comparedOperands[0]    
                secondOperand = comparedOperands[1]
                secondOperand = secondOperand.replace("=","")
                possOperandsRegex = re.compile(r'field|polygon|math|raster|rnd|True|False|euclidean|manhattan|geodesic|ellipsoidal')
                res = possOperandsRegex.search(firstOperand)
                if res == None and not firstOperand.isnumeric():
                    toReturn = "Error in first operand of if construct " + str(partCounter) + ": Invalid first operand of comparison"
                    return (toReturn, "")                 
                res = possOperandsRegex.search(secondOperand)                              
                if res == None and not secondOperand.isnumeric():
                    toReturn = "Error in second operand of if construct " + str(partCounter) + ": Invalid second operand of comparison"
                    return (toReturn, "")
                 
                #check polygons set if polygon function used
                if "crossesPolygon" in firstOperand and secondOperand != "True" and secondOperand != "False":
                    toReturn = "Error in if construct " + str(partCounter) + ": crossesPolygon can only be compared to False or True"
                    return (toReturn, "")
                if "insidePolygon" in firstOperand and secondOperand != "True" and secondOperand != "False": 
                    toReturn = "Error in if construct " + str(partCounter) + ": insidePolygon can only be compared to False or True"
                    return (toReturn, "")                        
                      
            if not ifParts[1] in possibleMetrics and not "math" in ifParts[1] and not "raster" in ifParts[1] and not "rnd" in ifParts[1] and not ifParts[1].isnumeric() and not "." in ifParts[1]:
                toReturn = "Error in if construct " + str(partCounter) + ": Invalid true value"
                return (toReturn, "")        
            if not ifParts[2] in possibleMetrics and not "math" in ifParts[2] and not "raster" in ifParts[2] and not "rnd" in ifParts[2] and not ifParts[2].isnumeric() and not "." in ifParts[2]:
                toReturn = "Error in if construct " + str(partCounter) + ": Invalid false value"
                return (toReturn, "")      
            
            partCounter+=1                     
    
    # check all polygon constructs
    partCounter = 1
    regex = re.compile(r'polygon\[?[0-9]?\]?:?[A-z]*')
    res = regex.findall(function)
    for matchString in res:
        if not "[" in matchString or not "]" in matchString or not ":" in matchString:
            toReturn = "Error in polygon construct " + str(partCounter) + ": No index given"
            return (toReturn, "")
        number = matchString.split("[")[1].split("]")[0]
        if not number.isnumeric:
            toReturn = "Error in polygon construct " + str(partCounter) + ": No index given"
            return (toReturn, "")
        if number == "":
            toReturn = "Error in polygon construct " + str(partCounter) + ": No valid index given"
            return (toReturn, "")
        if int(number) >= numberOfPolygons or int(number) < 0:
            toReturn = "Error in polygon construct " + str(partCounter) + ": No valid index given"
            return (toReturn, "")
        if not ":crossesPolygon" in matchString and not ":insidePolygon" in matchString:
            toReturn = "Error in polygon construct " + str(partCounter) + ": Define valid analysis for polygons"
            return (toReturn, "")
        partCounter+=1
    
    # check math constructs    
    partCounter = 1                      
    regex = re.compile(r'math\..+\(?')
    res = regex.findall(function)
    for matchString in res: 
        if not "(" in matchString:
            toReturn = "Error in math construct " + str(partCounter) + ": No opening bracket"
            return (toReturn, "")
        partCounter+=1
    
    partCounter = 1 
    regex = re.compile(r'math\.[A-z]*')
    res = regex.findall(function)
    for matchString in res:                          
        pointSplit = matchString.split(".")[1]
        if pointSplit == "":
            toReturn = "Error in math construct " + str(partCounter) + ": No function specified"
            return (toReturn, "")
        partCounter+=1 
    
    partCounter = 1        
    regex = re.compile(r'math\.[a-z]*\(?')   
    res = regex.findall(function)
    for matchString in res: 
        if "(" in matchString:
            mathEvalTest1 = matchString + "10)"
        else:
            mathEvalTest1 = matchString + "(10)"                       
        checkTwoValuesRegex = re.compile(r'math\.[a-z]*\(?.*?\)')  
        checkTwoValuesRes = checkTwoValuesRegex.findall(function)
        for matchString2 in checkTwoValuesRes:
            if "," in matchString2:                                                  
                if "(" in matchString:
                    mathEvalTest2 = matchString + "10,10)"
                else:
                    mathEvalTest1 = matchString + "(10,10)"  
                try:                       
                    eval(mathEvalTest2)
                except:    
                    toReturn = "Error in math construct " + str(partCounter) + ": Unable to execute"                                         
                    return(toReturn, "")       
            else:
                try:
                    eval(mathEvalTest1)
                except:  
                    toReturn = "Error in math construct " + str(partCounter) + ": Unable to execute"                                        
                    return(toReturn, "")   
        partCounter+=1 
    
    partCounter = 1                         
    found = True
    while(found):
        found = False    
        regex = re.compile(r'math\.[a-z]+\(')            
        res = regex.search(function)            
        if res != None:                               
            index = res.start()                                      
            found = True                                                                                        
            closingBracketIndex = __findClosingBracketIndex(function[index:], index)                
            function = function[0:closingBracketIndex] + "$" + function[closingBracketIndex+1:]                                                                                                                                               
            function = function[0:index] + function[index:].replace("(","%",1) 
            if "math" in function[index+4:closingBracketIndex]:
                toReturn = "Error in math construct " + str(partCounter) + ": Nested construct" 
                return (toReturn, "")
            
            number = function[index:].split("$")[0].split("%")[1]
            
            # only one operand
            if not "," in number:              
                if not number.isnumeric() and not "field:" in number and not "raster" in number and not "." in number and not "rnd" in number and not "if" in number:
                    if not number in possibleMetrics:
                        toReturn = "Error in math construct " + str(partCounter) + ": At least one operand necessary" 
                        return (toReturn, "")
             
            # two operands
            if "," in number:
                multNumbers = number.split(",")
                if len(multNumbers) > 2:
                    toReturn = "Error in math construct " + str(partCounter) + ": Only operations with two variables supported"
                    return (toReturn, "")
                for n in multNumbers:                    
                    if not n.isnumeric() and not "field:" in n and not "raster" in n and not "random" in n and not "rnd" in n and not "if" in n:
                        if not n in possibleMetrics:
                            toReturn = "Error in math construct " + str(partCounter) + ": Invalid value" 
                            return(toReturn,"")                       
            partCounter+=1
                   
    # raster check    
    partCounter = 1       
    regex = re.compile(r'raster\[?[0-9]*\]?:?[A-z]*')
    res = regex.findall(function)
    for matchString in res:                      
        if not "[" in matchString:
            toReturn = "Error in raster analysis " + str(partCounter) + ": Index necessary to reference raster data"
            return (toReturn, "")
        partCounter+=1
     
    partCounter = 1           
    regex = re.compile(r'raster\[[0-9]*\]:?')
    res = regex.findall(function)
    for matchString in res:        
        rasterIndexNumber = matchString.split("[")[1].split("]")[0]
        if not rasterIndexNumber.isnumeric():
            toReturn = "Error in raster analysis " + str(partCounter) + ": Index necessary to reference raster data"
            return (toReturn, "")
        if not ":" in matchString:
            toReturn = "Error in raster analysis " + str(partCounter) + ": No analysis type defined"
            return(toReturn, "")
        
        if int(rasterIndexNumber) > numberOfRasterData-1 or int(rasterIndexNumber) < 0:
            toReturn = "Error in raster analysis " + str(partCounter) + ": Invalid index"
            return (toReturn,"")               
        partCounter+=1
    
    partCounter = 1
    regex = re.compile(r'raster\[[0-9]+\]:[A-z]*')
    res = regex.findall(function)
    for matchString in res:               
        analysisType = re.split("<|>|,|\)|=", matchString.split("]:")[1])[0]  
        if not analysisType in possibleRasterAnalysis and not "percentOfValues" in analysisType and not "pixelValue" in analysisType and not "spPercentOfValues" in analysisType and not "spPixelValue" in analysisType:
            toReturn = "Error in raster analysis " + str(partCounter) + ": Invalid raster analysis"
            return (toReturn, "")    
        partCounter+=1
         
    # check shortestPath operators
    partCounter = 1
    findspRegex = re.compile(r'sp[A-z]+\(?[0-9]*,?[0-9]*\)?')
    spParts = findspRegex.findall(function)
    for spPart in spParts:
        if not "(" in spPart or not ")" in spPart:
            toReturn = "Error in if construct " + str(partCounter) + ": Heuristic index for shortest path missing"   
            return (toReturn, "")
        heuristicIndex = spPart.split("(")[1].split(")")[0]
        if "," in heuristicIndex:
            heuristicIndex = heuristicIndex.split(",")[0]
            percentage = spPart.split(",")[1].split(")")[0]
            if not percentage.isnumeric() or int(percentage) < 0 or int(percentage) > 100:
                toReturn = "Error in if construct " + str(partCounter) + ": No valid integer number as percentage" 
                return (toReturn, "") 
        if not heuristicIndex.isnumeric() or int(heuristicIndex) < 0 or int(heuristicIndex) > 5:
            toReturn = "Error in if construct " + str(partCounter) + ": No valid integer number as heuristic index" 
            return (toReturn, "") 
        
        partCounter+=1
    
    percentPixelRegexList = ['(if\{)?raster\[[0-9]+\]:pixelValue', '(if\{)?raster\[[0-9]+\]:spPixelValue', '(if\{)?raster\[[0-9]+\]:percentOfValues', '(if\{)?raster\[[0-9]+\]:spPercentOfValues']        
    for regex in percentPixelRegexList:
        partCounter = 1
        regexCompiled = re.compile(regex)
        findPercentOrPixel = regexCompiled.findall(function)
        for part in findPercentOrPixel: 
            if not "if" in part:
                toReturn = "Error in raster analysis " + str(partCounter) + ": PixelValue analysis can only be used inside if construct"   
                return (toReturn, "")
            partCounter+=1
    
    # fields check
    partCounter = 1
    foundFieldConstruct = False 
    regex = re.compile(r'field:?')  
    res = regex.findall(function)
    for matchString in res:        
        foundFieldConstruct = True      
        if not ":" in matchString:
            toReturn = 'Error in field query ' + str(partCounter) + ': No ":" after field'
            return (toReturn, "")
        partCounter+=1
    
    partCounter = 1
    fieldSet = False  
    regex = re.compile(r'field:[A-z]+')   
    res = regex.findall(function)  
    for matchString in res: 
        fieldSet = True
        fieldName = matchString.split("field:")[1]
        if not fieldName in possibleFields:
            toReturn = 'Error in field query ' + str(partCounter) + ': Invalid field name'
            return (toReturn, "")    
        partCounter+=1
    
    if foundFieldConstruct == True and fieldSet == False:
        return ("No field name defined","")
    
    # if no error was returned the function is valid                    
    return ("No error found", function) 

