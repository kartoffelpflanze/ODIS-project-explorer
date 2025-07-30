# Not actually a class, but whatever


import struct

from common_utils import enum_converters
from classes.DbStream import DbStream

# This imports all loaders defined in the `__all__` list of the file "object_loaders/__init__.py"
# If a new object loader is to be implemented, it must be added there
from object_loaders import *


def load_object_from_stream(stream):
    # The first 2 bytes of an Object's data are an enum which represents the Object's type
    # It will be used for selecting a loader to parse the data
    object_type_enum = stream.loadEnumMediumRange()
    object_type = enum_converters.get_object_type_enum(object_type_enum)
    
    # All loaders were imported by the wildcard import, look for the appropriate loader in the global namespace
    module = globals().get(object_type)
    if module is None:
        raise RuntimeError('Unknown object ({} - {:04X}), cannot load (size {})'.format(object_type, object_type_enum, stream.get_length()))
    
    # Call the `load` method
    obj = module.load(stream)
    
    # An Object will often be loaded as a dictionary
    # If it has a "plural" type, it will be loaded as a list of dictionaries
    # Dictionaries get an "artificial" attribute, with key '#OBJECT_TYPE' (first key)
    ret = obj
    if type(obj) is dict:
        ret = {'#OBJECT_TYPE': object_type}
        ret.update(obj)
    return ret


def load_object_from_stream_if_exists(stream):
    # Load the flag
    object_exists = stream.loadOneByteType()
    
    # The flag is a byte, but it is only allowed to be 0 or 1
    # Other values mean the data was read incorrectly, and the current position didn't really represent such a flag
    if object_exists == 1:
        return load_object_from_stream(stream)
    elif object_exists != 0:
        raise RuntimeError('Invalid object existance flag value ({})'.format(object_exists))
    
    # Return None if the Object isn't present
    return None


def load_object(object_data, string_storage):
    # Construct a DbStream instance from the binary data
    stream = DbStream(object_data, string_storage)
    
    # Load and return the Object
    return load_object_from_stream(stream)
