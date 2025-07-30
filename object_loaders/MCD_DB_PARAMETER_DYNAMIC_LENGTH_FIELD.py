from common_utils import common_loaders
from object_loaders import DB_DOP_FIELD


def load(stream):
    obj = DB_DOP_FIELD.load(stream) # super = DbDopField
    
    obj['first_item_offset'] = stream.loadNumericType(4)
    
    obj['determine_number_of_items_dop_ref'] = common_loaders.load_reference(stream, False, False) # DbObjectReference : DbDopBase
    
    obj['determine_number_of_items_byte_position'] = stream.loadNumericType(4)
    
    obj['determine_number_of_items_bit_position'] = stream.loadOneByteType()
    
    return obj
