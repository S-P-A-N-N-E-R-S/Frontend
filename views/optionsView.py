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
