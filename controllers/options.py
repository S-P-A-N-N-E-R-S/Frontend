#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Dennis Benz
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

from qgis.core import QgsSettings, QgsApplication, QgsAuthMethodConfig

from .base import BaseController
from .. import helperFunctions as helper
from ..network import parserManager


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
        self.view.setSsl(helper.getEncryptionOption())
        self.view.setSslCheck(helper.getEncryptionCertCheckOption())

        # init ssl input visibility
        self.view.setSslCheckVisibility(helper.getEncryptionOption())

        # check if id is set and not manually removed by user
        if savedAuthId and savedAuthId in self.authManager.configIds():
            self.view.setUsername(username)
            self.view.setPasswordPlaceholder(self.tr("Change password"))

    def saveOptions(self):
        host = self.view.getHost()
        port = self.view.getPort()
        ssl = self.view.getSsl()
        sslCheck = self.view.getSslCheck()
        username = self.view.getUsername()
        password = self.view.getPassword()
        savedAuthId = self.settings.value("ogdfplugin/authId")

        # true if authId stored in authentication database
        hasAuth = savedAuthId and savedAuthId in self.authManager.configIds()

        # save settings
        self.settings.setValue("ogdfplugin/host", host)
        self.settings.setValue("ogdfplugin/port", port)
        self.settings.setValue("ogdfplugin/ssl", ssl)
        self.settings.setValue("ogdfplugin/sslCheck", sslCheck)

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
            self.view.showWarning(self.tr("Please enter a username!"))
        elif not password and username and not hasAuth:
            self.view.showWarning(self.tr("Please enter a password!"))
        else:
            self.view.showSuccess(self.tr("Settings saved!"))

        parserManager.resetParsers()
