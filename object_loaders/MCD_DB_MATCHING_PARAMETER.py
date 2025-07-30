from common_utils import common_loaders


def load(stream):
    obj = {}
    
    obj['diag_com_primitive_ref'] = common_loaders.load_DbDiagComObjectReference(stream)
    
    if stream.loadOneByteType():
        obj['response_parameter_short_name_path'] = stream.loadAsciiString()[0]
    else:
        obj['response_parameter_name'] = stream.loadAsciiString()[0]
    
    obj['expected_value_string'] = stream.loadUnicodeString()[0]
    
    return obj
