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

from .baseView import BaseView
from ..controllers.options import OptionsController


class OptionsView(BaseView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"
        self.controller = OptionsController(self)

        self.dialog.options_save_btn.clicked.connect(self.controller.saveOptions)

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

    def getUsername(self):
        return self.dialog.options_credentials_username_input.text()

    def setUsername(self, username):
        self.dialog.options_credentials_username_input.setText(username)

    def getPassword(self):
        return self.dialog.options_credentials_password_input.text()

    def setPasswordPlaceholder(self, text):
        self.dialog.options_credentials_password_input.setPlaceholderText(text)
