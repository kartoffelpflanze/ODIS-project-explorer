from common_utils import common_loaders


def load(stream):
    obj = {}
    
    obj['vehicle_information_refs'] = common_loaders.loadStringToReferenceMap(stream)
    
    counter = stream.loadNumericType(2)
    for i in range(counter):
        raise RuntimeError('Counter not 0')
    
    return obj
