from .base import BaseController
from .. import mainPlugin
from .. import helperFunctions as helper

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
        username = self.settings.value("ogdfplugin/username", "")
        savedAuthId = self.settings.value("ogdfplugin/authId")

        self.view.setHost(helper.getHost())
        self.view.setPort(helper.getPort())
        # check if id is set and not manually removed by user
        if savedAuthId and savedAuthId in self.authManager.configIds():
            self.view.setUsername(username)
            self.view.setPasswordPlaceholder(self.tr("Change password"))

    def saveOptions(self):
        host = self.view.getHost()
        port = self.view.getPort()
        username = self.view.getUsername()
        password = self.view.getPassword()
        savedAuthId = self.settings.value("ogdfplugin/authId")

        # true if authId stored in authentication database
        hasAuth = savedAuthId and savedAuthId in self.authManager.configIds()

        # save settings
        self.settings.setValue("ogdfplugin/host", host)
        self.settings.setValue("ogdfplugin/port", port)
        # fetch available handlers
        mainPlugin.OGDFPlugin.fetchHandlers()
        # only save username if not empty
        if username:
            self.settings.setValue("ogdfplugin/username", username)

        # save authentication
        if username and password:
            config = QgsAuthMethodConfig()
            config.setName("ogdfplugin/serverAuth")
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

            self.settings.setValue("ogdfplugin/authId", config.id())

        elif username and hasAuth:
            # update username but remain password
            config = QgsAuthMethodConfig()
            # load saved authentication
            self.authManager.loadAuthenticationConfig(savedAuthId, config, True)
            config.setConfig("username", username)
            self.authManager.updateAuthenticationConfig(config)

        if password and not username or not username and hasAuth:
            self.view.showWarning(self.tr("Please enter an username!"))
        elif not password and username and not hasAuth:
            self.view.showWarning(self.tr("Please enter a password!"))
        else:
            self.view.showSuccess(self.tr("Settings saved!"))
