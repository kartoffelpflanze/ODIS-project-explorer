from classes import DbObject


def load(stream):
    obj = {}
    
    obj['matching_parameters'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbMatchingParametersImpl
    
    return obj
