from common_utils import enum_converters
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['compu_category'] = enum_converters.get_EDbCompuCategory(stream.loadEnumSmallRange())
    
    obj['compu_phys_to_internal'] = DbObject.load_object_from_stream_if_exists(stream) # DbCompuBase
    obj['compu_internal_to_phys'] = DbObject.load_object_from_stream_if_exists(stream) # DbCompuBase
    
    if obj['compu_category'] == 'eTEXTTAB':
        if obj['compu_phys_to_internal'] is not None and obj['compu_phys_to_internal']['compu_inverse_value'] is not None:
            obj['compu_inverse_val_id'] = stream.loadAsciiString()[0]
        if obj['compu_internal_to_phys'] is not None and obj['compu_internal_to_phys']['compu_default_value'] is not None:
            obj['compu_default_val_id'] = stream.loadAsciiString()[0]
    
    return obj
