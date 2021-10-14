import matplotlib.pyplot as plt

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
       
            plt.plot(self.xParameters[i], self.values[i], marker = "o", label=zLabel, linestyle = '-')
        
        
        plt.ylabel(self.yLabel)
        plt.xlabel(self.xLabel)
        plt.legend()
        plt.show()
        
                
    def plotLines(self):
        print("TODO")
    
    def plotBarChart(self):     
        print("TODO")