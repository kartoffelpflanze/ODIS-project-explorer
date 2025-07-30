from common_utils import enum_converters


def load(stream):
    obj = {}
    
    EDbPhysicalDataType_enum = stream.loadEnumSmallRange()
    obj['base_data_type'] = enum_converters.get_EDbDataType(enum_converters.map_enum_EDbPhysicalDataType_to_EDbDataType(EDbPhysicalDataType_enum))
    obj['base_data_type_as_mcd_data_type'] = enum_converters.get_MCDDataType(enum_converters.map_enum_EDbPhysicalDataType_to_MCDDataType(EDbPhysicalDataType_enum))
    
    obj['is_precision_available'] = bool(stream.loadNumericType(1))
    if obj['is_precision_available']:
        obj['precision'] = stream.loadNumericType(2)
    
    obj['display_radix'] = stream.loadEnumSmallRange()
    
    return obj
