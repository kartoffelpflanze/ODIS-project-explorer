from common_utils import common_loaders
from common_utils import enum_converters
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['long_name_id'] = stream.loadAsciiString()[0]
    
    obj['compu_inverse_rational_coeffs'] = DbObject.load_object_from_stream_if_exists(stream) # DbCompuRationalCoeffs
    obj['compu_rational_coeffs'] = DbObject.load_object_from_stream_if_exists(stream) # DbCompuRationalCoeffs
    
    obj['lower_limit'] = DbObject.load_object_from_stream_if_exists(stream) # DbLimit
    obj['upper_limit'] = DbObject.load_object_from_stream_if_exists(stream) # DbLimit
    
    obj['compu_const'] = common_loaders.loadMCDValueFromObjectStream(stream)
    obj['compu_inverse_value'] = common_loaders.loadMCDValueFromObjectStream(stream)
    obj['compu_const_as_coded_value'] = common_loaders.loadMCDValueFromObjectStream(stream)
    
    obj['lower_limit_as_coded_value'] = DbObject.load_object_from_stream_if_exists(stream) # DbLimit
    obj['upper_limit_as_coded_value'] = DbObject.load_object_from_stream_if_exists(stream) # DbLimit
    
    return obj
