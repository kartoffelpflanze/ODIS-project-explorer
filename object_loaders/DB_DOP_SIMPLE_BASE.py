from common_utils import common_loaders
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    
    obj['compu_method'] = DbObject.load_object_from_stream_if_exists(stream) # DbCompuMethod
    obj['diag_coded_type'] = DbObject.load_object_from_stream_if_exists(stream) # DbDiagCodedType
    obj['physical_type'] = DbObject.load_object_from_stream_if_exists(stream) # DbPhysicalType
    
    obj['phys_to_coded_index_map'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        item['map_key'] = stream.loadNumericType(4)
        item['item'] = stream.loadNumericType(2)
        obj['phys_to_coded_index_map'].append(item)

    obj['coded_to_phys_index_map'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        item['map_key'] = stream.loadNumericType(4)
        item['item'] = stream.loadNumericType(2)
        obj['coded_to_phys_index_map'].append(item)
    
    obj['units_ref'] = None
    if stream.loadOneByteType():
        obj['units_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : MCDDbUnitImpl
    
    obj['internal_constraint_ref'] = None
    if stream.loadOneByteType():
        obj['internal_constraint_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : MCDConstraintImpl
    
    obj['physical_constraint_ref'] = None
    if stream.loadOneByteType():
        obj['physical_constraint_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : MCDConstraintImpl
    
    return obj
