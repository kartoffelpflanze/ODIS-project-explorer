import struct
from classes.StringStorage import StringStorage


class DbStream:
    @staticmethod
    def bytearray_to_string(ba):
        return ''.join('{:02X} '.format(x) for x in ba)
    
    
    # Constructor
    ### data           = bytearray object with complete Object data, as read from the .db file and decompressed with zlib
    ### string_storage = instance of StringStorage class, loaded from the current Project
    def __init__(self, data, string_storage):
        # Parameter checking
        if type(data) is not bytearray:
            raise RuntimeError('DbStream needs bytearray, not {}'.format(type(data)))
        if type(string_storage) is not StringStorage:
            raise RuntimeError('DbStream needs StringStorage, not {}'.format(type(string_storage)))
        
        # Private variables
        self.__stream = data
        self.__string_storage = string_storage
        
        # Store the Object's type enum (first 2 bytes)
        self.__stream_object_type = struct.unpack('<H', self.__stream[:2])[0]
    
    
    # Destructor
    def __del__(self):
        # After an Object is fully loaded, its stream must be '#>\0' (3 characters)
        # If more than 3 bytes are present, some data was left unparsed, print this to the console
        if self.get_length() > 3:
            print('Object stream ({:04X}) not empty: {}'.format(self.__stream_object_type, DbStream.bytearray_to_string(self.__stream[:-3])))
    
    
    # Converter to string (returns current stream bytes as formatted string)
    def __str__(self):
        return DbStream.bytearray_to_string(self.__stream)
    
    
    # Getter for amount of bytes remaining in the stream
    def get_length(self):
        return len(self.__stream)
    
    
    # Read an arbitrary amount of bytes, returned as a bytearray
    def read(self, count):
        # Parameter checking
        if count > len(self.__stream):
            raise RuntimeError('Cannot read {} bytes, only have {}'.format(count, len(self.__stream)))
        
        # Read the requested amount of bytes and remove them from the strteam
        data = self.__stream[:count]
        for i in range(count):
            self.__stream.pop(0)
        return data
    
    
    # Load 2 bytes, usually used for enums
    def loadEnumMediumRange(self):
        return struct.unpack('<H', self.read(2))[0]
    
    
    # Load 1 byte, usually used for enums
    def loadEnumSmallRange(self):
        return struct.unpack('<B', self.read(1))[0]
    
    
    # Load 1 byte, usually used for flags and counters
    def loadOneByteType(self):
        return struct.unpack('<B', self.read(1))[0]
    
    
    # Load 1/2/4 bytes, interpreted as (un)signed integer
    def loadNumericType(self, size, signed = False):
        if size == 1:
            return struct.unpack('<B' if not signed else '<b', self.read(size))[0]
        elif size == 2:
            return struct.unpack('<H' if not signed else '<h', self.read(size))[0]
        elif size == 4:
            return struct.unpack('<I' if not signed else '<i', self.read(size))[0]
        else:
            raise RuntimeError('Numeric type can only have size 1/2/4, not {}'.format(size))
    
    
    # Load 8 bytes, interpreted as double
    def loadDoubleType(self):
        return struct.unpack('<d', self.read(8))[0]
    
    
    # Load 4 bytes, interpreted as unsigned integer (string hash), converted to ASCII string
    def loadAsciiString(self):
        string_hash = self.loadNumericType(4)
        string = self.__string_storage.get_ascii_string(string_hash)
        return string, string_hash
    
    
    # Load 4 bytes, interpreted as unsigned integer (string hash), converted to Unicode string
    def loadUnicodeString(self):
        string_hash = self.loadNumericType(4)
        string = self.__string_storage.get_unicode_string(string_hash)
        return string, string_hash
    
    
    # Load variable amount of bytes, interpreted as raw ASCII string (or hash?)
    def loadNativeAsciiString(self):
        hash_or_length = self.loadNumericType(4)
        
        # If the number has the highest bit set, it represents the string's length (amount of bytes following)
        if hash_or_length & 0x80000000:
            # Decode the following bytes as ASCII
            return self.read(hash_or_length & 0x7FFFFFFF).decode('cp1252')
        elif hash_or_length != 0:
            raise RuntimeError('Native string (A) might be hash')
            #return self.__string_storage.get_ascii_string(hash_or_length)
        else:
            return None
    
    
    # Load variable amount of bytes, interpreted as raw Unicode string (or hash?)
    def loadNativeUnicodeString(self):
        hash_or_length = self.loadNumericType(4)
        
        # If the number has the highest bit set, it represents the string's length (amount of pairs of bytes following)
        if hash_or_length & 0x80000000:
            # Decode the following bytes as Unicode
            return self.read(2 * (hash_or_length & 0x7FFFFFFF)).decode('utf-16')
        elif hash_or_length != 0:
            raise RuntimeError('Native string (U) might be hash')
            #return self.__string_storage.get_unicode_string(hash_or_length)
        else:
            return None
