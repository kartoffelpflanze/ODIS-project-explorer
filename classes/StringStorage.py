import os
import struct
import zlib
import traceback


class StringStorage:
    # Constructor
    ### project_folder_path = path to Project folder, containing .db files
    def __init__(self, project_folder_path):
        # The string database needs 4 files, which are usually stored as gzip-compressed, but can be uncompressed too
        
        # Construct the path for each of the 4 string database files
        ascii_data_file_path = os.path.join(project_folder_path, 'AStringData.data')
        ascii_index_file_path = os.path.join(project_folder_path, 'AStringData.idx')
        unicode_index_file_path = os.path.join(project_folder_path, 'UStringData.idx')
        unicode_data_file_path = os.path.join(project_folder_path, 'UStringData.data')
        
        # If they are not found, they must be in gzip format
        if not os.path.isfile(ascii_data_file_path) or not os.path.isfile(ascii_index_file_path) or not os.path.isfile(unicode_index_file_path) or not os.path.isfile(unicode_data_file_path):
            # Add the extension to the paths
            ascii_data_file_path += '.gz'
            ascii_index_file_path += '.gz'
            unicode_index_file_path += '.gz'
            unicode_data_file_path += '.gz'
            
            # Decompress the files and store their contents in private members
            try:
                with open(ascii_data_file_path, 'rb') as ad, open(ascii_index_file_path, 'rb') as ai, open(unicode_data_file_path, 'rb') as ud, open(unicode_index_file_path, 'rb') as ui:
                    self.__ascii_data_file_contents = zlib.decompress(ad.read(), wbits = 31)
                    self.__ascii_index_file_contents = zlib.decompress(ai.read(), wbits = 31)
                    self.__unicode_data_file_contents = zlib.decompress(ud.read(), wbits = 31)
                    self.__unicode_index_file_contents = zlib.decompress(ui.read(), wbits = 31)
            except FileNotFoundError:
                raise
            except:
                raise RuntimeError('StringStorage: gz file error: {}'.format(traceback.format_exc()))
        
        # If they are found, they are not compressed
        else:
            # Read the files and store their contents in private members
            try:
                with open(ascii_data_file_path, 'rb') as ad, open(ascii_index_file_path, 'rb') as ai, open(unicode_data_file_path, 'rb') as ud, open(unicode_index_file_path, 'rb') as ui:
                    self.__ascii_data_file_contents = ad.read()
                    self.__ascii_index_file_contents = ai.read()
                    self.__unicode_data_file_contents = ud.read()
                    self.__unicode_index_file_contents = ui.read()
            except FileNotFoundError:
                raise
            except:
                raise RuntimeError('StringStorage: non-gz file error: {}'.format(traceback.format_exc()))
        
        # Parse the files' data as text databases (ASCII and Unicode) and store them in private members
        self.__ascii_tdb_dict = self.__read_tdb(self.__ascii_data_file_contents, self.__ascii_index_file_contents, 'A')
        self.__unicode_tdb_dict = self.__read_tdb(self.__unicode_data_file_contents, self.__unicode_index_file_contents, 'U')
    
    
    # Converter to string (returns text databases sizes, ASCII and Unicode, as formatted string)
    def __str__(self):
        return 'A: {}, U: {}'.format(len(self.__ascii_tdb_dict), len(self.__unicode_tdb_dict))
    
    
    # PRIVATE METHODS
    
    
    # Parse a text database from its .idx and .data files
    def __read_tdb(self, data_file_contents, index_file_contents, string_type):
        tdb_dict = {}
        
        # The first 4 bytes in the .idx file represent the amount of strings contained in the database
        string_count = struct.unpack('<I', index_file_contents[:4])[0]
        
        # Get each string
        for i in range(string_count):
            # Each "record" in the .idx file is 8 bytes long, and "records" start from position 4
            index_file_position = 4 + i * 8
            
            # The first 4 bytes represent the current string's position in the .data file
            # The second 4 bytes represent the hash of the current string
            (data_file_position, string_hash) = struct.unpack('<II', index_file_contents[index_file_position : index_file_position+8])
            
            # In the data file, at the indicated position, the first 4 bytes represent the amount of characters in the string that follows
            string_length = struct.unpack('<I', data_file_contents[data_file_position : data_file_position+4])[0]
            
            # Parse the string based on the provided type (all strings in a database are of the same type)
            string_type = string_type.upper()
            if string_type == 'A':
                # ASCII strings use encoding "Windows 1252" and each character is 1 byte
                encoding = 'cp1252'
                character_size = 1
            elif string_type == 'U':
                # Unicode strings use encoding "UTF-16" and each character is 2 bytes
                encoding = 'utf-16'
                character_size = 2
            else:
                return None
            
            # The string's bytes start after the length
            string_position = data_file_position + 4
            
            # Convert the following bytes to a string of the determined encoding
            string_size = string_length * character_size
            string = data_file_contents[string_position : string_position+string_size].decode(encoding)
            
            # Ensure the string's hash is not already present in the dictionary
            if string_hash in tdb_dict:
                raise RuntimeError('Duplicate key ({}) while loading {} strings ("{}")'.format(string_hash, string_type, tdb_dict[string_hash]))
            
            # Store the string in the dictionary, with its hash as the key
            tdb_dict[string_hash] = string
        
        return tdb_dict
    
    
    # Write a text database to new .idx and .data files
    def __write_tdb(self, tdb_dict, output_data_file_path, output_index_file_path, string_type):
        # Open the files
        with open(output_data_file_path, 'wb') as data_file, open(output_index_file_path, 'wb') as index_file:
            # Create empty buffers for the files
            data_file_buffer = bytearray()
            index_file_buffer = bytearray()
            
            # Add each string to the .data file buffer
            string_pointers = []
            for string_hash in tdb_dict:
                # Retrieve the string from the dictionary
                string = tdb_dict[string_hash]
                
                # Store the current .data position, to write in .idx afterwards
                string_pointers.append(len(data_file_buffer))
                
                # Add the string's character count as 4 bytes
                data_file_buffer += struct.pack('<I', len(string))
                
                # Add the string's bytes, depending on encoding
                string_type = string_type.upper()
                if string_type == 'A':
                    data_file_buffer += string.encode('cp1252')
                elif string_type == 'U':
                    data_file_buffer += string.encode('utf-16')[2:] # skip the first 2 bytes = UTF-16 marker
            
            # Add the amount of strings as 4 bytes to the .idx file buffer
            index_file_buffer += struct.pack('<I', len(tdb_dict))
            
            # Add data for each string to the .idx file buffer
            counter = 0
            for string_hash in tdb_dict:
                # Add the string's .data position as 4 bytes
                index_file_buffer += struct.pack('<I', string_pointers[counter])
                counter += 1
                
                # Add the string's hash as 4 bytes
                index_file_buffer += struct.pack('<I', string_hash)
            
            # Compress the file buffers to gzip format and write them to the files
            data_file.write(zlib.compress(data_file_buffer, wbits = 31, level = 1))
            index_file.write(zlib.compress(index_file_buffer, wbits = 31, level = 1))
    
    
    # Get a character from a bytearray at a specified index
    def __get_character_from_bytes(self, string_bytes, character_index, string_type):
        string_type = string_type.upper()
        if string_type == 'A':
            # In ASCII mode, each character takes 1 byte
            return string_bytes[character_index]
        elif string_type == 'U':
            # In Unicode mode, each character takes 2 bytes
            val = struct.unpack('<H', string_bytes[2*character_index : 2*character_index+2])[0]
            return val
        else:
            return None
    
    
    # Get the hash for a string
    # * this only calculates the initial hash, without collision checking (that is done in the public methods)
    def __get_string_hash(self, string, string_type):
        # The hashing algorithm used is DJB2, the result is ANDed with 0x7FFFFFFF
        # If the resulting hash is 0, 5 is used instead
        
        # Convert the given string to bytes
        string_type = string_type.upper()
        if string_type == 'A':
            string_bytes = string.encode('cp1252')
        elif string_type == 'U':
            string_bytes = string.encode('utf-16')[2:] # skip the first 2 bytes = UTF-16 marker
        else:
            return None
        
        # DJB2 algorithm
        string_hash = 5381
        for i in range(len(string)):
            c = self.__get_character_from_bytes(string_bytes, i, string_type)
            string_hash = ((string_hash << 5) + string_hash) + c
        
        # ANDing resulting hash
        string_hash &= 0x7FFFFFFF
        
        # Using 5 if result is 0
        if string_hash == 0:
            string_hash = 5
        
        return string_hash
    
    
    # Add a string to the database
    def __add_string(self, string, string_type):
        string_type = string_type.upper()
        if string_type == 'A':
            tdb_dict = self.__ascii_tdb_dict
            get_string = self.get_ascii_string
        elif string_type == 'U':
            tdb_dict = self.__unicode_tdb_dict
            get_string = self.get_unicode_string
        else:
            return
        
        # Calculate the hash of the provided string
        string_hash = self.__get_string_hash(string, string_type)
        
        # Handle collisions by adding 11 to the hash until an unused key is found (and the key 0 is invalid, 5 is used instead)
        while string_hash in tdb_dict:
            string_hash = (string_hash + 11) & 0x7FFFFFFF
            if string_hash == 0:
                string_hash = 5
        
        # Store the string
        tdb_dict[string_hash] = string
    
    
    # PUBLIC METHODS
    
    
    # Get an ASCII string by providing its hash
    ### string_hash = hash of the desired ASCII string
    def get_ascii_string(self, string_hash):
        string_hash = int(string_hash)
        if string_hash in self.__ascii_tdb_dict:
            return self.__ascii_tdb_dict[string_hash]
        return None
    
    
    # Get a Unicode string by providing its hash
    ### string_hash = hash of the desired Unicode string
    def get_unicode_string(self, string_hash):
        string_hash = int(string_hash)
        if string_hash in self.__unicode_tdb_dict:
            return self.__unicode_tdb_dict[string_hash]
        return None
    
    
    # Get a string by providing its hash
    ### string_hash = hash of the desired string
    # * this will try to retrieve the string as ASCII and as Unicode, and return the one that exists
    def get_string(self, string_hash):
        ascii_string = self.get_ascii_string(string_hash)
        if ascii_string is not None:
            return ascii_string
        return self.get_unicode_string(string_hash)
    
    
    # Get the hash of an ASCII string
    ### string = ASCII string whose hash to compute
    def get_ascii_hash(self, string):
        # Calculate the initial hash using the algorithm
        string_hash = self.__get_string_hash(string, 'A')
        
        # If a string with this hash doesn't exist in the database, return the initial hash
        if self.get_ascii_string(string_hash) is None:
            return string_hash
        
        # If another string has this hash, add 11 until the hash resolves back to the provided string
        while self.get_ascii_string(string_hash) != string:
            string_hash = (string_hash + 11) & 0x7FFFFFFF
            if string_hash == 0:
                string_hash = 5
        return string_hash
    
    
    # Get the hash of a Unicode string
    ### string = Unicode string whose hash to compute
    def get_unicode_hash(self, string):
        # Calculate the initial hash using the algorithm
        string_hash = self.__get_string_hash(string, 'U')
        
        # If a string with this hash doesn't exist in the database, return the initial hash
        if self.get_unicode_string(string_hash) is None:
            return string_hash
        
        # If another string has this hash, add 11 until the hash resolves back to the provided string
        while self.get_unicode_string(string_hash) != string:
            string_hash = (string_hash + 11) & 0x7FFFFFFF
            if string_hash == 0:
                string_hash = 5
        return string_hash
    
    
    # Add an ASCII string to the database
    ### string = ASCII string to add
    def add_string_ascii(self, string):
        self.__add_string(string, 'A')
    
    
    # Add a Unicode string to the database
    ### string = Unicode string to add
    def add_string_unicode(self, string):
        self.__add_string(string, 'U')
    
    
    # Write the ASCII and Unicode text databases to new .idx and .data files
    ### output_folder_path = path to Project folder, where to write files
    def write(self, output_folder_path):
        ascii_data_file_path = os.path.join(output_folder_path, 'AStringData.data.gz')
        ascii_index_file_path = os.path.join(output_folder_path, 'AStringData.idx.gz')
        self.__write_tdb(self.__ascii_tdb_dict, ascii_data_file_path, ascii_index_file_path, 'A')
        
        unicode_data_file_path = os.path.join(output_folder_path, 'UStringData.data.gz')
        unicode_index_file_path = os.path.join(output_folder_path, 'UStringData.idx.gz')
        self.__write_tdb(self.__unicode_tdb_dict, unicode_data_file_path, unicode_index_file_path, 'U')
