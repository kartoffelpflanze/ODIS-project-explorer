from common_utils import common_loaders


def load(stream):
    obj = {}
    
    obj['code_file'] = stream.loadUnicodeString()[0]
    obj['encryption'] = stream.loadUnicodeString()[0]
    obj['syntax'] = stream.loadUnicodeString()[0]
    obj['revision'] = stream.loadUnicodeString()[0]
    obj['entry_point'] = stream.loadUnicodeString()[0]
    
    obj['library_refs'] = common_loaders.loadStringToReferenceMap(stream, False, False, True)
        
    return obj
