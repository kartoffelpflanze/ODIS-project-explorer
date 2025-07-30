import os
import struct
import zlib

from classes.PBL import PBL


class PblRecordManager:
    # Constructor
    ### dll_path = path to "pbl.dll"
    def __init__(self, dll_path):
        self.__pbl = PBL(dll_path)
    
    
    # Create a dictionary of all records (key-data pairs) from a PBL keyfile
    ### input_folder_path = path to Project folder, containing .db files
    ### PoolID            = name of desired .key file, without extension
    def get_all_records(self, input_folder_path, pool_id):
        # Create an empty dictionary
        records = {}
        
        # Construct the keyfile's path and ensure the file exists
        key_file_path = os.path.join(input_folder_path, pool_id + '.key')
        if not os.path.isfile(key_file_path):
            raise FileNotFoundError('Cannot find key file "{}"'.format(key_file_path))
        
        # Open the keyfile
        key_file = self.__pbl.pblKfOpen(key_file_path)
        if not key_file:
            raise RuntimeError('Cannot open key file "{}"'.format(key_file_path))
        
        # Go to the first record in the keyfile (should not fail)
        pbl_kf_result = self.__pbl.pblKfFirst(key_file)
        
        # Parse each record, until there are no more left
        while pbl_kf_result is not None:
            # Decode the result
            (key, key_length) = pbl_kf_result
            
            # The key is always supposed to be 4 bytes long
            if key_length != 4:
                raise RuntimeError('PBL key length not 4 ({})'.format(key_length))
            
            # Convert the key to a 4-byte unsigned integer
            key = struct.unpack('<L', key)[0]
            
            # Read the data of the current record
            data = self.__pbl.pblKfRead(key_file)
            
            # Add the record to the dictionary (keys must be unique)
            # The key is the 4-byte value, which represents the hash of an Ascii string (ObjectID = Object name)
            # The data is a bytearray describing how to retrieve the Object's data from the .db file
            if key in records:
                raise RuntimeError('Duplicate key in PBL records')
            records[key] = data
            
            # Go to the next record (the result is None if there are no more records left)
            pbl_kf_result = self.__pbl.pblKfNext(key_file)
        
        # Close the file
        self.__pbl.pblKfClose(key_file)
        
        # Return the dictionary
        return records
    
    
    # Extract the 3 fields from the data of a PBL record
    ### data = PBL record data
    @staticmethod
    def parse_pbl_data(data):
        # PBL data is only allowed to be 6/8/32 bytes
        # If the data is 6 bytes long, the sizes are 1 byte each
        # If the data is 8 bytes long, the sizes are 2 bytes each
        # If the data is 12 bytes long, the sizes are 4 bytes each
        if len(data) == 6:
            (file_position, compressed_size, decompressed_size) = struct.unpack('<IBB', data)
        elif len(data) == 8:
            (file_position, compressed_size, decompressed_size) = struct.unpack('<IHH', data)
        elif len(data) == 12:
            (file_position, compressed_size, decompressed_size) = struct.unpack('<III', data)
        else:
            raise RuntimeError('Invalid PBL data length: {}'.format(len(data)))
        
        # Return a tuple with the 3 values
        return (file_position, compressed_size, decompressed_size)
    
    
    # Retrieve the data bytes of an Object from a Pool (.db file)
    ### db_file                = appropriate .db file (representing the desired Pool), opened in 'rb' mode
    ### db_file_position       = first field decoded from the PBL record data
    ### compressed_data_size   = second field decoded from the PBL record data
    ### decompressed_data_size = third field decoded from the PBL record data
    @staticmethod
    def get_object_data(db_file, db_file_position, compressed_data_size, decompressed_data_size):
        # Go to the indicated position in the file
        db_file.seek(db_file_position)
        
        # Read the specified amount of bytes (zlib stream)
        compressed_data = db_file.read(compressed_data_size)
        
        # Decompress the zlib stream
        decompressed_data = bytearray(zlib.decompress(compressed_data))
        
        # Ensure the length of the data matches the info from the PBL record
        if len(decompressed_data) != decompressed_data_size:
            raise RuntimeError('get_object_data: Wrong data length ({} vs {})'.format(len(decompressed_data), decompressed_data_size))
        
        # Return the Object's data bytes as a bytearray
        return decompressed_data
