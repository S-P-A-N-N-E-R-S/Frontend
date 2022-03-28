from .mainPlugin import SPANNERSPlugin

def classFactory(iface):
    return SPANNERSPlugin(iface)