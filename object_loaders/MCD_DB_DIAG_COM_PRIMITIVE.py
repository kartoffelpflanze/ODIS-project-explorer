from common_utils import common_loaders
from common_utils import enum_converters


def load(stream):
    obj = {}
    
    obj['id'] = stream.loadAsciiString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    obj['unique_object_id'] = stream.loadAsciiString()[0]
    
    obj['description'] = stream.loadUnicodeString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['short_name'] = stream.loadAsciiString()[0]
    
    if stream.loadOneByteType():
        obj['request_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : MCDDbRequestImpl
    
    obj['positive_response_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    obj['negative_response_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    obj['functional_class_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    
    obj['semantic'] = stream.loadAsciiString()[0]
    
    obj['transmission_mode'] = enum_converters.get_MCDTransmissionMode(stream.loadEnumMediumRange())
    
    obj['is_api_executable'] = bool(stream.loadOneByteType())
    obj['is_no_operataion'] = bool(stream.loadOneByteType())
    
    obj['diagnostic_class'] = stream.loadEnumSmallRange()
    
    # DbNamedObjectReferences - DbSemanticAttributedObjectReference - MCDDbEcuStateTransitionImpl
    obj['ecu_state_transition_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    # maybe wrong handling
    
    # DbNamedObjectReferences - DbSemanticAttributedObjectReference - MCDDbEcuStateImpl
    obj['ecu_state_ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    # maybe wrong handling
    
    obj['has_suppress_positive_response_capability'] = bool(stream.loadOneByteType())
    
    if obj['has_suppress_positive_response_capability']:
        obj['bytefield'] = common_loaders.loadBytefieldFromObjectStream(stream)
        
        obj['has_positive_response_suppression_parameter_short_name_path'] = bool(stream.loadOneByteType())
        if obj['has_positive_response_suppression_parameter_short_name_path']:
            obj['positive_response_suppression_parameter_short_name_path'] = stream.loadAsciiString()[0]
        else:
            obj['positive_response_suppression_parameter_short_name'] = stream.loadAsciiString()[0]
    
    return obj
