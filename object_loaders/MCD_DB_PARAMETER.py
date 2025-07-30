from common_utils import common_loaders
from common_utils import enum_converters
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['description'] = stream.loadUnicodeString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['some_id'] = stream.loadAsciiString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    obj['unique_object_id'] = stream.loadAsciiString()[0]
    
    obj['bit_position'] = stream.loadNumericType(1)
    obj['byte_position'] = stream.loadNumericType(4)
    
    flags = stream.loadNumericType(1)
    
    obj['default_mcd_value'] = None
    if flags & (1 << 0):
        obj['default_mcd_value'] = common_loaders.loadMCDValueFromObjectStream(stream)
    
    obj['display_level'] = stream.loadNumericType(4)
    
    obj['semantic'] = None
    if flags & (1 << 1):
        obj['semantic'] = stream.loadAsciiString()[0]
    
    obj['sys_param'] = stream.loadAsciiString()[0]
    
    obj['mcd_parameter_type'] = enum_converters.get_MCDParameterType(0x7000 + stream.loadNumericType(1))
    
    obj['layer_id'] = None
    layer_id = stream.loadEnumSmallRange()
    if layer_id != 0xFF:
        obj['layer_id'] = layer_id
    
    obj['diag_coded_type'] = None
    if flags & (1 << 2):
        obj['diag_coded_type'] = DbObject.load_object_from_stream_if_exists(stream) # DbDiagCodedType
    
    obj['db_object_ref'] = None
    if flags & (1 << 3):
        obj['db_object_ref'] = common_loaders.load_reference(stream, False)
    
    # DOP base ?
    if flags & (1 << 4):
        raise RuntimeError('_MCD_DB_PARAMETER.py: Flag 1<<4 set')
    
    obj['is_byte_pos_available'] = bool(flags & (1 << 5))
    
    #obj['special_data_group_refs'] = None
    if flags & (1 << 6):
        raise RuntimeError('_MCD_DB_PARAMETER.py: Flag 1<<6 set')
    
    obj['is_protocol_parameter'] = bool(flags & (1 << 7))
    
    if obj['mcd_parameter_type'] == 'eNRC_CONST':
        raise RuntimeError('_MCD_DB_PARAMETER.py: Is eNRC_CONST')
    
    return obj
