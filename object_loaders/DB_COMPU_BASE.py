from common_utils import common_loaders
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['compu_scales'] = DbObject.load_object_from_stream_if_exists(stream) # DbCompuScales
    
    obj['compu_default_value'] = common_loaders.loadMCDValueFromObjectStream(stream)
    obj['compu_code_byte_stream'] = common_loaders.loadMCDValueFromObjectStream(stream)
    
    obj['code_information'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbCodeInformationImpl
    
    obj['compu_inverse_value'] = common_loaders.loadMCDValueFromObjectStream(stream)
    
    return obj
