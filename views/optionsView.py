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

from .baseContentView import BaseContentView
from ..controllers.options import OptionsController


class OptionsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"
        self.controller = OptionsController(self)

        self.dialog.options_save_btn.clicked.connect(self.controller.saveOptions)

    def getHost(self):
        return self.dialog.options_server_host_input.text()

    def setHost(self, host):
        self.dialog.options_server_host_input.setText(host)

    def getPort(self):
        return self.dialog.options_server_port_input.value()

    def setPort(self, port):
        self.dialog.options_server_port_input.setValue(port)

    # authentication

    def getUsername(self):
        return self.dialog.options_credentials_username_input.text()

    def setUsername(self, username):
        self.dialog.options_credentials_username_input.setText(username)

    def getPassword(self):
        return self.dialog.options_credentials_password_input.text()

    def setPasswordPlaceholder(self, text):
        self.dialog.options_credentials_password_input.setPlaceholderText(text)
