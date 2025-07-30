from common_utils import common_loaders
from object_loaders import MCD_DB_ECU


def load(stream):
    obj = {}
    
    obj['group_member_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    
    obj['ecu'] = {'#OBJECT_TYPE': 'MCD_DB_ECU'}
    obj['ecu'].update(MCD_DB_ECU.load(stream))
    
    return obj
