from common_utils import common_loaders
from common_utils import enum_converters


def load(stream):
    obj = {}
    
    obj['mcd_value'] = common_loaders.loadMCDValueFromObjectStream(stream)
    obj['limit_type'] = enum_converters.get_MCDLimitType(stream.loadNumericType(1) + 0x6D00)
    
    return obj
