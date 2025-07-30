import os

from classes.PblRecordManager import PblRecordManager
from classes import DbObject


class ObjectLoader:
    # Split a database reference object into a tuple containing the PoolID and ObjectID which it refers to
    ### reference = dictionary containing keys 'pool_id' and 'object_id'
    @staticmethod
    def decode_object_reference(reference):
        return (reference['pool_id'], reference['object_id'])
    
    
    # Load the Object's data using the provided PBL record data and an already opened .db file
    ### pbl_data = bytearray representing the PBL record data for the desired Object
    ### db_file  = appropriate .db file (representing the desired Pool), opened in 'rb' mode
    @staticmethod
    def get_object_data_from_opened_db_file(pbl_data, db_file):
        # Decode the PBL record data
        (file_position, compressed_size, decompressed_size) = PblRecordManager.parse_pbl_data(pbl_data)
        
        # The data of the PBL record tells how to extract the Object's data bytes from the .db file (position and size)
        
        # Retrieve the Object's data from the .db file (will also decompress it with zlib)
        return PblRecordManager.get_object_data(db_file, file_position, compressed_size, decompressed_size)
    
    
    # Open the appropriate .db file and load the Object's data using the provided PBL record data
    ### pbl_data          = bytearray representing the PBL record data for the desired Object
    ### input_folder_path = path to Project folder, containing .db files
    ### PoolID            = name of desired .db file, without extension
    @staticmethod
    def get_object_data_from_db_file(pbl_data, input_folder_path, PoolID):
        db_file_path = os.path.join(input_folder_path, PoolID + '.db')
        with open(db_file_path, 'rb') as db_file:
            return ObjectLoader.get_object_data_from_opened_db_file(pbl_data, db_file)
    
    
    # Constructor
    ### pbl_record_manager = instance of PblRecordManager class
    ###### this is not necessary for all methods (see method descriptions)
    ### string_storage = instance of StringStorage class, loaded from the current Project
    ###### this is not necessary for all methods (see method descriptions)
    def __init__(self, pbl_record_manager, string_storage):
        self.__pbl_record_manager = pbl_record_manager
        self.__string_storage = string_storage
        
        # PBL records will be stored per instance, for each loaded Pool
        self.__loaded_pbl_records = {}
        
        # Same for DOP references
        self.__dop_cache = {}
    
    
    # Load an Object from its bytearray of data
    ### object_data = bytearray containing Object data
    ### * StringStorage instance needed in constructor
    def load_object_by_object_data(self, object_data):
        if self.__string_storage is None:
            raise RuntimeError('Cannot use method with invalid StringStorage')
        
        return DbObject.load_object(object_data, self.__string_storage)
    
    
    # Load an Object by its PBL data record and PoolID
    ### pbl_data          = bytearray representing the PBL record data for the desired Object
    ### input_folder_path = path to Project folder, containing .db files
    ### PoolID            = name of desired Pool
    ### * StringStorage instance needed in constructor
    def load_object_by_pbl_data(self, pbl_data, input_folder_path, PoolID):
        # Retrieve the Object's data
        object_data = ObjectLoader.get_object_data_from_db_file(pbl_data, input_folder_path, PoolID)
        
        # Load the Object from its data
        return self.load_object_by_object_data(object_data)
    
    
    # Load an Object by its PoolID and ObjectID
    ### input_folder_path = path to Project folder, containing .db files
    ### PoolID            = name of desired Pool
    ### ObjectID          = name of desired Object
    ### * PblRecordManager instance needed in constructor
    ### * StringStorage instance needed in constructor
    def load_object_by_id(self, input_folder_path, PoolID, ObjectID):
        if self.__pbl_record_manager is None:
            raise RuntimeError('Cannot use method with invalid PblRecordManager')
        if self.__string_storage is None:
            raise RuntimeError('Cannot use method with invalid StringStorage')
        
        # If the PBL records for the requested Pool do not exist, load them
        if PoolID not in self.__loaded_pbl_records:
            self.__loaded_pbl_records[PoolID] = self.__pbl_record_manager.get_all_records(input_folder_path, PoolID)
        
        # Convert the given ObjectID string to its hash, which will be used as a key for the PBL record
        ObjectID_hash = self.__string_storage.get_ascii_hash(ObjectID)
        
        # Get the PBL record data belonging to the requested Object, and load it
        pbl_data = self.__loaded_pbl_records[PoolID][ObjectID_hash]
        return self.load_object_by_pbl_data(pbl_data, input_folder_path, PoolID)
    
    
    # Load an Object by a reference
    ### input_folder_path = path to Project folder, containing .db files
    ### reference         = dictionary containing keys 'pool_id' and 'object_id'
    ### * PblRecordManager instance needed in constructor
    ### * StringStorage instance needed in constructor
    def load_object_by_reference(self, input_folder_path, reference):
        # Retrieve the PoolID and ObjectID from the reference and load the Object
        (PoolID, ObjectID) = ObjectLoader.decode_object_reference(reference)
        return self.load_object_by_id(input_folder_path, PoolID, ObjectID)
    
    
    # Load a DOP reference which may be missing the PoolID (file name)
    ### input_folder_path = path to Project folder, containing .db files
    ### layer_data_objects  = list or "layer data" objects
    ### reference           = reference of the DOP to load
    ### * PblRecordManager instance needed in constructor
    ### * StringStorage instance needed in constructor
    def load_DOP_by_reference_without_PoolID(self, input_folder_path, layer_data_objects, reference):
        # Some parameters will not have a PoolID in the DOP reference
        # In this case, the provided ObjectID will be searched in the DOP reference map of the ECU-VARIANT's layer data
        # If it's not there, it will be searched in the DOP reference map of the BASE-VARIANT's layer data
        # If it's not there either, it will be searched in the DOP reference map of the protocol's layer data
        
        # Split the reference into PoolID and ObjectID
        (PoolID, ObjectID) = ObjectLoader.decode_object_reference(reference)
        
        # If the PoolID is provided, use the reference directly
        if PoolID is not None:
            # Load the DOP by the provided reference
            return self.load_object_by_id(input_folder_path, PoolID, ObjectID)
                        
        # Otherwise, search in the map(s)
        else:
            # If the DOP exists in the cache, load it directly
            dop_cache = self.__dop_cache
            if ObjectID in dop_cache:
                return self.load_object_by_id(input_folder_path, dop_cache[ObjectID], ObjectID)
            
            # Search for the item in the map which has the needed ObjectID as the key
            dop_reference = None
            for layer_data_object in layer_data_objects:
                for dop_reference_map_item in layer_data_object['dop_refs_map']:
                    if dop_reference_map_item['map_key'] == ObjectID:
                        dop_reference = dop_reference_map_item['reference']
                        break
                if dop_reference is not None:
                    break
            
            # It must have been found here
            if dop_reference is None:
                raise RuntimeError('Could not find DOP reference: {}'.format(ObjectID))
            
            # Load the DOP by the reference that was found
            return self.load_object_by_reference(input_folder_path, dop_reference)
