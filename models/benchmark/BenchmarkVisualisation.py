import matplotlib.pyplot as plt
import numpy as np

class BenchmarkVisualisation():
    
    
    def __init__(self, yLabel):
        
        # xLabels and values are 2D
        # zLabels is 1D 
        self.xParameters = []
        self.yLabel = yLabel
        self.zLabels = []
        self.values = []
        
    
    def setOnePlotData(self, xLabel, xParameters, zLabel, values):
        self.xParameters.append(xParameters)
        self.zLabels.append(zLabel)
        self.values.append(values)
        self.xLabel = xLabel
    
    def plotPoints(self, withLines, callNumber):
        print(self.yLabel)
        print(self.xParameters)
        print(self.zLabels)
        print(self.values)
        
        plt.figure(callNumber)
        
        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]
            
            if withLines == True:
                plt.plot(self.xParameters[i], self.values[i], marker = "o", label=zLabel, linestyle = '-')
            else:
                print("TEST")
                plt.scatter(self.xParameters[i], self.values[i], label=zLabel)
        
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        plt.legend(loc = "best")
        #plt.tight_layout()
        plt.show()
        
                
    def plotLines(self, callNumber):
        print(self.yLabel)
        print(self.xParameters)
        print(self.zLabels)
        print(self.values)
        
        plt.figure(callNumber)
        
        for i in range(len(self.zLabels)):
            zLabel = self.zLabels[i]
            
            plt.plot(self.xParameters[i], self.values[i], label=zLabel, linestyle = '-')
        
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        plt.legend(loc = "best")
        #plt.tight_layout()
        plt.show()
    
    def plotBarChart(self, callNumber):     
        print(self.yLabel)
        print(self.xParameters)
        print(self.zLabels)
        print(self.values)
        
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
        plt.legend(loc = "best")
        #plt.tight_layout()
        plt.show()
        

        
    def plotBoxPlot(self, callNumber):
        print("TODO")    
        
        
        
        
        
        
        
        
        