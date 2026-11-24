# Stand-ins for native dependencies, so the scripts can be imported without them.
# Import this module before importing dumpMWB, parseMWB or dumpECUVariantPatterns.
import sys
import types


# classes.PBL loads a Windows DLL through ctypes; replace it with a class that does nothing
pbl_module = types.ModuleType('classes.PBL')


class PBL:
    def __init__(self, dll_path):
        pass


pbl_module.PBL = PBL
sys.modules['classes.PBL'] = pbl_module

# classes.LongNameTranslation needs jpype (which needs a JVM)
for name in ('jpype', 'jpype.imports', 'jpype.types'):
    sys.modules[name] = types.ModuleType(name)
# "from jpype.types import *" needs an __all__
sys.modules['jpype.types'].__all__ = []
