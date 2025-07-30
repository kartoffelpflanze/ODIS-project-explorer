from common_utils import common_loaders
from common_utils import enum_converters
from object_loaders import MCD_DB_DIAG_COM_PRIMITIVE
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['access_level'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbAccessLevelImpl
    obj['audience_state'] = DbObject.load_object_from_stream_if_exists(stream) # MCDAudienceImpl
    
    obj['repetition_mode'] = enum_converters.get_MCDRepetitionMode(0x6600 + stream.loadNumericType(1))
    
    obj['related_data_primitives'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream, common_loaders.load_DbDiagComObjectReference) # MCDDbDiagComObjectReferences : DbDiagComObjectReference, MCDDbDataPrimitives, MCDDbDataPrimitive, MCDDbDataPrimitiveImpl
    
    status_byte = stream.loadNumericType(1)
    
    obj['disabled_additional_audiences'] = None
    if status_byte & 1:
        obj['disabled_additional_audiences'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    
    obj['enabled_additional_audiences'] = None
    if status_byte & 2:
        obj['enabled_additional_audiences'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    
    if status_byte & 4:
        obj['special_data_group_refs'] = common_loaders.loadObjectReferenceCollectionFromObjectStream_MCDDbSpecialDataGroupImplRef(stream)
    
    obj['diag_com_primitive'] = {'#OBJECT_TYPE': 'MCD_DB_DIAG_COM_PRIMITIVE'}
    obj['diag_com_primitive'].update(MCD_DB_DIAG_COM_PRIMITIVE.load(stream))
    
    return obj
