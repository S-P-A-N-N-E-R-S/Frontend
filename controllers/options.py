from .base import BaseController

from qgis.core import QgsSettings

class OptionsController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OptionsView
        """
        super().__init__(view)
        self.settings = QgsSettings()

        # show saved settings
        host = self.settings.value("protoplugin/host", "")
        port = self.settings.value("protoplugin/port", "")
        username = self.settings.value("protoplugin/username", "")

        self.view.setHost(host)
        self.view.setPort(port)
        self.view.setUsername(username)

    def saveOptions(self):
        host = self.view.getHost()
        port = self.view.getPort()
        username = self.view.getUsername()

        self.settings.setValue("protoplugin/host", host)
        self.settings.setValue("protoplugin/port", port)
        self.settings.setValue("protoplugin/username", username)