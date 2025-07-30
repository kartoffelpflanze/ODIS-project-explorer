from common_utils import common_loaders
from object_loaders import MCD_DB_PARAMETER


def load(stream):
    obj = MCD_DB_PARAMETER.load(stream) # super = MCDDbParameterImpl
    
    obj['key_param_short_name'] = stream.loadAsciiString()[0]
    obj['table_ref'] = common_loaders.loadDbAttributedObjectReference(stream) # DbAttributedObjectReference : MCDDbDataRecordImpl
    
    return obj
