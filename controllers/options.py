from .base import BaseController

from qgis.core import QgsSettings, QgsApplication, QgsAuthMethodConfig

class OptionsController(BaseController):

    def __init__(self, view):
        """
        Constructor
        :type view: OptionsView
        """
        super().__init__(view)
        self.settings = QgsSettings()
        self.authManager = QgsApplication.authManager()

        # show saved settings
        host = self.settings.value("protoplugin/host", "")
        port = self.settings.value("protoplugin/port", 80)
        username = self.settings.value("protoplugin/username", "")
        savedAuthId = self.settings.value("protoplugin/authId")

        self.view.setHost(host)
        self.view.setPort(int(port))
        self.view.setUsername(username)
        # check if id is set and not manually removed by user
        if savedAuthId and savedAuthId in self.authManager.configIds():
            self.view.setPasswordPlaceholder("Change password")

    def saveOptions(self):
        host = self.view.getHost()
        port = self.view.getPort()
        username = self.view.getUsername()
        password = self.view.getPassword()

        # save settings
        self.settings.setValue("protoplugin/host", host)
        self.settings.setValue("protoplugin/port", port)
        self.settings.setValue("protoplugin/username", username)

        # save authentication
        if username and password:
            config = QgsAuthMethodConfig()
            config.setName("protoplugin/serverAuth")
            config.setMethod("Basic")
            config.setConfig("username", username)
            config.setConfig("password", password)

            savedAuthId = self.settings.value("protoplugin/authId")
            # check if id is set and not manually removed by user
            if savedAuthId and savedAuthId in self.authManager.configIds():
                # update existing config
                config.setId(savedAuthId)
                self.authManager.updateAuthenticationConfig(config)
            else:
                # create new config
                self.authManager.storeAuthenticationConfig(config)

            self.settings.setValue("protoplugin/authId", config.id())

        if password and not username:
            self.view.showWarning("Please enter an username!")
        else:
            self.view.showSuccess("Settings saved!")
