
class BaseContentWindow:


    def __init__(self, dialog):
        """
        Base constuctor of a content window
        :param dialog: contains all ui elements
        """
        self.name = None
        self.dialog = dialog

    def setupWindow(self):
        """
        Sets up the contents and Slots of the content window
        :return:
        """
        raise NotImplementedError
