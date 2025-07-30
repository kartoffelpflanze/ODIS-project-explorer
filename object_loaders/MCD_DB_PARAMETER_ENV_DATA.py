from classes import DbObject


def load(stream):
    obj = {}
    
    obj['byte_length'] = stream.loadNumericType(2)
    
    obj['parameters'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbParametersImpl
    
    return obj
