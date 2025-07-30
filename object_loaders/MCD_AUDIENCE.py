def load(stream):
    obj = {}
    
    obj['supplier'] = stream.loadOneByteType()
    obj['development'] = stream.loadOneByteType()
    obj['manufacturing'] = stream.loadOneByteType()
    obj['after_sales'] = stream.loadOneByteType()
    obj['after_market'] = stream.loadOneByteType()
    
    return obj
