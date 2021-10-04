# Frontend

# Requirements

- Protobuf(>=3.17)
- pybind(>=2.7.1)

# Deploy plugin to QGIS3

The plugin can be deployed to QGIS on Linux with the following command: `make deploy`

The plugin is located under: `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`

Finally, the plugin needs to be enabled in QGIS (Plugins -> Manage and Install Plugins...)

An alternative is to clone the repository directly into the folder `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
and to execute `make proto` and `make pybind_build`

# Create .zip file

The following command deploys the plugin to QGIS and creates a .zip file: `make zip`

