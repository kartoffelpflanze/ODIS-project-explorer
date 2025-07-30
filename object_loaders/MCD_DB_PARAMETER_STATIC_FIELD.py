from object_loaders import DB_DOP_FIELD


def load(stream):
    obj = DB_DOP_FIELD.load(stream) # super = DbDopField
    
    obj['fixed_number_of_items'] = stream.loadNumericType(4)
    obj['item_byte_size'] = stream.loadNumericType(4)
    
    return obj
