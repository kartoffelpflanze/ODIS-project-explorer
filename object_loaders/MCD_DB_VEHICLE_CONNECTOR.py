from common_utils import common_loaders
from classes import DbObject


def load(stream):
    obj = {}
    
    s1 = stream.loadAsciiString()[0]
    s2 = stream.loadAsciiString()[0]
    s3 = stream.loadAsciiString()[0]
    if s1 is not None or s2 is not None or s3 is not None:
        raise RuntimeError('Not None: {}, {}, {}'.format(s1, s2, s3))
    
    obj['description'] = stream.loadUnicodeString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['short_name'] = stream.loadAsciiString()[0]
    
    obj['connector_pins'] = DbObject.load_object_from_stream_if_exists(stream)
    
    return obj
