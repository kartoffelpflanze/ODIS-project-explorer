from common_utils import enum_converters


def add_field_to_string(key, field, value):
    if key != '':
        key += '.'
    key += '[{}]{}'.format(field, value)
    return key


def load(stream):
    obj = {}
    
    obj['ecu_base_variant'] = stream.loadAsciiString()[0]
    obj['ecu_base_variant_id'] = stream.loadAsciiString()[0]
    obj['ecu_variant'] = stream.loadAsciiString()[0]
    obj['ecu_variant_id'] = stream.loadAsciiString()[0]
    obj['functional_group'] = stream.loadAsciiString()[0]
    obj['multiple_ecu_job'] = stream.loadAsciiString()[0]
    obj['protocol'] = stream.loadAsciiString()[0]
    
    obj['location_type'] = enum_converters.get_location_type_enum(stream.loadEnumMediumRange())
    
    var_id = stream.loadAsciiString()[0]
    if var_id[1] == '.' and var_id[3] == '.' and var_id[5] == '@' and var_id[-3] == '.':
        obj['pool_id'] = var_id
    else:
        obj['layer_data_object_id'] = var_id
    
    string = ''
    if obj['protocol'] is not None:
        string = add_field_to_string(string, 'Protocol', obj['protocol'])
    if obj['functional_group'] is not None:
        string = add_field_to_string(string, 'FunctionalGroup', obj['functional_group'])
    if obj['ecu_base_variant'] is not None:
        string = add_field_to_string(string, 'EcuBaseVariant', obj['ecu_base_variant'])
    if obj['ecu_variant'] is not None:
        string = add_field_to_string(string, 'EcuVariant', obj['ecu_variant'])
    
    #if string_storage.get_ascii_hash(string) is None:
    #    raise RuntimeError('Failed to find AccessKey "{}"'.format(string))
    
    obj['string'] = string
    
    return obj
