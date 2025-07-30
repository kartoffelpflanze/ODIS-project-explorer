from common_utils import enum_converters
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['interval'] = DbObject.load_object_from_stream_if_exists(stream) # MCDIntervalImpl
    
    obj['range_info'] = enum_converters.get_MCDRangeInfo(0x600 + stream.loadNumericType(1))
    
    obj['description'] = stream.loadUnicodeString()[0]
    obj['description_id'] = stream.loadAsciiString()[0]
    obj['short_label'] = stream.loadAsciiString()[0]
    obj['short_label_id'] = stream.loadAsciiString()[0]
    
    obj['is_computed'] = bool(stream.loadOneByteType())
    
    return obj
