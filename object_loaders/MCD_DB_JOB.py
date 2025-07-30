from object_loaders import MCD_DB_DATA_PRIMITIVE
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['major'] = stream.loadNumericType(4)
    obj['minor'] = stream.loadNumericType(4)
    obj['revision'] = stream.loadNumericType(4)
    
    obj['db_code_informations'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbCodeInformationsImpl
    
    obj['is_reduced_result_enabled'] = bool(stream.loadOneByteType())
    
    obj['data_primitive'] = {'#OBJECT_TYPE': 'MCD_DB_DATA_PRIMITIVE'}
    obj['data_primitive'].update(MCD_DB_DATA_PRIMITIVE.load(stream))
    
    return obj
