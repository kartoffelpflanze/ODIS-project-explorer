from common_utils import common_loaders
from object_loaders import MCD_DB_ECU
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['ecu_variant_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    
    obj['matching_patterns'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        
        item['short_name'] = stream.loadAsciiString()[0]
        item['items'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbMatchingPatternsImpl
        
        obj['matching_patterns'].append(item)
    
    obj['ecu'] = {'#OBJECT_TYPE': 'MCD_DB_ECU'}
    obj['ecu'].update(MCD_DB_ECU.load(stream))
    
    return obj
