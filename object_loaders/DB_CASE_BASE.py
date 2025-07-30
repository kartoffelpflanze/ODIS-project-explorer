from common_utils import common_loaders


def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    
    s4 = stream.loadAsciiString()[0]
    s5 = stream.loadAsciiString()[0]
    s6 = stream.loadAsciiString()[0]
    if s4 is not None or s5 is not None or s6 is not None:
        raise RuntimeError('Not None: "{}", "{}", "{}"'.format(s4, s5, s6))
    
    obj['structure_dop_ref'] = None if not stream.loadOneByteType() else common_loaders.load_reference(stream, False, False) # DbObjectReference : DbDopBase
    
    return obj
