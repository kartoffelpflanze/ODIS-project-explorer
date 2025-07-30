from object_loaders import MCD_DB_PARAMETER
from classes import DbObject
from classes.DbStream import DbStream


def load(stream):
    obj = {}
    
    obj['key'] = stream.loadUnicodeString()[0]
    
    obj['audience_state'] = DbObject.load_object_from_stream_if_exists(stream) # MCDAudienceImpl
    
    obj['disabled_additional_audiences'] = None
    if stream.loadOneByteType():
        raise RuntimeError('disabled_additional_audiences present')
    
    obj['enabled_additional_audiences'] = None
    if stream.loadOneByteType():
        raise RuntimeError('enabled_additional_audiences present')
    
    obj['parameter'] = {'#OBJECT_TYPE': 'MCD_DB_PARAMETER'}
    obj['parameter'].update(MCD_DB_PARAMETER.load(stream))
    
    # Following are two "named streams", which I didn't dwell to much on since all projects seem to have the same sequence of bytes
    # I don't really know how to parse them properly
    # The streams may or not be present; one is named 'A' and the other is named 'B':
    # A = isApiExecutable (expected: 01 = True)
    # B = preconStateRefs (expected: 0000 = 0 refs)
    # The stream always ends with 3 bytes (233E00) which shouldn't be parsed, but are included in the 'length'
    match stream.get_length():
        case 20:
            # A and B present (True, 0 refs)
            stream_bytes = stream.read(17)
            if stream_bytes != bytearray.fromhex('233E00 4101 233E01 233C00 420000 233E01'):
                raise RuntimeError('Values of named objects (A and B) not expected: {}'.format(DbStream.bytearray_to_string(stream_bytes)))
        case 11:
            # Only A present (True)
            stream_bytes = stream.read(8)
            if stream_bytes != bytearray.fromhex('233E00 4101 233E01'):
                raise RuntimeError('Values of named objects (A and B) not expected: {}'.format(DbStream.bytearray_to_string(stream_bytes)))
        case _:
            raise RuntimeError('Unexpected length of named objects (A and B): {}'.format(stream.get_length()))
    
    obj['is_api_executable'] = True
    obj['pre_condition_state_refs'] = None
    
    return obj
