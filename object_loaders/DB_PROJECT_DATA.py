from common_utils import common_loaders
from object_loaders import MCD_DB_LOCATION_REFERENCES
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['location_refs'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        obj['location_refs'].append(MCD_DB_LOCATION_REFERENCES.load(stream))
    
    obj['functional_group_ref'] = common_loaders.load_reference(stream)
    obj['ecu_base_variant_ref'] = common_loaders.load_reference(stream)
    obj['ecu_variant_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    obj['ecu_variant_ref'] = common_loaders.load_reference(stream)
    
    obj['string1'] = stream.loadAsciiString()[0]
    obj['string2'] = stream.loadAsciiString()[0]
    obj['string3'] = stream.loadAsciiString()[0]
    
    obj['functional_groups'] = common_loaders.loadAsciiStringVectorFromObjectStream(stream)
    
    obj['ecu_variants'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        obj['ecu_variants'].append(DbObject.load_object_from_stream_if_exists(stream))
    
    return obj
