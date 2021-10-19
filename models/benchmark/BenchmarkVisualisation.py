import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime


class BenchmarkVisualisation():
    
    
    def __init__(self, yLabel, createLegend, logSelected, tightLayout):
        
        # xLabels and values are 2D
        # zLabels is 1D 
        self.xParameters = []
        self.yLabel = yLabel
        self.zLabels = []
        self.values = []
        self.xParametersMultiExe = []
        self.zLabelsMultiExe = []
        self.valuesMultiExe = []
        self.createLegend = createLegend
        self.logSelected = logSelected
        self.tightLayout = tightLayout
        
        
    def setOneMultiExePlotData(self, xLabel, xParameters, zLabel, values):
        self.xParametersMultiExe.append(xParameters)
        self.zLabelsMultiExe.append(zLabel)
        self.valuesMultiExe.append(values)
        self.xLabel = xLabel
           
    def setOnePlotData(self, xLabel, xParameters, zLabel, values):
        self.xParameters.append(xParameters)
        self.zLabels.append(zLabel)
        self.values.append(values)
        self.xLabel = xLabel
        
    def createTextFile(self, path):
        dateString = date.today().strftime("%b_%d_%Y_")
        timeString = datetime.now().strftime("%H_%M_%S")
        if path == "":
            f = open(path + "BenchmarkResult_" + dateString + timeString + ".txt","w")
        else:          
            f = open(path + "/" + "BenchmarkResult_" + dateString + timeString + ".txt","w")
        
        longestParasIndex = 0
        longestParasLength = len(self.xParameters[0])
        for counter, xParaList in enumerate(self.xParameters):
            if longestParasLength < len(xParaList):
                longestParasIndex = counter
                longestParasLength = len(xParaList)
         
        f.write(str(self.xLabel)) 
                 
        for parameter in self.xParameters[longestParasIndex]:
            f.write("\t" + parameter)
   
        f.write("\n")
        
        for i in range(len(self.zLabels)):
            f.write(self.zLabels[i] + "\t")
            for value in self.values[i]:
                f.write(str(value) + "\t")
            f.write("\n")     
        

        f.close()
    
    def plotPoints(self, withLines, callNumber):       
        plt.figure(callNumber)
        
        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]
            
            if withLines == True:
                plt.plot(self.xParameters[i], self.values[i], marker = "o", label=zLabel, linestyle = '-')
            else:
                plt.scatter(self.xParameters[i], self.values[i], label=zLabel)
        
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        if self.createLegend:
            plt.legend(loc = "best")
            
        if self.logSelected:    
            plt.yscale("log")      
        
        if self.tightLayout:    
            plt.tight_layout()
        plt.show()
        
                
    def plotLines(self, callNumber):      
        plt.figure(callNumber)
        
        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]
            
            plt.plot(self.xParameters[i], self.values[i], label=zLabel, linestyle = '-')
        
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        if self.createLegend:
            plt.legend(loc = "best")
        
        if self.logSelected:    
            plt.yscale("log")      
            
        if self.tightLayout:    
            plt.tight_layout()
            
        plt.show()
    
    def plotBarChart(self, callNumber):             
        plt.figure(callNumber)
        
        width = 0.35
        
        # get longest xParameters
        longestParaIndex = 0
        longestPara = len(self.xParameters[0])
        for i in range (len(self.xParameters)):
            if len(self.xParameters[i]) > longestPara:
                longestParaIndex = i
                longestPara = len(self.xParameters[i])
                
            
        x = np.arange(longestPara)
        
        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]
            
            plt.bar(x, self.values[i], label=zLabel, width=width)
            
            x = [br + width for br in x]
        
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        plt.xticks([r + ((width/2)*(len(self.zLabels)-1)) for r in range(len(self.xParameters[longestParaIndex]))], self.xParameters[longestParaIndex])
        if self.createLegend:
            plt.legend(loc = "best")
        
        if self.logSelected:    
            plt.yscale("log")    
            
        if self.tightLayout:    
            plt.tight_layout()
        
        plt.show()
        
       
    def plotBoxPlot(self, callNumber):
        
        #plt.figure(callNumber)
        fig, ax = plt.subplots()
        subplots = []
        boxes = []
        colors = ["blue", "green", "purple", "tan", "pink", "red"]
        for i in range(len(self.zLabelsMultiExe)):
            zLabel = self.zLabelsMultiExe[i]
            bp = ax.boxplot(self.valuesMultiExe[i], labels=self.xParametersMultiExe[i], patch_artist = True)
            subplots.append(bp)
            patch = bp["boxes"][0]
            patch.set_facecolor(colors[i])
            boxes.append(patch)
              
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        if self.createLegend:
            plt.legend(boxes, self.zLabelsMultiExe,loc = "best")
        if self.logSelected:    
            ax.set_yscale("log")                
        
        if self.tightLayout:    
            plt.tight_layout()

        plt.show()
        
        
        