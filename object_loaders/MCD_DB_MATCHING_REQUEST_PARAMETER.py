from object_loaders import MCD_DB_PARAMETER


def load(stream):
    obj = MCD_DB_PARAMETER.load(stream) # super = MCDDbParameterImpl
    
    obj['request_byte_position'] = stream.loadNumericType(4)
    obj['byte_length'] = stream.loadNumericType(4)
    
    return obj
