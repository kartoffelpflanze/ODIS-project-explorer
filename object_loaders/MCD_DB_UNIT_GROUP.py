from common_utils import common_loaders
from common_utils import enum_converters


def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    
    s4 = stream.loadAsciiString()[0]
    if s4 is not None:
        raise RuntimeError('s4: {}'.format(s4))
    s5 = stream.loadAsciiString()[0]
    if s5 is not None:
        raise RuntimeError('s5: {}'.format(s5))
    s6 = stream.loadAsciiString()[0]
    if s6 is not None:
        raise RuntimeError('s6: {}'.format(s6))
    
    obj['category'] = enum_converters.get_MCDUnitGroupCategory(stream.loadEnumMediumRange())
    
    obj['ref_collection'] = common_loaders.loadNamedObjectReferenceCollectionFromObjectStream(stream)
    
    return obj
