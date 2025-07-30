from object_loaders import MCD_DB_DIAG_COM_PRIMITIVE


def load(stream):
    obj = MCD_DB_DIAG_COM_PRIMITIVE.load(stream) # super = MCDDbDiagComPrimitiveImpl
    
    obj['service_protocol_parameters'] = []
    counter = stream.loadNumericType(2)
    for i in range(counter):
        obj['service_protocol_parameters'].append(stream.loadAsciiString()[0])
    
    return obj
