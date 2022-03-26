# S.P.A.N.N.E.R.S. - Frontend

The S.P.A.N.N.E.R.S. plugin provides the creation, visualization and modification of graphs in the 
Open Source Geographic Information System [QGIS](https://qgis.org). 

In addition, this QGIS plugin serves as a frontend for the backend that supports the execution of analyses on the created graphs.
For the execution of these analyses, the backend is required. The backend receives graph information from the frontend over 
the network in order to execute analyses on it using the [Open Graph Drawing Framework](https://ogdf.uos.de/).

Furthermore, customisable experiments can be performed and the results can automatically be visualised in a scientific manner.

## Installation
The recommended way to install the plugin is from the [QGIS Python Plugins Repository](https://plugins.qgis.org/plugins/).
A detailed installation guide for Linux and Windows can be found in the 
[handbook](https://project2.informatik.uni-osnabrueck.de/spanners/) and in the `help` directory.

To install the plugin from source under Linux, follow the instructions below.
The repository can be cloned by `git clone --recursive <repository>`. 
Make sure to clone it recursively so that the submodules are loaded.

Alternatively, the submodules can be loaded with the `git submodule update --init --recursive` command.

### Requirements

- QGIS (3.x)
- protobuf (>=3.17)
- pybind11 (>=2.7.1)

The required python packages can be installed with the `pip install -r requirements.txt` command. The protobuf compiler 
is required as well.

### Deploy Plugin to QGIS3

On Linux, the plugin can be deployed to QGIS by calling the `make deploy` command in the root directory.

The plugin is now located on Linux under: `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`

Finally, the plugin needs to be enabled in QGIS (`Plugins -> Manage and Install Plugins...`)

Subsequently, you can install the backend or connect the frontend to an existing backend server.

### Alternative Installation

An alternative is to clone the repository directly into the folder located under `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`.
After copying, the commands `make proto`, `make transcompile` and `make pybind_build` need to be executed.

### Create .zip File

The `make zip` command creates a .zip file containing the plugin. The file can be used to distribute or install the plugin in QGIS.
The plugin can be installed in QGIS under `Plugins -> Manage and Install Plugins... -> Install from ZIP`.

## Usage
The plugin provides several user interfaces for easily create, visualize, analyse and modify graphs. 
Detailed usage information can be found in the [handbook](https://project2.informatik.uni-osnabrueck.de/spanners/).

## Licence
This plugin is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

## Used Libraries
The library kdtree, licenced under the ISC, is used for shortest path analyses.
