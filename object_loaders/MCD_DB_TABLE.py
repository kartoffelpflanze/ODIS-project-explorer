from common_utils import common_loaders


def load(stream):
    obj = {}
    
    s1 = stream.loadAsciiString()[0]
    if s1 is not None:
        raise RuntimeError('s1: {}'.format(s1))
    
    obj['some_id'] = stream.loadAsciiString()[0]
    
    obj['object_id'] = stream.loadAsciiString()[0]
    
    obj['description'] = stream.loadUnicodeString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['short_name'] = stream.loadAsciiString()[0]
    
    obj['table_key_map'] = []
    counter = stream.loadNumericType(4)
    for i in range(counter):
        item = {}
        
        item['map_key'] = stream.loadUnicodeString()[0]
        
        # DbNamedObjectReference : MCDDbTableParameterImpl
        named_reference = {}
        named_reference['object_id'] = stream.loadAsciiString()[0]
        named_reference['pool_id'] = stream.loadAsciiString()[0]
        named_reference['short_name'] = stream.loadAsciiString()[0]
        item['reference'] = named_reference
        
        obj['table_key_map'].append(item)
    
    obj['semantic'] = stream.loadAsciiString()[0]
    
    # MCDDbDiagComObjectReferences : DbDiagComObjectReference, MCDDbDiagComPrimitives, MCDDbDiagComPrimitive, MCDDbDiagComPrimitiveImpl
    obj['diag_com_primitives_refs'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream, common_loaders.load_DbDiagComObjectReference)
    
    if stream.loadOneByteType():
        obj['dop_simple_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : DbDopSimple
    
    # obj['special_data_group_refs'] = None
    if stream.loadOneByteType():
        raise RuntimeError('SDGs present')
    
    return obj
