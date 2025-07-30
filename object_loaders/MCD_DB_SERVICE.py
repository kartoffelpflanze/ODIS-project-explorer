from common_utils import enum_converters
from object_loaders import MCD_DB_DIAG_SERVICE


def load(stream):
    obj = {}
    
    obj['repetition_mode'] = enum_converters.get_MCDAddressingMode(0x6000 + stream.loadNumericType(1))
    
    obj.update(MCD_DB_DIAG_SERVICE.load(stream)) # super = MCDDbDiagServiceImpl
    
    return obj
