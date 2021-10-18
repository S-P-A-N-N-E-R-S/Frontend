from ..exceptions import ParseError

class BaseField:
    type = None

    def __init__(self, key="", label="", default=None, required=False):
        self.key = key
        self.label = label
        self.default = default
        self.required = required

    def getInfo(self):
        return {
            "type": self.type,
            "label": self.label,
            "default": self.default,
            "required": self.required,
        }


class BaseResult:
    type = None

    def __init__(self, key="", label=""):
        self.key = key
        self.label = label

    def getInfo(self):
        return {
            "type": self.type,
            "label": self.label,
        }

    def getProtoField(self, response):
        try:
            return getattr(response, self.key)
        except AttributeError as error:
            raise ParseError(f"Invalid key: {self.key}") from error

    def getProtoMapField(self, response):
        fieldName, mapKey = self.key.split(".")
        try:
            return getattr(response, fieldName)[mapKey]
        except AttributeError as error:
            raise ParseError(f"Invalid field name: {fieldName}") from error


class GraphDependencyMixin():
    graphKey = ""
