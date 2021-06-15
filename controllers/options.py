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
        port = self.settings.value("protoplugin/port", 4711)
        username = self.settings.value("protoplugin/username", "")
        savedAuthId = self.settings.value("protoplugin/authId")

        self.view.setHost(host)
        self.view.setPort(int(port))
        # check if id is set and not manually removed by user
        if savedAuthId and savedAuthId in self.authManager.configIds():
            self.view.setUsername(username)
            self.view.setPasswordPlaceholder("Change password")

    def saveOptions(self):
        host = self.view.getHost()
        port = self.view.getPort()
        username = self.view.getUsername()
        password = self.view.getPassword()
        savedAuthId = self.settings.value("protoplugin/authId")

        # true if authId stored in authentication database
        hasAuth = savedAuthId and savedAuthId in self.authManager.configIds()

        # save settings
        self.settings.setValue("protoplugin/host", host)
        self.settings.setValue("protoplugin/port", port)
        # only save username if not empty
        if username:
            self.settings.setValue("protoplugin/username", username)

        # save authentication
        if username and password:
            config = QgsAuthMethodConfig()
            config.setName("protoplugin/serverAuth")
            config.setMethod("Basic")
            config.setConfig("username", username)
            config.setConfig("password", password)

            # check if id is set and not manually removed by user
            if hasAuth:
                # update existing config
                config.setId(savedAuthId)
                self.authManager.updateAuthenticationConfig(config)
            else:
                # create new config
                hasAuth = self.authManager.storeAuthenticationConfig(config)

            self.settings.setValue("protoplugin/authId", config.id())

        elif username and hasAuth:
            # update username but remain password
            config = QgsAuthMethodConfig()
            # load saved authentication
            self.authManager.loadAuthenticationConfig(savedAuthId, config, True)
            config.setConfig("username", username)
            self.authManager.updateAuthenticationConfig(config)

        if password and not username or not username and hasAuth:
            self.view.showWarning("Please enter an username!")
        elif not password and username and not hasAuth:
            self.view.showWarning("Please enter a password!")
        else:
            self.view.showSuccess("Settings saved!")
