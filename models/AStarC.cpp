/**
 *  This file is part of the S.P.A.N.N.E.R.S. plugin.
 *
 *  Copyright (C) 2022  Tim Hartmann
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public
 *  License along with this program; if not, see
 *  https://www.gnu.org/licenses/gpl-2.0.html.
 */

#include <pybind11/pybind11.h>
#include <queue>
#include <tuple>
#include <vector>
#include <utility>
#include <stdlib.h>
#include <time.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <limits.h>

namespace py = pybind11;

struct Point{
	int x;
	int y;
	int weight;
	
	Point(int xPos, int yPos, int weight) : x(xPos), y(yPos), weight(weight){
	}
	
	bool operator<(const struct Point& other) const {
		return weight > other.weight;
	}
	bool operator==(const Point& other) {
		if(x == other.x && y == other.y){
			return true;
		}
		else{
			return false;
		}
	}
	bool operator!=(const Point& other) {
		if(x == other.x && y == other.y){
			return false;
		}
		else{
			return true;
		}
	}
};

class AStar {
	public:
		AStar(const std::vector<std::vector<int>> matrix, int heuristicIndex, int minValue, int meanValue, bool createShortestPathMatrix) : matrix(matrix), heuristicIndex(heuristicIndex), minValue(minValue), meanValue(meanValue),createShortestPathMatrix(createShortestPathMatrix) {
			if(createShortestPathMatrix){
				shortestPathMatrix1.resize(matrix.size());
				shortestPathMatrix2.resize(matrix.size());
				shortestPathMatrix3.resize(matrix.size());
				for(int i=0; i<int(matrix.size()); i++){
					shortestPathMatrix1[i].resize(matrix[0].size());
					shortestPathMatrix2[i].resize(matrix[0].size());
					shortestPathMatrix3[i].resize(matrix[0].size());
				}
			}				
			srand(time(NULL));		
		}
		
