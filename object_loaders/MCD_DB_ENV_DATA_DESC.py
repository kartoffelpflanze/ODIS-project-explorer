from classes import DbObject


def load(stream):
    obj = {}
    
    s1 = stream.loadUnicodeString()[0]
    if s1 is not None:
        raise RuntimeError('s1: {}'.format(s1))
    
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['short_name'] = stream.loadAsciiString()[0]
    
    s4 = stream.loadAsciiString()[0]
    if s4 is not None:
        raise RuntimeError('s4: {}'.format(s4))
    s5 = stream.loadAsciiString()[0]
    if s5 is not None:
        raise RuntimeError('s5: {}'.format(s5))
    s6 = stream.loadAsciiString()[0]
    if s6 is not None:
        raise RuntimeError('s6: {}'.format(s6))
    
    obj['env_data_param_map'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        item['key'] = stream.loadNumericType(4)
        item['string'] = stream.loadAsciiString()[0]
        obj['env_data_param_map'].append(item)
    
    # Not a mistake, 1b is checked twice
    if stream.loadOneByteType():
        obj['all_value_db_env_data_param'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbParameterImpl
    
    obj['env_data_params'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        
        item['string'] = stream.loadAsciiString()[0]
        item['param'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbParameterImpl
        
        # loadVectorFromObjectStream
        
        item['vector'] = []
        vector_items = stream.loadNumericType(4)
        for j in range(vector_items):
            item['vector'].append(stream.loadNumericType(4))
        
        obj['env_data_params'].append(item)
    
    return obj
