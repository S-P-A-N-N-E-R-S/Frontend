from .mainPlugin import OGDFPlugin

def classFactory(iface):
    return OGDFPlugin(iface)