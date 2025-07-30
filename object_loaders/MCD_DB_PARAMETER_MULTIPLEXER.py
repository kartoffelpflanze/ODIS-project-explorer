from classes import DbObject


def load(stream):
    obj = {}
    
    obj['byte_position'] = stream.loadNumericType(4)
    
    obj['switch_key'] = DbObject.load_object_from_stream_if_exists(stream) # DbSwitchKey
    obj['cases'] = DbObject.load_object_from_stream_if_exists(stream) # DbCases
    obj['default_case'] = DbObject.load_object_from_stream_if_exists(stream) # DbDefaultCase
    
    return obj
