from classes import DbObject


def load(stream):
    obj = {}
    
    obj['object_id'] = stream.loadAsciiString()[0]
    obj['pool_id'] = stream.loadAsciiString()[0]
    
    obj['access_keys'] = []
    for i in range(stream.loadOneByteType()):
        obj['access_keys'].append(DbObject.load_object_from_stream(stream))
    
    return obj
