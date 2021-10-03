# Frontend

This QGIS plugin provides the creation and visualization of graphs in the 
Open Source Geographic Information System [QGIS](https://qgis.org). 

In addition, the Frontend supports the execution of analyses on the created graphs.
For the execution of the analyses, the backend is required, which receives graph information from the Frontend over 
the network in order to execute analyses on it using the [Open Graph Drawing Framework](https://ogdf.uos.de/).

## Installation

The repository can be cloned by `git clone --recursive <repository>`. Make sure to clone it recursively so that 
the submodules are loaded.

Alternatively, the submodules can be loaded with the `git submodule update --init --recursive` command.

### Requirements

- QGIS(3.x)
- protobuf(>=3.17)
- pybind(>=2.7.1)

The requirements except QGIS can be installed with the `pip -r requirements.txt` command.

### Deploy plugin to QGIS3

On Linux, the plugin can be deployed to QGIS by calling the `make deploy` command in the root directory. <br>

For other systems, the `QGISDIR` variable in the `Makefile` must be changed to point to the QGIS plugin directory.
Some plugin directories are listed below:

* Linux (default):`.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
* Mac OS X: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`
* Windows: `AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`

For example, the plugin is located on linux under: `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`

Finally, the plugin needs to be enabled in QGIS (Plugins -> Manage and Install Plugins...)

### Alternative Installation

An alternative is to clone the repository directly into the folder located under `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`.
After copying, the commands `make proto`, `make transcompile` and `make pybind_build` need to be executed.

### Create .zip file

The `make zip` command creates a .zip file containing the plugin. The file can be used to distribute or install the plugin in QGIS.
The plugin can be installed in QGIS under Plugins -> Manage and Install Plugins... -> Install from ZIP.

## Usage
The Plugin provides several User-Interfaces for easily create, visualize, analyse and modify graphs. 
Detailed usage information can be found in the [handbook]().


