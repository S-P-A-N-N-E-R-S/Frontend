#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
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

from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QLabel


class LoginDialog(QDialog):
    """
    Dialog for user login and user creation

    It provides two input fields for username and password.
    """

    def __init__(self, parent=None, username="", create=False):
        super().__init__(parent)

        # username input
        labelName = QLabel(self)
        labelName.setText("Username")
        self.textName = QLineEdit(self)
        if username:
            self.textName.setText(username)

        # password input
        labelPass = QLabel(self)
        labelPass.setText("Password")
        self.textPass = QLineEdit(self)
        self.textPass.setEchoMode(QLineEdit.Password)

        # set up buttons
        btnText = "Create User" if create else "Login"
        self.buttonLogin = QPushButton(btnText, self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        self.buttonCancel = QPushButton('Cancel', self)
        self.buttonCancel.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        btnLayout = QHBoxLayout(self)
        layout.addWidget(labelName)
        layout.addWidget(self.textName)
        layout.addWidget(labelPass)
        layout.addWidget(self.textPass)
        btnLayout.addWidget(self.buttonCancel)
        btnLayout.addWidget(self.buttonLogin)
        layout.addLayout(btnLayout)

    def handleLogin(self):
        if self.textName.text() and self.textPass.text():
            self.accept()
        elif not self.textName.text():
            QMessageBox.warning(self, 'Error', 'Missing username')
        elif not self.textPass.text():
            QMessageBox.warning(self, 'Error', 'Missing password')

    def getUsername(self):
        return self.textName.text()

    def getPassword(self):
        return self.textPass.text()
