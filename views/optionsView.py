from .baseContentView import BaseContentView
from ..controllers.options import OptionsController


class OptionsView(BaseContentView):

    def __init__(self, dialog):
        super().__init__(dialog)
        self.name = "options"
        self.controller = OptionsController(self)

        self.dialog.options_save_btn.clicked.connect(self.controller.saveOptions)

    def getServerAddress(self):
        return self.dialog.options_server_adress_input.text()

    def setServerAddress(self, address):
        self.dialog.options_server_adress_input.setText(address)

    # credentials

    def getUsername(self):
        return self.dialog.options_credentials_username_input.text()

    def setUsername(self, username):
        self.dialog.options_credentials_username_input.setText(username)

    def getPassword(self):
        return self.dialog.options_credentials_password_input.text()
