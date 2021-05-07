# Frontend

# Usage
When loaded, select a VectorLayer and click the green Button in the Plugin Toolbar. 

The plugin loads the VectorLayer into a QgsGraph and the QgsGraph into a new VectorLayer.

# Deploy plugin to QGIS3

The plugin can be deployed to QGIS on Linux with the following command: `make deploy`

The plugin is located under: `/home/<user>/.local/share/QGIS/QGIS3/profiles/default/python/plugins`

Finally, the plugin needs to be enabled in QGIS.

# Create .zip file

The following command deploys the plugin to QGIS and creates a .zip file: `make zip`

