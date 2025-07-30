from common_utils import common_loaders
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['diag_trouble_codes_ref_map'] = []
    map_items = stream.loadNumericType(2)
    for i in range(map_items):
        item = {}
        item['map_key'] = stream.loadNumericType(4)
        item['reference'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : MCDDbDiagTroubleCodeImpl
        obj['diag_trouble_codes_ref_map'].append(item)
    
    ref_counter = stream.loadNumericType(2)
    if ref_counter != 0:
        raise RuntimeError('Ref counter is {}'.format(ref_counter))
    
    obj['compu_method'] = DbObject.load_object_from_stream_if_exists(stream)
    obj['diag_coded_type'] = DbObject.load_object_from_stream_if_exists(stream)
    obj['physical_type'] = DbObject.load_object_from_stream_if_exists(stream)
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    obj['unique_object_identifier'] = stream.loadAsciiString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    obj['description_id'] = stream.loadAsciiString()[0]
    
    # additional DTCs possible: getLoadStreamByName('D') (1800c7ac8)
    
    return obj
