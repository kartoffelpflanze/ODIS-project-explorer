from classes import DbObject


def load(stream):
    obj = {}
    
    obj['interval'] = DbObject.load_object_from_stream_if_exists(stream) # MCDIntervalImpl
    obj['scale_constraints'] = DbObject.load_object_from_stream_if_exists(stream) # MCDScaleConstraintsImpl
    
    obj['is_computed'] = bool(stream.loadOneByteType())
    
    return obj
