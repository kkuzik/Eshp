from .Eshp import Eshp

def classFactory(iface):
    return Eshp(iface)
