from common_utils import common_loaders
from object_loaders import DB_DOP_FIELD


def load(stream):
    obj = DB_DOP_FIELD.load(stream) # super = DbDopField
    
    obj['termination_value'] = stream.loadAsciiString()[0]
    
    obj['dop_base_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : DbDopBase
    
    return obj
