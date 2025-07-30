from object_loaders import MCD_DB_PARAMETER


# Strange naming, MCD_DB_PARAMETER is actually loaded instead
def load(stream):
    return MCD_DB_PARAMETER.load(stream)


#def load(stream):
#    obj = {}
#    
#    obj['s1'] = stream.loadUnicodeString()[0]
#    obj['s2'] = stream.loadUnicodeString()[0]
#    obj['s3'] = stream.loadAsciiString()[0]
#    obj['s4'] = stream.loadAsciiString()[0]
#    obj['s5'] = stream.loadAsciiString()[0]
#    obj['s6'] = stream.loadAsciiString()[0]
#    
#    obj['bit_position'] = stream.loadOneByteType()
#    # todo
#    
#    return obj
