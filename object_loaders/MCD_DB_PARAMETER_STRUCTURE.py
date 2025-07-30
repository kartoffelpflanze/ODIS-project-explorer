from classes import DbObject


def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    obj['description_id'] = stream.loadAsciiString()[0]
    obj['unique_object_id'] = stream.loadAsciiString()[0]
    
    obj['byte_size'] = stream.loadNumericType(2)
    
    obj['parameters'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbParametersImpl
    
    return obj
