from common_utils import common_loaders
from common_utils import enum_converters
from classes import DbObject


def loadStringToObjectMap(stream):
    obj = []
    
    map_item_count = stream.loadNumericType(2)
    for i in range(map_item_count):
        item = {}
        
        item['map_key'] = stream.loadAsciiString()[0]
        item['object'] = DbObject.load_object_from_stream_if_exists(stream)
        
        obj.append(item)
    
    return obj


def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    
    obj['unique_object_id'] = stream.loadAsciiString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    obj['description_id'] = stream.loadAsciiString()[0]

    obj['protocol_short_name'] = stream.loadAsciiString()[0]
    obj['base_variant_id'] = stream.loadAsciiString()[0]
    obj['functional_group_id'] = stream.loadAsciiString()[0]
    obj['protocol_type'] = stream.loadAsciiString()[0]
    
    counter = stream.loadNumericType(2)
    if counter:
        print('logical link refs not 0')
    
    obj['physical_vehicle_link_or_interface_ref'] = common_loaders.load_reference(stream)
    
    obj['gateway_mode'] = enum_converters.get_MCDGatewayMode(stream.loadEnumMediumRange())
    
    obj['accessed_via_gateway'] = bool(stream.loadOneByteType())
    
    obj['link_com_params_map'] = loadStringToObjectMap(stream)
    obj['link_complex_com_params_map'] = loadStringToObjectMap(stream)
    
    return obj
