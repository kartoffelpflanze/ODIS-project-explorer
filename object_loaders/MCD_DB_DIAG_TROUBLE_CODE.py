from common_utils import common_loaders


def load(stream):
    obj = {}
    
    obj['label'] = stream.loadAsciiString()[0]
    
    obj['short_name'] = stream.loadAsciiString()[0]
    obj['long_name'] = stream.loadAsciiString()[0]
    obj['description'] = stream.loadUnicodeString()[0]
    
    obj['level'] = stream.loadNumericType(4)
    
    obj['trouble_code'] = stream.loadNumericType(4)
    
    if stream.loadOneByteType():
        obj['special_data_group_refs'] = common_loaders.loadObjectReferenceCollectionFromObjectStream_MCDDbSpecialDataGroupImplRef(stream)
    
    obj['trouble_code_text'] = stream.loadAsciiString()[0]
    
    return obj
