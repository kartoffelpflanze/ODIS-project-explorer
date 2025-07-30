from common_utils import enum_converters
from object_loaders import MCD_DB_DATA_PRIMITIVE
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['items'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        
        item['string'] = stream.loadAsciiString()[0]
        item['service_protocol_parameters'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbRequestParametersImpl
        
        obj['items'].append(item)
    
    obj['runtime_mode'] = enum_converters.get_MCDRuntimeMode(stream.loadEnumMediumRange())
    
    obj['is_multiple'] = bool(stream.loadOneByteType())
    
    obj['data_primitive'] = {'#OBJECT_TYPE': 'MCD_DB_DATA_PRIMITIVE'}
    obj['data_primitive'].update(MCD_DB_DATA_PRIMITIVE.load(stream))
    
    return obj
