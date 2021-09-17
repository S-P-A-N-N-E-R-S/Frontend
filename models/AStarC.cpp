#include <pybind11/pybind11.h>
#include <queue>
#include <tuple>
#include <vector>
#include <utility>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <limits.h>

namespace py = pybind11;

struct Point{
	int x;
	int y;
	int weight;
	
	Point(int xPos, int yPos, double weight) : x(xPos), y(yPos), weight(weight){
	}
	
	bool operator<(const struct Point& other) const {
		return weight > other.weight;
	}
	bool operator==(const Point& other) {
		if(x == other.x and y == other.y){
			return true;
		}
		else{
			return false;
		}
	}
	bool operator!=(const Point& other) {
		if(x == other.x and y == other.y){
			return false;
		}
		else{
			return true;
		}
	}
};

class AStarC {
	public:
		AStarC(const std::vector<std::vector<int>> matrix, int heuristicIndex, double minValue, double meanValue, bool createShortestPathMatrix) : matrix(matrix), heuristicIndex(heuristicIndex), minValue(minValue), meanValue(meanValue),createShortestPathMatrix(createShortestPathMatrix) {
			if(createShortestPathMatrix){
				shortestPathMatrix.resize(matrix.size());
				for(int i=0; i<matrix.size(); i++){
					shortestPathMatrix[i].resize(matrix[0].size());
				}
			}			
		}
		
		std::vector<int> shortestPath(int x1, int y1, int x2, int y2){		
			std::vector<std::vector<int>> pixelWeights(matrix.size(), std::vector<int>(matrix[0].size()));	
			std::vector<std::vector<std::tuple<int,int>>> predMatrix (matrix.size(), std::vector<std::tuple<int,int>>(matrix[0].size()));
			
			for(int i=0; i<matrix.size();i++){
				for(int j=0; j<matrix[0].size();j++){
					pixelWeights[i][j] = INT_MAX;
				}			
			}

			pixelWeights[x1][y1] = 0;
			
			Point startPoint = Point(x1,y1,pixelWeights[x1][y1]);
			Point endPoint = Point(x2,y2,pixelWeights[x2][y2]);
			std::priority_queue<Point> pq;
			pq.push(startPoint);
			
			while(not pq.empty()){				
				Point current = pq.top();
				pq.pop();
				
				if(current == endPoint){
					std::vector<int> shortestPathWeights;
					std::tuple<int,int> u = std::make_tuple(endPoint.x,endPoint.y);
					Point currPathPoint = Point(std::get<0>(u),std::get<1>(u),0);
					while(currPathPoint != startPoint){
						if(createShortestPathMatrix){
							shortestPathMatrix[currPathPoint.x][currPathPoint.y] = 100;
						}
						shortestPathWeights.push_back(matrix[std::get<0>(u)][std::get<1>(u)]);
						u = predMatrix[std::get<0>(u)][std::get<1>(u)];
						currPathPoint = Point(std::get<0>(u),std::get<1>(u),0);
					}
					shortestPathWeights.push_back(matrix[startPoint.x][startPoint.y]);	
					if(createShortestPathMatrix){
						shortestPathMatrix[startPoint.x][startPoint.y] = 100;
					}	
								
					return shortestPathWeights;
				}
				
				if(current.weight - heuristic(current.x, current.y, endPoint.x, endPoint.y) > pixelWeights[current.x][current.y]){
					continue;				
				}
				
				std::vector<std::tuple<int,int>> neighbors = getNeighborIndices(current.x, current.y);
				
				for(std::tuple<int,int> neighbor : neighbors){
					int neighborX = std::get<0>(neighbor);
					int neighborY = std::get<1>(neighbor);
				
					int newDistance = pixelWeights[current.x][current.y] + matrix[current.x][current.y];
					
					if(neighborX > 0 and neighborY > 0 and neighborX < matrix.size() and neighborY < matrix[0].size()){
						if(newDistance < pixelWeights[neighborX][neighborY]){
							predMatrix[neighborX][neighborY] = std::make_tuple(current.x, current.y);
							pixelWeights[neighborX][neighborY] = newDistance;
							
							if(createShortestPathMatrix){
								if(not (shortestPathMatrix[current.x][current.y] == 100)){
									shortestPathMatrix[current.x][current.y] = 50;
								}							
							}							
							double heuristicWeight = pixelWeights[neighborX][neighborY] + heuristic(neighborX, neighborY, endPoint.x, endPoint.y);						
							pq.push(Point(neighborX, neighborY, heuristicWeight));
						}				
					}
					
				}
				
			}		
			return {INT_MAX};
		} 
		
		
		std::vector<std::vector<int>> getShortestPathMatrix(){
			return shortestPathMatrix;
		}
		
		
	private:
		std::vector<std::vector<int>> matrix;
		int heuristicIndex;
		double minValue;
		double meanValue;
		bool createShortestPathMatrix;
		std::vector<std::vector<int>> shortestPathMatrix;
		
		std::vector<std::tuple<int,int>> getNeighborIndices(int i, int j){
			std::tuple<int,int> bl = std::make_tuple(i-1,j-1);
			std::tuple<int,int> bm = std::make_tuple(i-1,j);
			std::tuple<int,int> br = std::make_tuple(i-1,j+1);
			std::tuple<int,int> ml = std::make_tuple(i,j-1);
			std::tuple<int,int> mr = std::make_tuple(i,j+1);
			std::tuple<int,int> tl = std::make_tuple(i+1,j-1);
			std::tuple<int,int> tm = std::make_tuple(i+1,j);
			std::tuple<int,int> tr = std::make_tuple(i+1,j+1);	
			
			std::vector<std::tuple<int,int>> toReturn = {bl,bm,br,ml,mr,tl,tm,tr};
			
			return toReturn;
			
		}
		
		double heuristic(int point1X, int point1Y, int point2X, int point2Y){
			double factor = 0.0;
			if(heuristicIndex == 0){
				factor = minValue;			
			}			
			else{
				if(heuristicIndex == 1){
					factor = meanValue/4;
				}
				else if(heuristicIndex == 2){
					factor = meanValue/2;
				}
				else if(heuristicIndex == 3){
					factor = meanValue/1.5;
				}
				else if(heuristicIndex == 4){
					factor = meanValue/1.25;
				}
				else if(heuristicIndex == 5){
					factor = meanValue;
				}
			}									
			double heurValue = std::max(std::abs(point2X-point1X), std::abs(point2Y-point1Y)) * factor;
			return heurValue;		
		}
};

PYBIND11_MODULE(AStarC,m) {
	py::class_<AStarC>(m, "AStarC")
	.def(py::init<const std::vector<std::vector<int>>, int, double, double, bool>())
	.def("shortestPath", &AStarC::shortestPath)
	.def("getShortestPathMatrix", &AStarC::getShortestPathMatrix);
}
