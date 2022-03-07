#  This file is part of the OGDF plugin.
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

from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
import re
import math


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


def __findConstructPosition(originalFunction, construct, index):

    searchResult = re.finditer(construct, originalFunction)
    counter = 1
    for match in searchResult:
        if counter == index:
            return (match.start(), match.end())
        counter+=1
                       
    

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
    
    originalFunction = function    
    costFunction = function.replace(" ", "").replace('"', '')  
    function = function.replace(" ", "").replace('"', '')
    
    formulaParts = re.split("\+|-|\*|/|;|<|>|==|or|,|!=", costFunction)
    possibleMetrics = ["euclidean", "manhattan", "geodesic", "ellipsoidal"]
    possibleRasterAnalysis = ["sum", "mean", "median", "min", "max", "variance", "standDev", "gradientSum", "gradientMin", "gradientMax", 
                               "ascent", "descent", "totalClimb", "spSum", "spMean", "spMedian", "spMin", "spMax", 
                              "spVariance", "spStandDev", "spGradientSum", "spGradientMin", "spGradientMax","spAscent",
                              "spDescent", "spTotalClimb", "spEuclidean", "spManhattan", "spGeodesic", "spEllipsoidal"]
    comparisonOperators = ["<",">","==",]
           
    possibleFields = []
    for field in fields:
        possibleFields.append(field.name())
    
    # check for invalid operands
    partCounter = 1
    for i in range(len(formulaParts)):        
        var = formulaParts[i].replace("(","").replace(")","").replace("=","")
        if var == "":
            toReturn = ("Missing operand", "", 0, len(originalFunction))      
            return toReturn
        if var in "euclidean" and len(var) < 9:
            toReturn = ("Invalid operand", "", 0, len(originalFunction))      
            return toReturn    
        if var in "manhattan" and len(var) < 9:
            toReturn = ("Invalid operand", "", 0, len(originalFunction))      
            return toReturn
        if var in "geodesic" and len(var) < 8:
            toReturn = ("Invalid operand", "", 0, len(originalFunction))      
            return toReturn
        if var in "ellipsoidal" and len(var) < 11:       
            toReturn = ("Invalid operand", "", 0, len(originalFunction))      
            return toReturn
        
        for metric in possibleMetrics:
            if metric in var and len(var) != len(metric):
                res = var.split(metric)[0]
                if not(any(res in s for s in possibleMetrics) or res == "True" or res == "False" or res.isnumeric() or "if" in res or "field:" in res or "math." in res or "raster[" in res or "random" in res or "polygon[" in var):
                    toReturn = ("Invalid operand", "", 0, len(originalFunction))      
                    return toReturn
        
        if not(any(var in s for s in possibleMetrics) or var == "True" or var == "False" or var.isnumeric() or "if" in var or "field:" in var or "math." in var or "raster[" in var or "random" in var or "polygon[" in var):      
            try:
                float(var)
            except:
                if "and" in var:
                    andSepParts = var.split("and")
                    for res in andSepParts:
                        if not(any(res in s for s in possibleMetrics) or res == "True" or res == "False" or res.isnumeric() or "if" in res or "field:" in res or "math." in res or "raster[" in res or "random" in res or "polygon[" in var):      
                            try:
                                float(res)
                            except:                                  
                                toReturn = ("Invalid operand", "", 0, len(originalFunction))      
                                return toReturn                  
                else:                                    
                    toReturn = ("Invalid operand", "", 0, len(originalFunction))      
                    return toReturn               
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
                return ("Unbalanced parentheses", "",0, len(originalFunction))    
    if len(stack) != 0:
        return ("Unbalanced parentheses", "",0, len(originalFunction))        
    
    # check no ü,ä,ö,§,$,%,&,?,~,# are used
    specialCharList = ["ü","ä","ö","§","$","%","&","{","}","&","?", "~","#"] 
    for char in function.lower():
        if char in specialCharList:
            toReturn = ("Forbidden special character used", "", 0, len(originalFunction))
            return toReturn
    
    # check brackets in if and random
    partCounter = 1
    regex = re.compile(r'if\(?')
    res = regex.findall(function)
    for matchString in res:
        if not "(" in matchString:
            errorPos = __findConstructPosition(originalFunction, "if", partCounter)               
            toReturn = ("Error in if construct: Missing opening bracket", "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1
            
    partCounter = 1
    regex = re.compile(r'random\(?')
    res = regex.findall(function)
    for matchString in res:
        if not "(" in matchString:
            errorPos = __findConstructPosition(originalFunction, "random", partCounter)               
            toReturn = ("Error in random function: Missing opening bracket", "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1
    
    # check all if constructs
    partCounter = 1 
    found = True
    while(found):
        found = False    
        index =  function.find("if(")
        if index != -1:
            found = True
            errorPos = __findConstructPosition(originalFunction, "if", partCounter) 
            closingBracketIndex = __findClosingBracketIndex(function[index:], index)             
            function = function[0:closingBracketIndex] + "}" + function[closingBracketIndex+1:]                                                                                                                                               
            function = function[0:index] + function[index:].replace("(","{",1)                                              
            ifParts = function[index:closingBracketIndex].split(";")
            
            if "if(" in function[index:closingBracketIndex]:              
                toReturn = ('Error in if construct: Nested if construct not allowed. Use "and/or" instead', "", errorPos[0], errorPos[1])
                return toReturn
            
            if not len(ifParts) == 3:              
                toReturn = ("Error in if construct: Two values in if function necessary", "", errorPos[0], errorPos[1])
                return toReturn                           
                                     
            for part in ifParts:
                if len(part) == 0:              
                    toReturn = ("Error in if construct: Two values in if function necessary", "", errorPos[0], errorPos[1])
                    return toReturn   
                         
            compOpSearch = re.compile(r'<|>|==|!=')
            res = compOpSearch.search(ifParts[0])
            if res == None:              
                toReturn = ("Error in if construct: Missing comparison operator", "", errorPos[0], errorPos[1])
                return toReturn  
    
            # check percentOfValues operator
            findPercentOfValuesRegex = re.compile(r'percentOfValues\(?[0-9]*\)?')
            percentParts = findPercentOfValuesRegex.findall(ifParts[0])
            for percentPart in percentParts:
                if not "(" in percentPart or not ")" in percentPart:               
                    toReturn = ("Error in if construct: Percentage value missing", "", errorPos[0], errorPos[1])
                    return toReturn  
                
                percent = percentPart.split("(")[1].split(")")[0]
                if not percent.isnumeric() or int(percent) < 0 or int(percent) > 100:              
                    toReturn = ("Error in if construct: No valid integer number as percentage", "", errorPos[0], errorPos[1])
                    return toReturn                                         
            ifParts[0] = ifParts[0].replace("random","rnd")
            andOrSeperatedParts = re.split("or|and", ifParts[0])
            for andOrPart in andOrSeperatedParts:           
                comparedOperands = re.split(r'<|>|==|!=', andOrPart)              
                if len(comparedOperands) != 2:             
                    toReturn = ("Error in if construct: Missing comparison value", "", errorPos[0], errorPos[1])
                    return toReturn 

                if "if{" in comparedOperands[0]:
                    firstOperand = comparedOperands[0].split("if{")[1]
                else:
                    firstOperand = comparedOperands[0]    
                secondOperand = comparedOperands[1]
                secondOperand = secondOperand.replace("=","")
                possOperandsRegex = re.compile(r'field|polygon|math|raster|rnd|random|True|False|euclidean|manhattan|geodesic|ellipsoidal')
                res = possOperandsRegex.search(firstOperand)
                if res == None and not firstOperand.isnumeric():                                      
                    toReturn = ("Error in if construct: Invalid first operand of comparison", "", errorPos[0], errorPos[1])
                    return toReturn  
              
                res = possOperandsRegex.search(secondOperand)                              
                if res == None and not secondOperand.isnumeric() and not("." in secondOperand and secondOperand.split(".")[0].isnumeric() and secondOperand.split(".")[1].isnumeric):        
                    toReturn = ("Error in if construct: Invalid second operand of comparison", "", errorPos[0], errorPos[1])
                    return toReturn  
                 
                #check polygons set if polygon function used
                if "crossesPolygon" in firstOperand and secondOperand != "True" and secondOperand != "False":            
                    toReturn = ("Error in if construct: crossesPolygon can only be compared to False or True", "", errorPos[0], errorPos[1])
                    return toReturn  
                
                if "insidePolygon" in firstOperand and secondOperand != "True" and secondOperand != "False":               
                    toReturn = ("Error in if construct: insidePolygon can only be compared to False or True", "", errorPos[0], errorPos[1])
                    return toReturn                      
                     
            seperatedParts = re.split("\+|-|\*|/", ifParts[1])
                     
            for sepPart in seperatedParts:
                sepPart = sepPart.replace(")","")   
                if not any(sepPart in s for s in possibleMetrics) and not "math" in sepPart and not "raster" in sepPart and not "rnd" in sepPart and not "random" in sepPart and not sepPart.isnumeric():             
                    try:
                        float(sepPart)
                    except:                 
                        toReturn = ("Error in if construct: Invalid true value", "", errorPos[0], errorPos[1])
                        return toReturn  
            
            seperatedParts = re.split("\+|-|\*|/", ifParts[2])
            
            for sepPart in seperatedParts:
                sepPart = sepPart.replace(")","") 
                if not any(sepPart in s for s in possibleMetrics) and not "math" in sepPart and not "raster" in sepPart and not "rnd" in sepPart and not "random" in sepPart and not sepPart.isnumeric():             
                    try:
                        float(sepPart)
                    except: 
                        toReturn = ("Error in if construct: Invalid false value", "", errorPos[0], errorPos[1])
                        return toReturn       
            
            if "pixelvalue" in ifParts[1].lower() or "percentofvalues" in ifParts[1].lower():
                toReturn = ("Error in if construct: Invalid true value", "", errorPos[0], errorPos[1])
                return toReturn  
            if "pixelvalue" in ifParts[2].lower() or "percentofvalues" in ifParts[2].lower():
                toReturn = ("Error in if construct: Invalid false value", "", errorPos[0], errorPos[1])
                return toReturn                       
            partCounter+=1
           
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
            searchMath = re.finditer('math\.[a-z]+\(.+?\)', function[index:closingBracketIndex])
            for matchObj in searchMath:         
                function = function[:matchObj.start()+index] + function[matchObj.start()+index:matchObj.end()+index].replace("§",",") + function[matchObj.end()+index:]                        
            if not "§" in function[index:closingBracketIndex] or len(function[index:closingBracketIndex].split("§")) != 2:
                errorPos = __findConstructPosition(originalFunction, "random", partCounter)               
                toReturn = ("Error in random function: Two valid values necessary", "", errorPos[0], errorPos[1])
                return toReturn
            randomRangeValues = function[index+4:closingBracketIndex-3].split("§")
            for value in randomRangeValues:   
                value = value.replace("(","") .replace(")","")   
                sepParts = re.split("\+|-|\*|;|/", value)
                for v in sepParts: 
                    v = v.replace("}","")                                   
                    if not v.isnumeric() and not v in possibleMetrics and not "raster[" in v and not "math." in v and not "if" in v:
                        try:
                            float(v)
                        except:
                            if "," in v:
                                splitRes = v.split(",")                      
                                for res in splitRes:
                                    if not res.isnumeric() and not res in possibleMetrics and not "raster[" in res and not "math." in res and not "if" in res:
                                        try:
                                            float(res)
                                        except:
                                           errorPos = __findConstructPosition(originalFunction, "random", partCounter)               
                                           toReturn = ("Error in random function: Invalid upper or lower bound", "", errorPos[0], errorPos[1])
                                           return toReturn                      
                            else:
                                errorPos = __findConstructPosition(originalFunction, "random", partCounter)               
                                toReturn = ("Error in random function: Invalid upper or lower bound", "", errorPos[0], errorPos[1])
                                return toReturn                                               
            partCounter+=1
    
    # check all polygon constructs
    partCounter = 1
    regex = re.compile(r'polygon\[?[0-9]?\]?:?[A-z]*')
    res = regex.findall(function)
    for matchString in res:
        errorPos = __findConstructPosition(originalFunction, "polygon", partCounter) 
        if not "[" in matchString or not "]" in matchString or not ":" in matchString:                         
            toReturn = ("Error in polygon construct: No index given", "", errorPos[0], errorPos[1])
            return toReturn   

        number = matchString.split("[")[1].split("]")[0]
        if not number.isnumeric:              
            toReturn = ("Error in polygon construct: No index given", "", errorPos[0], errorPos[1])
            return toReturn   
        if number == "":              
            toReturn = ("Error in polygon construct: No valid index given", "", errorPos[0], errorPos[1])
            return toReturn   
        if int(number) >= numberOfPolygons or int(number) < 0:             
            toReturn = ("Error in polygon construct: No valid index given", "", errorPos[0], errorPos[1])
            return toReturn   
        if not ":crossesPolygon" in matchString and not ":insidePolygon" in matchString:              
            toReturn = ("Error in polygon construct: Define valid analysis for polygons", "", errorPos[0], errorPos[1])
            return toReturn   
        partCounter+=1
    
    # check math constructs    
    partCounter = 1                      
    regex = re.compile(r'math\.[A-z]+\(?')
    res = regex.findall(function)
    for matchString in res: 
        if not "(" in matchString:
            errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
            toReturn = ("Error in math construct: No opening bracket", "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1
    
    partCounter = 1 
    regex = re.compile(r'math\.?')
    res = regex.findall(function)
    for matchString in res:                          
        if not "." in matchString:
            errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
            toReturn = ("Error in math construct: No function specified", "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1 
    
    partCounter = 1 
    regex = re.compile(r'math\.[A-z]*')
    res = regex.findall(function)
    for matchString in res:                          
        pointSplit = matchString.split(".")[1]
        if pointSplit == "":
            errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
            toReturn = ("Error in math construct: No function specified", "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1 
       
    partCounter = 1        
    regex = re.compile(r'math\.[A-z]*\(?')   
    res = regex.finditer(function)
    for matchObj in res:
        matchString = matchObj.group().replace("(","")
        closingAt = __findClosingBracketIndex(function[matchObj.start():], matchObj.start())
        matchString2 = function[matchObj.start():closingAt+1]                 
        if "," in matchString2:                                                  
            mathEvalTest2 = matchString + "(10,10)"  
            try:                                          
                eval(mathEvalTest2)  
                                  
            except:
                errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                toReturn = ("Error in math construct: Unable to execute", "", errorPos[0], errorPos[1])
                return toReturn     
        else:
            mathEvalTest1 = matchString + "(10)"                
            try:
                if "math.acos" in mathEvalTest1:
                    mathEvalTest1 = mathEvalTest1.replace("10","1")                              
            except:
                errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                toReturn = ("Error in math construct: Unable to execute", "", errorPos[0], errorPos[1])
                return toReturn 
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
                errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                toReturn = ("Error in math construct: Nested construct", "", errorPos[0], errorPos[1])
                return toReturn 
            
            number = function[index:].split("$")[0].split("%")[1]
            number = number.replace("(","").replace(")","").replace("==","=").replace("!","").replace("(","").replace(")","").replace("}","").replace("{","").replace("&","").replace("$","")
            if ("<" in number or ">" in number or "=" in number) and not "if" in number:
                errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                toReturn = ("Error in math construct: Nested construct", "", errorPos[0], errorPos[1])
                return toReturn 
            # only one operand
            if not "," in number:
                multiNumbers = re.split("\+|-|\*|/|>|<|;|=", number)
                for n in multiNumbers:                  
                    if not n in possibleMetrics and not n.isnumeric() and not "field:" in n and not "raster" in n and not "rnd" in n and not "if" in n and not "and" in n and not n == "True" and not n == "False":
                        try:
                            float(n)
                        except:
                            errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                            toReturn = ("Error in math construct: At least one valid operand necessary", "", errorPos[0], errorPos[1])
                            return toReturn 
             
            # two operands
            if "," in number:
                multNumbers = number.split(",")
                if len(multNumbers) > 2:
                    errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                    toReturn = ("Error in math construct: Only operations with two variables supported", "", errorPos[0], errorPos[1])
                    return toReturn 
                for n1 in multNumbers:
                    n2 = re.split("\+|-|\*|/", n1)
                    for n in n2:                                
                        if not n.isnumeric() and not "field:" in n and not "raster" in n and not "random" in n and not "rnd" in n and not "if" in n:
                            if not n in possibleMetrics:
                                try:
                                    float(n)
                                except:   
                                    errorPos = __findConstructPosition(originalFunction, "math", partCounter)               
                                    toReturn = ("Error in math construct: Invalid value", "", errorPos[0], errorPos[1])
                                    return toReturn                   
            partCounter+=1
                   
    # raster check    
    partCounter = 1       
    regex = re.compile(r'raster\[?[0-9]*\]?:?[A-z]*')
    res = regex.findall(function)
    for matchString in res:                      
        if not "[" in matchString:
            errorPos = __findConstructPosition(originalFunction, "raster", partCounter)               
            toReturn = ("Error in raster analysis: Index necessary to reference raster data", "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1
     
    partCounter = 1           
    regex = re.compile(r'raster\[[0-9]*\]:?')
    res = regex.findall(function)
    for matchString in res:        
        rasterIndexNumber = matchString.split("[")[1].split("]")[0]
        if not rasterIndexNumber.isnumeric():
            errorPos = __findConstructPosition(originalFunction, "raster", partCounter)               
            toReturn = ("Error in raster analysis: Index necessary to reference raster data", "", errorPos[0], errorPos[1])
            return toReturn
        if not ":" in matchString:
            errorPos = __findConstructPosition(originalFunction, "raster", partCounter)               
            toReturn = ("Error in raster analysis: No analysis type defined", "", errorPos[0], errorPos[1])
            return toReturn
        
        if int(rasterIndexNumber) > numberOfRasterData-1 or int(rasterIndexNumber) < 0:
            errorPos = __findConstructPosition(originalFunction, "raster", partCounter)               
            toReturn = ("Error in raster analysis: Invalid index", "", errorPos[0], errorPos[1])
            return toReturn            
        partCounter+=1
    
    partCounter = 1
    regex = re.compile(r'raster\[[0-9]+\]:[A-z]*\(?')
    res = regex.findall(function)
    for matchString in res:     
        analysisType = re.split("<|>|,|\)|=|and|or", matchString.split("]:")[1])[0]
        if not "sp" in analysisType and "(" in analysisType and not "percentOfValues" in analysisType:
            errorPos = __findConstructPosition(originalFunction, "raster", partCounter)               
            toReturn = ("Error in raster analysis: No heuristic index necessary", "", errorPos[0], errorPos[1])
            return toReturn
        analysisType = analysisType.replace("(","")
        if not analysisType in possibleRasterAnalysis and not "percentOfValues" in analysisType and not "pixelValue" in analysisType and not "spPercentOfValues" in analysisType and not "spPixelValue" in analysisType:
            errorPos = __findConstructPosition(originalFunction, "raster", partCounter)               
            toReturn = ("Error in raster analysis: Invalid raster analysis", "", errorPos[0], errorPos[1])
            return toReturn
        
        
        partCounter+=1
         
    # check shortestPath operators
    partCounter = 1
    findspRegex = re.compile(r'raster\[[0-9+]\]:sp[A-z]+\(?[0-9]*,?[0-9]*\)?')
    spParts = findspRegex.findall(function)
    for spPart in spParts:
        if not "(" in spPart or not ")" in spPart:
            errorPos = __findConstructPosition(originalFunction, "raster\[[0-9]+\]:sp", partCounter)               
            toReturn = ("Error in raster analysis: Heuristic index for shortest path missing", "", errorPos[0], errorPos[1])
            return toReturn  
        heuristicIndex = spPart.split("(")[1].split(")")[0]
        if "," in heuristicIndex:
            if "pixelValue" in spPart or "PixelValue" in spPart:
                 errorPos = __findConstructPosition(originalFunction, "raster\[[0-9]+\]:sp", partCounter)               
                 toReturn = ("Error in raster analysis: Only heuristic index necessary", "", errorPos[0], errorPos[1])
                 return toReturn  
            
            heuristicIndex = heuristicIndex.split(",")[0]
            percentage = spPart.split(",")[1].split(")")[0]
            if not percentage.isnumeric() or int(percentage) < 0 or int(percentage) > 100:
                errorPos = __findConstructPosition(originalFunction, "raster\[[0-9]+\]:sp", partCounter)               
                toReturn = ("Error in raster analysis: No valid integer number as percentage", "", errorPos[0], errorPos[1])
                return toReturn 
        if not heuristicIndex.isnumeric() or int(heuristicIndex) < 0 or int(heuristicIndex) > 5:
            errorPos = __findConstructPosition(originalFunction, "raster\[[0-9]+\]:sp", partCounter)               
            toReturn = ("Error in raster analysis: No valid integer number as heuristic index", "", errorPos[0], errorPos[1])
            return toReturn        
        partCounter+=1
    
    percentPixelRegexList = ['raster\[[0-9]+\]:pixelValue', 'raster\[[0-9]+\]:spPixelValue', 'raster\[[0-9]+\]:percentOfValues', 'raster\[[0-9]+\]:spPercentOfValues']        
    for regex in percentPixelRegexList:
        partCounter = 1
        regexCompiled = re.compile(regex)
        findPercentOrPixel = regexCompiled.finditer(function)
        for matchObj in findPercentOrPixel:
            if matchObj.start() == 0:
                errorPos = __findConstructPosition(originalFunction, regex, partCounter)               
                toReturn = ("Error in raster analysis: PixelValue analysis can only be used inside if construct", "", errorPos[0], errorPos[1])
                return toReturn 
            findIf = function[matchObj.start()-3:matchObj.start()]
            if not "if" in findIf:
                if not "and" in findIf and not "or" in findIf:
                    errorPos = __findConstructPosition(originalFunction, regex, partCounter)               
                    toReturn = ("Error in raster analysis: PixelValue analysis can only be used inside if construct", "", errorPos[0], errorPos[1])
                    return toReturn                    
            partCounter+=1
    
    # fields check
    partCounter = 1
    foundFieldConstruct = False 
    regex = re.compile(r'field:?')  
    res = regex.findall(function)
    for matchString in res:        
        foundFieldConstruct = True      
        if not ":" in matchString:
            errorPos = __findConstructPosition(originalFunction, "field", partCounter)               
            toReturn = ('Error in field query: No ":" after field', "", errorPos[0], errorPos[1])
            return toReturn
        partCounter+=1
    
    partCounter = 1
    fieldSet = False  
    regex = re.compile(r'field:[A-z]+')   
    res = regex.findall(function)  
    for matchString in res: 
        fieldSet = True
        fieldName = matchString.split("field:")[1]
        if not fieldName in possibleFields:
            errorPos = __findConstructPosition(originalFunction, "field", partCounter)               
            toReturn = ("Error in field query: Invalid field name", "", errorPos[0], errorPos[1])
            return toReturn  
        partCounter+=1
    
    if foundFieldConstruct == True and fieldSet == False:
        return ("No field name defined","", 0, len(originalFunction))
    
    # if no error was returned the function is valid                    
    return ("No error found", function, 0, 0) 