		std::vector<int> shortestPath(int x1, int y1, int x2, int y2){	
			diagonals = 0;	
			std::vector<std::vector<int>> pixelWeights(matrix.size(), std::vector<int>(matrix[0].size()));	
			std::vector<std::vector<std::tuple<int,int>>> predMatrix (matrix.size(), std::vector<std::tuple<int,int>>(matrix[0].size()));
			
			int randomRed = rand() % 255 + 1;
			int randomGreen = rand() % 255 + 1;
			int randomBlue = rand() % 255 + 1;
			
			for(int i=0; i<int(matrix.size());i++){
				for(int j=0; j<int(matrix[0].size());j++){
					pixelWeights[i][j] = INT_MAX;
				}			
			}

			pixelWeights[x1][y1] = 0;
			
			Point startPoint = Point(x1,y1,pixelWeights[x1][y1]);
			Point endPoint = Point(x2,y2,pixelWeights[x2][y2]);
			std::priority_queue<Point> pq;
			pq.push(startPoint);
			
			while(!pq.empty()){
				Point current = pq.top();
				pq.pop();
				
				if(current == endPoint){
					std::vector<int> shortestPathWeights;
					std::tuple<int,int> u = std::make_tuple(endPoint.x,endPoint.y);
					Point currPathPoint = Point(std::get<0>(u),std::get<1>(u),0);
					while(currPathPoint != startPoint){
						if(createShortestPathMatrix){
							shortestPathMatrix1[currPathPoint.x][currPathPoint.y] = (shortestPathMatrix1[currPathPoint.x][currPathPoint.y] + randomRed) / 2;
							shortestPathMatrix2[currPathPoint.x][currPathPoint.y] = (shortestPathMatrix2[currPathPoint.x][currPathPoint.y] + randomGreen) / 2;
							shortestPathMatrix3[currPathPoint.x][currPathPoint.y] = (shortestPathMatrix3[currPathPoint.x][currPathPoint.y] + randomBlue) / 2;
						}
						shortestPathWeights.push_back(matrix[std::get<0>(u)][std::get<1>(u)]);
						int prevX = std::get<0>(u);
						int prevY = std::get<1>(u);
						u = predMatrix[std::get<0>(u)][std::get<1>(u)];
						if(std::get<0>(u) != prevX && std::get<1>(u) != prevY){
							diagonals++;
						}
						
						currPathPoint = Point(std::get<0>(u),std::get<1>(u),0);
					}
					shortestPathWeights.push_back(matrix[startPoint.x][startPoint.y]);	
					if(createShortestPathMatrix){
						shortestPathMatrix1[startPoint.x][startPoint.y] = (shortestPathMatrix1[currPathPoint.x][currPathPoint.y] + randomRed) / 2;
						shortestPathMatrix2[startPoint.x][startPoint.y] = (shortestPathMatrix2[currPathPoint.x][currPathPoint.y] + randomGreen) / 2;
						shortestPathMatrix3[startPoint.x][startPoint.y] = (shortestPathMatrix3[currPathPoint.x][currPathPoint.y] + randomBlue) / 2;
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
					
					if(neighborX > 0 && neighborY > 0 && neighborX < int(matrix.size()) && neighborY < int(matrix[0].size())){
						if(newDistance < pixelWeights[neighborX][neighborY]){
							predMatrix[neighborX][neighborY] = std::make_tuple(current.x, current.y);
							pixelWeights[neighborX][neighborY] = newDistance;
							
							if(createShortestPathMatrix){
								if(shortestPathMatrix1[current.x][current.y] == 0 && shortestPathMatrix2[current.x][current.y] == 0 && shortestPathMatrix3[current.x][current.y] == 0){
									shortestPathMatrix1[current.x][current.y] = 255;
									shortestPathMatrix2[current.x][current.y] = 255;
									shortestPathMatrix3[current.x][current.y] = 255;
								}																	
							}
							int heuristicWeight = pixelWeights[neighborX][neighborY] + heuristic(neighborX, neighborY, endPoint.x, endPoint.y);						
							pq.push(Point(neighborX, neighborY, heuristicWeight));
						}				
					}
				}				
			}		
			return {INT_MAX};
		} 
		
		std::vector<std::vector<short>> &getShortestPathMatrix1(){
			return shortestPathMatrix1;
		}
		std::vector<std::vector<short>> &getShortestPathMatrix2(){
			return shortestPathMatrix2;
		}
		std::vector<std::vector<short>> &getShortestPathMatrix3(){
			return shortestPathMatrix3;	
		}
		int &getNumberOfDiagonals(){
			return diagonals;
		}
				
	private:
		std::vector<std::vector<int>> matrix;
		int heuristicIndex;
		int minValue;
		int meanValue;
		bool createShortestPathMatrix;
		std::vector<std::vector<short>> shortestPathMatrix1;
		std::vector<std::vector<short>> shortestPathMatrix2;
		std::vector<std::vector<short>> shortestPathMatrix3;
		int diagonals = 0;
		
		std::vector<std::tuple<int,int>> getNeighborIndices(int i, int j){
			// non diagonal
			std::tuple<int,int> bm = std::make_tuple(i-1,j);		
			std::tuple<int,int> ml = std::make_tuple(i,j-1);
			std::tuple<int,int> mr = std::make_tuple(i,j+1);		
			std::tuple<int,int> tm = std::make_tuple(i+1,j);
			
			//diagonal
			std::tuple<int,int> bl = std::make_tuple(i-1,j-1);
			std::tuple<int,int> br = std::make_tuple(i-1,j+1);
			std::tuple<int,int> tl = std::make_tuple(i+1,j-1);
			std::tuple<int,int> tr = std::make_tuple(i+1,j+1);	
			
			std::vector<std::tuple<int,int>> toReturn = {bm,ml,mr,tm,bl,br,tl,tr};

			return toReturn;
			
		}
		
		int heuristic(int point1X, int point1Y, int point2X, int point2Y){
			int factor = 0;
			if(heuristicIndex == 0){
				factor = minValue;			
			}			
			else{
				if(heuristicIndex == 1){
					factor = int(meanValue/4);
				}
				else if(heuristicIndex == 2){
					factor = int(meanValue/2);
				}
				else if(heuristicIndex == 3){
					factor = int(meanValue/1.5);
				}
				else if(heuristicIndex == 4){
					factor = int(meanValue/1.25);
				}
				else if(heuristicIndex == 5){
					factor = int(meanValue);
				}
			}									
			int heurValue = std::max(std::abs(point2X-point1X), std::abs(point2Y-point1Y)) * factor;
			return heurValue;		
		}
};

PYBIND11_MODULE(AStarC,m) {
	py::class_<AStar>(m, "AStar")
	.def(py::init<const std::vector<std::vector<int>>, int, int, int, bool>())
	.def("shortestPath", &AStar::shortestPath)
	.def("getShortestPathMatrix1", &AStar::getShortestPathMatrix1)
	.def("getShortestPathMatrix2", &AStar::getShortestPathMatrix2)
	.def("getShortestPathMatrix3", &AStar::getShortestPathMatrix3)
	.def("getNumberOfDiagonals", &AStar::getNumberOfDiagonals);
}
