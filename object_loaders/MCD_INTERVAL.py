from common_utils import common_loaders
from common_utils import enum_converters


def load(stream):
    obj = {}
    
    obj['lower_limit'] = common_loaders.loadMCDValueFromObjectStream(stream)
    obj['upper_limit'] = common_loaders.loadMCDValueFromObjectStream(stream)
    
    flags = stream.loadNumericType(1)
    
    if flags & 0x02:
        lower_limit_type_enum = 0x6D03 # infinite
    else:
        if flags & 0x01:
            lower_limit_type_enum = 0x6D02 # closed
        else:
            lower_limit_type_enum = 0x6D01 # open
    
    if flags & 0x20:
        upper_limit_type_enum = 0x6D03 # infinite
    else:
        if flags & 0x10:
            upper_limit_type_enum = 0x6D02 # closed
        else:
            upper_limit_type_enum = 0x6D01 # open
    
    obj['lower_limit_type'] = enum_converters.get_MCDLimitType(lower_limit_type_enum)
    obj['upper_limit_type'] = enum_converters.get_MCDLimitType(upper_limit_type_enum)
    
    return obj
