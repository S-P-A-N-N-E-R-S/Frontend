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

from enum import Enum

from qgis.core import QgsSettings, QgsApplication, QgsAuthMethodConfig, QgsTask

from .base import BaseController
from .. import helperFunctions as helper
from ..network import parserFetcher

# client imports
from ..network.client import Client
from ..network.exceptions import NetworkClientError, ParseError, ServerError


class TaskOptions(Enum):
    LOGIN = 0
    CREATE_USER = 1


class OptionsController(BaseController):

    activeTask = None

    def __init__(self, view):
        """
        Constructor
        :type view: OptionsView
        """
        super().__init__(view)
        self.settings = QgsSettings()
        self.authManager = QgsApplication.authManager()

        # show saved settings
        username = helper.getUsername()
        savedAuthId = helper.getAuthId()

        self.view.setHost(helper.getHost())
        self.view.setPort(helper.getPort())
        self.view.setSsl(helper.getEncryptionOption())
        self.view.setSslCheck(helper.getEncryptionCertCheckOption())

        # init ssl input visibility
        self.view.setSslCheckVisibility(helper.getEncryptionOption())

        # check if id is set and not manually removed by user
        loggedIn = bool(username and savedAuthId and savedAuthId in self.authManager.configIds())
        self.view.setLoggedInView(loggedIn, username)

    def saveOptions(self):
        host = self.view.getHost()
        port = self.view.getPort()
        ssl = self.view.getSsl()
        sslCheck = self.view.getSslCheck()

        # save settings
        self.settings.setValue("ogdfplugin/host", host)
        self.settings.setValue("ogdfplugin/port", port)
        self.settings.setValue("ogdfplugin/ssl", ssl)
        self.settings.setValue("ogdfplugin/sslCheck", sslCheck)

    def saveAction(self):
        self.saveOptions()
        self.view.showSuccess(self.tr("Settings saved!"))

        parserFetcher.instance().refreshParsers()

    def updateCredentials(self, savedAuthId, hasAuth, username, password):
        # only save username if not empty
        self.settings.setValue("ogdfplugin/username", username)

        # save authentication
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

        # check if id is set and not manually removed by user
        return bool(username and savedAuthId and savedAuthId in self.authManager.configIds())

    def resetCredentials(self):
        savedAuthId = helper.getAuthId()
        hasAuth = savedAuthId and savedAuthId in self.authManager.configIds()
        self.updateCredentials(savedAuthId, hasAuth, "", "")

    def logOut(self):
        self.resetCredentials()
        parserFetcher.instance().resetParsers()
        self.view.setLoggedInView(False)

    def logIn(self, username=""):
        self.createTask(self.createLogInTask, "Logging in ...", username)

    def createLogInTask(self, _task, host, port, tlsOption):
        try:
            with Client(host, port, tlsOption) as client:
                response = client.checkAuthenticationData()
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

        if response:
            return {
                "method": TaskOptions.LOGIN,
                "success": self.tr("Logged in successfully!")
            }
        else:
            return {"error": self.tr("Login failed!")}

    def createUser(self, username=""):
        self.createTask(self.createUserCreationTask, "Creating user...", username, create=True)

    def createUserCreationTask(self, _task, host, port, tlsOption):
        try:
            with Client(host, port, tlsOption) as client:
                response = client.createUser()
        except (NetworkClientError, ParseError, ServerError) as error:
            return {"error": str(error)}

        if response:
            return {
                "method": TaskOptions.CREATE_USER,
                "success": self.tr("User created!")
            }
        else:
            return {"error": self.tr("User creation failed!")}

    def createTask(self, creationMethod, description, username="", create=False):
        if OptionsController.activeTask is not None:
            self.view.showError(self.tr("Please wait until previous user creation is finished!"))
            return

        username, password = self.view.getCredentials(username, create)

        savedAuthId = helper.getAuthId()
        hasAuth = savedAuthId and savedAuthId in self.authManager.configIds()

        if not password or not username or not hasAuth:
            return

        self.saveOptions()
        if not self.updateCredentials(savedAuthId, hasAuth, username, password):
            self.view.showWarning(self.tr("Error while saving credentials!"))
            return

        self.view.setNetworkButtonsEnabled(False)

        task = QgsTask.fromFunction(
            description,
            creationMethod,
            host=helper.getHost(),
            port=helper.getPort(),
            tlsOption=helper.getTlsOption(),
            on_finished=self.taskCompleted
        )
        QgsApplication.taskManager().addTask(task)
        OptionsController.activeTask = task
        self.view.showInfo(task.description())

    def taskCompleted(self, exception, result=None):
        """
        Processes the results of the user creation and login task.
        """
        # first remove active task to allow a new request.
        OptionsController.activeTask = None

        self.view.setNetworkButtonsEnabled(True)

        if exception is None:
            if result is None:
                # no result returned (probably manually canceled by the user)
                return

            if "success" in result:
                username = helper.getUsername()
                self.view.setLoggedInView(True, username)
                self.view.showSuccess(result["success"])

                parserFetcher.instance().refreshParsers()

            if "error" in result:
                username = helper.getUsername()
                self.resetCredentials()
                parserFetcher.instance().resetParsers()
                self.view.showError(str(result["error"]), self.tr("Network Error"))
                if result["method"] == TaskOptions.CREATE_USER:
                    self.createUser(username)
                else:
                    self.logIn(username)
        else:
            self.resetCredentials()
            parserFetcher.instance().resetParsers()
            self.view.showError(f"An unknown error occurred: {str(exception)}")
            raise exception
