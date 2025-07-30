def load(stream):
    obj = {}
    
    s1 = stream.loadNativeAsciiString()
    s2 = stream.loadNativeAsciiString()
    s3 = stream.loadNativeAsciiString()
    
    if s1 is not None or s2 is not None or s3 is not None:
        raise RuntimeError('Not None: {}, {}, {}'.format(s1, s2, s3))
    
    obj['description'] = stream.loadNativeUnicodeString()
    obj['long_name'] = stream.loadNativeUnicodeString()
    obj['short_name'] = stream.loadNativeAsciiString()
    
    return obj
