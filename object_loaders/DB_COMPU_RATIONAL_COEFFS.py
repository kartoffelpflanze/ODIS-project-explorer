def load(stream):
    obj = {}
    
    obj['numerator'] = []
    counter = stream.loadOneByteType()
    for i in range(counter):
        obj['numerator'].append(stream.loadDoubleType())
    
    obj['denominator'] = []
    counter = stream.loadOneByteType()
    for i in range(counter):
        obj['denominator'].append(stream.loadDoubleType())
    
    return obj
