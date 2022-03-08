#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Dennis Benz, Leon Nienhüser
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

from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog

from .baseView import BaseView
from .widgets.loginDialog import LoginDialog
from ..controllers.options import OptionsController


class OptionsView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"
        self.controller = OptionsController(self)

        self.dialog.options_save_btn.clicked.connect(self.controller.saveAction)
        self.dialog.options_log_out_btn.clicked.connect(self.controller.logOut)
        self.dialog.options_log_in_btn.clicked.connect(self.controller.logIn)
        self.dialog.options_user_creation_btn.clicked.connect(self.controller.createUser)

        self.dialog.options_ssl_input.stateChanged.connect(self.updateSslCheckVisibility)

    def getHost(self):
        return self.dialog.options_server_host_input.text()

    def setHost(self, host):
        self.dialog.options_server_host_input.setText(host)

    def getPort(self):
        return self.dialog.options_server_port_input.value()

    def setPort(self, port):
        self.dialog.options_server_port_input.setValue(port)

    def getSsl(self):
        return self.dialog.options_ssl_input.isChecked()

    def setSsl(self, checked):
        self.dialog.options_ssl_input.setChecked(checked)

    def getSslCheck(self):
        return self.dialog.options_ssl_check_input.isChecked()

    def setSslCheck(self, checked):
        self.dialog.options_ssl_check_input.setChecked(checked)

    def updateSslCheckVisibility(self):
        self.dialog.options_ssl_check_input.setVisible(self.getSsl())

    def setSslCheckVisibility(self, visible):
        self.dialog.options_ssl_check_input.setVisible(visible)

    # authentication

    def getCredentials(self, username="", create=False):
        loginDialog = LoginDialog(username=username, create=create)
        if loginDialog.exec_() == QDialog.Accepted:
            return loginDialog.getUsername(), loginDialog.getPassword()
        return "", ""

    def getUsername(self):
        return self.dialog.options_credentials_username_input.text()

    def setUsername(self, username):
        self.dialog.options_credentials_username_input.setText(username)

    def getPassword(self):
        return self.dialog.options_credentials_password_input.text()

    def setLoggedInView(self, loggedIn, username=""):
        if loggedIn:
            loggedInText = f"{self.tr('Logged in as')}: {username}"
            self.dialog.ogdf_logged_in_label.setText(loggedInText)
        else:
            self.dialog.ogdf_logged_in_label.setText(self.tr("Not logged in"))
        self.dialog.options_log_out_btn.setVisible(loggedIn)
        self.dialog.options_log_in_btn.setVisible(not loggedIn)
        self.dialog.options_user_creation_btn.setVisible(not loggedIn)

    def setPasswordPlaceholder(self, text):
        self.dialog.options_credentials_password_input.setPlaceholderText(text)

    def setNetworkButtonsEnabled(self, enabled):
        self.dialog.options_save_btn.button(QDialogButtonBox.Save).setEnabled(enabled)
        self.dialog.options_user_creation_btn.setEnabled(enabled)
