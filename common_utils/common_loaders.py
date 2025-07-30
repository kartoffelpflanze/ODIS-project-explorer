import struct
from common_utils import enum_converters


# "Standard" loader for DbObjectReference
def load_reference(stream, third_string = True, string_vector = False):
    obj = {}
    
    obj['object_id'] = stream.loadAsciiString()[0]
    obj['pool_id'] = stream.loadAsciiString()[0]
    if third_string:
        obj['object_id2'] = stream.loadAsciiString()[0]
    
    if string_vector:
        obj['strings'] = []
        counter = stream.loadOneByteType()
        for i in range(counter):
            obj['strings'].append(stream.loadAsciiString()[0])
    
    return obj


# Custom loader for DbDiagComObjectReference
def load_DbDiagComObjectReference(stream, dummy = 0):
    item = {}
    
    item['attrib_obj_ref'] = loadDbAttributedObjectReference(stream)
    
    item['number'] = stream.loadNumericType(1)
    item['mcd_object_type'] = enum_converters.get_MCDObjectType(stream.loadEnumMediumRange())
    
    if stream.loadOneByteType():
        item['strings'] = loadAsciiStringVectorFromObjectStream(stream)
    
    return item


# Named reference
def loadNamedObjectReferenceFromObjectStream(stream, reference_loader = load_reference, reference_loader_argument = False):
    obj = {}
    
    obj['name'] = stream.loadAsciiString()[0]
    obj['reference'] = reference_loader(stream, reference_loader_argument)
    
    return obj


# Collection of named references
def loadNamedObjectReferenceCollectionFromObjectStream(stream, reference_loader = load_reference, reference_loader_argument = False):
    obj = []
    
    collection_items = stream.loadNumericType(2)
    for i in range(collection_items):
        obj.append(loadNamedObjectReferenceFromObjectStream(stream, reference_loader, reference_loader_argument))
    
    return obj


# ASCII string vector
def loadAsciiStringVectorFromObjectStream(stream):
    obj = []
    
    vector_items = stream.loadNumericType(2)
    for i in range(vector_items):
        obj.append(stream.loadAsciiString()[0])
    
    return obj


# ASCII string vector map (key + string vector)
def loadStringVectorMapFromObjectStream(stream):
    obj = []
    
    map_items = stream.loadNumericType(2)
    for i in range(map_items):
        item = {}
        
        item['map_key'] = stream.loadAsciiString()[0]
        item['strings'] = loadAsciiStringVectorFromObjectStream(stream)
        
        obj.append(item)
    
    return obj


# String-to-reference map (key + reference)
def loadStringToReferenceMap(stream, string_vector_in_reference = False, is_DbDiagComObjectReference = False, is_NamedObjectReference = False):
    obj = []
    
    map_items = stream.loadNumericType(2)
    for i in range(map_items):
        item = {}
        
        item['map_key'] = stream.loadAsciiString()[0]
        
        if is_DbDiagComObjectReference:
            item['reference'] = load_DbDiagComObjectReference(stream)
        elif is_NamedObjectReference:
            item['reference'] = loadNamedObjectReferenceFromObjectStream(stream)
        else:
            item['reference'] = load_reference(stream, False, string_vector_in_reference)
        
        obj.append(item)
    
    return obj


# Attributed reference (reference + strings)
def loadDbAttributedObjectReference(stream, dummy = 0):
    obj = {}
    
    obj['object_id'] = stream.loadAsciiString()[0]
    obj['pool_id'] = stream.loadAsciiString()[0]
    
    obj['strings'] = []
    counter = stream.loadOneByteType()
    for i in range(counter):
        obj['strings'].append(stream.loadAsciiString()[0])
    
    return obj


# MCDValue (data type + value)
def loadMCDValueFromObjectStream(stream):
    obj = {}
    
    obj['data_type'] = enum_converters.get_mcd_value_data_type_enum(stream.loadNumericType(1))
    
    match obj['data_type']:
        case 'eA_ASCIISTRING':
            obj['value'] = stream.loadAsciiString()[0]
        case 'eA_UNICODE2STRING':
            obj['value'] = stream.loadUnicodeString()[0]
        case 'eA_FLOAT32':
            obj['value'] = struct.unpack('<f', stream.read(4))[0]
        case 'eA_FLOAT64':
            obj['value'] = struct.unpack('<d', stream.read(8))[0]
        case 'eA_INT32':
            obj['value'] = stream.loadNumericType(4, True)
        case 'eA_UINT32':
            obj['value'] = stream.loadNumericType(4)
        case 'eA_BITFIELD'| 'eA_BYTEFIELD':
            obj['value'] = bytearray()
            if stream.loadOneByteType() != 0:
                size = stream.loadNumericType(2)
                obj['value'] = stream.read(size)
        case 'eNO_TYPE':
            return None
        case _:
            raise RuntimeError('Unknown how to retrieve MCD value with type {}'.format(obj['data_type']))
    
    return obj


# Bytefield
def loadBytefieldFromObjectStream(stream):
    obj = bytearray()
    
    if stream.loadOneByteType() != 0:
        size = stream.loadNumericType(4)
        obj = stream.read(size)
    
    return obj


# Collection of references (for SDGs, uncommon)
def loadObjectReferenceCollectionFromObjectStream_MCDDbSpecialDataGroupImplRef(stream):
    obj = []
    
    collection_items = stream.loadNumericType(2)
    for i in range(collection_items):
        item = {}
        item['object_id'] = stream.loadNumericType(4) # asam::database::base::IDbPersistentObject::setDbObjectID
        obj.append(item)
    
    return obj
