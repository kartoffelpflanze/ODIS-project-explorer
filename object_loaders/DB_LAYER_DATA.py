from common_utils import common_loaders
from common_utils import enum_converters
from classes import DbObject


def load(stream):
    obj = {}
    
    obj['layer_id'] = stream.loadAsciiString()[0]
    obj['unk_string'] = stream.loadAsciiString()[0]
    obj['protocol_type'] = stream.loadAsciiString()[0]
    obj['protocol_stack_short_name'] = stream.loadAsciiString()[0]
    obj['com_param_spec_pool_id'] = stream.loadAsciiString()[0]
    
    obj['mcd_location_type'] = enum_converters.get_MCDLocationType(stream.loadEnumMediumRange())
    
    match obj['mcd_location_type']:
        case 'eECU_BASE_VARIANT':
            obj['ecu_base_variant_ref'] = common_loaders.load_reference(stream, False) # DbObjectReference : MCDDbEcuBaseVariantImpl
        case 'eECU_VARIANT':
            obj['ecu_variant_ref'] = common_loaders.load_reference(stream, False) # DbObjectReference : MCDDbEcuVariantImpl
        case 'eFUNCTIONAL_GROUP':
            obj['functional_group_ref'] = common_loaders.load_reference(stream, False) # DbObjectReference : MCDDbFunctionalGroupImpl
    
    obj['diag_com_refs'] = common_loaders.loadStringToReferenceMap(stream, False, True)
    
    obj['dtc_dops'] = common_loaders.loadAsciiStringVectorFromObjectStream(stream)
    
    obj['dop_refs_map'] = common_loaders.loadStringToReferenceMap(stream)
    obj['table_refs_map'] = common_loaders.loadStringToReferenceMap(stream, True)
    obj['request_refs_map'] = common_loaders.loadStringToReferenceMap(stream)
    obj['global_negative_response_refs_map'] = common_loaders.loadStringToReferenceMap(stream)
    obj['functional_class_refs_map'] = common_loaders.loadStringToReferenceMap(stream)
    
    obj['functional_class_data_primitive_refs_map'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        
        item['string'] = stream.loadAsciiString()[0]
        item['map'] = common_loaders.loadStringToReferenceMap(stream, is_DbDiagComObjectReference = True)
        
        obj['functional_class_data_primitive_refs_map'].append(item)
    
    mcd_db_ecu_state_chart_ref_map = common_loaders.loadStringToReferenceMap(stream)
    if len(mcd_db_ecu_state_chart_ref_map) != 0:
        raise RuntimeError('mcd_db_ecu_state_chart_ref_map not 0')
    
    mcd_db_sub_component_ref_map = common_loaders.loadStringToReferenceMap(stream)
    if len(mcd_db_sub_component_ref_map) != 0:
        raise RuntimeError('mcd_db_sub_component_ref_map not 0')
    
    mcd_db_additional_audience_ref_map = common_loaders.loadStringToReferenceMap(stream)
    if len(mcd_db_additional_audience_ref_map) != 0:
        raise RuntimeError('mcd_db_additional_audience_ref_map not 0')
    
    obj['env_data_descs_map'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        item = {}
        
        item['map_key'] = stream.loadAsciiString()[0]
        
        item['env_data_desc'] = DbObject.load_object_from_stream_if_exists(stream) # MCDDbEnvDataDescImpl
        
        obj['env_data_descs_map'].append(item)
    
    obj['parent_layers_vector'] = common_loaders.loadAsciiStringVectorFromObjectStream(stream)
    obj['shared_data_parent_layers_vector'] = common_loaders.loadAsciiStringVectorFromObjectStream(stream)
    
    obj['not_inherited_dops_map'] = common_loaders.loadStringVectorMapFromObjectStream(stream)
    obj['unk_map1'] = common_loaders.loadStringVectorMapFromObjectStream(stream)
    obj['unk_map2'] = common_loaders.loadStringVectorMapFromObjectStream(stream)
    obj['not_inherited_glob_neg_responses_map'] = common_loaders.loadStringVectorMapFromObjectStream(stream)
    
    obj['unit_group_refs_map'] = common_loaders.loadStringToReferenceMap(stream)
    obj['unit_refs_map'] = common_loaders.loadStringToReferenceMap(stream)
    
    obj['protocol_parameters'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        obj['protocol_parameters'].append(DbObject.load_object_from_stream_if_exists(stream))
    
    stream.loadOneByteType()
    
    #obj['special_data_group_refs'] = None
    if stream.loadOneByteType():
        raise RuntimeError('special_data_group_refs not 0')
    
    db_diag_com_object_ref_map = common_loaders.loadStringToReferenceMap(stream)
    if len(db_diag_com_object_ref_map) != 0:
        raise RuntimeError('db_diag_com_object_ref_map not 0')
    
    return obj
