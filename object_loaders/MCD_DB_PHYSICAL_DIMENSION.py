def load(stream):
    obj = {}
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadUnicodeString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    obj['unique_object_id'] = stream.loadAsciiString()[0]
    obj['long_name_id'] = stream.loadAsciiString()[0]
    
    s6 = stream.loadAsciiString()[0]
    if s6 is not None:
        raise RuntimeError('s6: {}'.format(s6))
    
    obj['length_exponent'] = stream.loadNumericType(4, True)
    obj['mass_exponent'] = stream.loadNumericType(4, True)
    obj['time_exponent'] = stream.loadNumericType(4, True)
    obj['current_exponent'] = stream.loadNumericType(4, True)
    obj['temperature_exponent'] = stream.loadNumericType(4, True)
    obj['molar_amount_exponent'] = stream.loadNumericType(4, True)
    obj['luminous_intensity_exponent'] = stream.loadNumericType(4, True)
    
    return obj
