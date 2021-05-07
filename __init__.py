from .mainPlugin import ProtoPlugin

def classFactory(iface):
    return ProtoPlugin(iface)