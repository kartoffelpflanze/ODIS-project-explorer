from classes import DbObject


def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    obj['id'] = stream.loadAsciiString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    
    s3 = stream.loadAsciiString()[0]
    
    if s3 is not None:
        raise RuntimeError('Not None: {}'.format(s3))
    
    obj['request_parameters'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbRequestParametersImpl
    
    # obj['special_data_group_refs'] = None
    if stream.loadOneByteType():
        raise RuntimeError('SDGs present')
    
    return obj
