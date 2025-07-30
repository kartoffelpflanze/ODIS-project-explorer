from common_utils import common_loaders
from common_utils import enum_converters
from classes import DbObject


def initEncoding(base_data_type, encoding):
    orig_encoding = encoding
    
    match base_data_type:
        case 'eDB_INT32':
            if encoding not in ['e1C', 'e2C', 'eSM']:
                encoding = 'e2C'
        case 'eDB_UINT32':
            if encoding not in ['eBCD_P', 'eBCD_UP']:
                encoding = 'eNONE'
        case 'eDB_FLOAT32' | 'eDB_FLOAT64':
            if encoding != 'eIEEE754':
                encoding = 'eNONE'
        case 'eDB_ASCIISTRING':
            if encoding not in ['eISO_8859_1', 'eISO_8859_2', 'eWINDOWS_1252']:
                encoding = 'eISO_8859_1'
        case 'eDB_UTF8STRING':
            encoding = 'eUTF_8'
        case 'eDB_UNICODE2STRING':
            encoding = 'eUCS_2'
        case 'eDB_BYTEFIELD':
            if encoding not in ['eBCD_P', 'eBCD_UP']:
                encoding = 'eNONE'
        case 'eDB_BITFIELD':
            encoding = 'eNONE'
        case _:
            encoding = 'eNONE'
    
    if orig_encoding != encoding:
        raise RuntimeError('Encoding changed from {} to {} for type {}'.format(orig_encoding, encoding, base_data_type))
    
    return encoding


def load(stream):
    obj = {}
    
    obj['type'] = enum_converters.get_EDbDiagCodedType(stream.loadEnumSmallRange())
    
    if obj['type'] == 'eMIN_MAX_LENGTH_TYPE':
        obj['max_length'] = stream.loadNumericType(4)
        obj['min_length'] = stream.loadNumericType(4)
        obj['termination'] = enum_converters.get_EDbTermination(stream.loadEnumSmallRange())
    else:
        obj['bit_length'] = stream.loadNumericType(4)
        
    if obj['type'] == 'eSTANDARD_LENGTH_TYPE':
        obj['bit_mask'] = common_loaders.loadBytefieldFromObjectStream(stream)
    
    EDbDataType_enum = stream.loadEnumSmallRange()
    obj['base_data_type'] = enum_converters.get_EDbDataType(EDbDataType_enum)
    obj['base_data_type_as_mcd_data_type'] = enum_converters.get_MCDDataType(enum_converters.map_enum_EDbDataType_to_MCDDataType(EDbDataType_enum))
    obj['encoding'] = initEncoding(obj['base_data_type'], enum_converters.get_EDbEncoding(stream.loadEnumSmallRange()))
    
    obj['is_high_low_byte_order'] = bool(stream.loadOneByteType())
    obj['is_condensed_bit_mask'] = bool(stream.loadOneByteType())
    
    if obj['type'] == 'ePARAM_LENGTH_INFO_TYPE':
        obj['length_key_parameter'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbParameterImpl
    
    return obj
