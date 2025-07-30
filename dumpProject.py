import argparse
import os
import struct

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.ObjectLoader import ObjectLoader
from classes.StringStorage import StringStorage


# Import the `__all__` list from the "__init__.py" module of the "object_loaders" package as the list of supported Objects to unpack
from object_loaders import __all__ as supported_object_types


# PBL is needed for parsing .key files, which will be done by the PblRecordManager class
# The file "pbl.dll" should be in the working directory, in the "bin" folder
pbl_dll_path = os.path.join(os.path.abspath(os.getcwd()), 'bin/pbl.dll')
pbl_record_manager = PblRecordManager(pbl_dll_path)


# Unpack and dump the contents of a single MCD Project to a folder
### string_storage      = instance of StringStorage, loaded from the target Project
### project_folder_path = Project path (folder with .db and .key files)
### output_folder_path  = path of folder where to write Pool files (dumps of .db files)
### overwrite           = whether or not to unpack and dump a Pool if it already exists (False = skip file)
def app_dumpProject(string_storage, project_folder_path, output_folder_path, overwrite = True):
    # An instance of the ObjectLoader class is used for loading Objects from Pools
    # The first parameter (instance of the PblRecordManager class) is not needed since we will extract the PBL records "manually"
    object_loader = ObjectLoader(None, string_storage)
    
    # Go through each file (Pool) in the Project folder
    for current_filename in os.listdir(project_folder_path):
        # The PoolID simply refers to the file's name (without extension)
        (PoolID, extension) = os.path.splitext(current_filename)
        
        # Only parse .db files
        db_file_path = os.path.join(project_folder_path, current_filename)
        if not os.path.isfile(db_file_path) or extension != '.db':
            continue
        
        # The current Pool will be unpacked into its own file
        # The .c extension is only used for highlighting and block folding in a code editor
        output_pool_path = os.path.join(output_folder_path, PoolID + '.c')
        
        # Only unpack the Pool if the file doesn't already exist (or if overwriting is allowed)
        if overwrite or not os.path.isfile(output_pool_path):
            # Open the output file
            with open(output_pool_path, 'w', encoding='utf-8') as output_pool_file:
                # Determine the Pool's type and write it to the file
                db_file_type = enum_converters.get_db_file_type(PoolID)
                object_printer.print_indented(0, db_file_type, output_pool_file)
                
                # Load all records from the .key file
                # They contain information on how to extract all Objects from the .db file
                pbl_records = pbl_record_manager.get_all_records(project_folder_path, PoolID)
                
                # Open the .db file once for all Objects
                db_file_path = os.path.join(project_folder_path, PoolID + '.db')
                with open(db_file_path, 'rb') as db_file:
                    # Go though each record, to unpack each Object
                    for ObjectID_hash in pbl_records:
                        # Extract the current Object's data from the .db file
                        object_data = ObjectLoader.get_object_data_from_opened_db_file(pbl_records[ObjectID_hash], db_file)
                        
                        # The key of each record in the records dictionary is the hash for an ASCII string
                        # Convert it to the corresponding string (using the strings database), this is the Object's name
                        ObjectID = string_storage.get_ascii_string(ObjectID_hash)
                        if ObjectID is None:
                            raise RuntimeError('ObjectID is invalid')
                        
                        # The first 2 bytes of an Object's data are an enum which represents the Object's type
                        object_type_enum = struct.unpack('<H', object_data[:2])[0]
                        object_type = enum_converters.get_object_type_enum(object_type_enum)
                        
                        # Only attempt to parse known object types
                        if object_type in supported_object_types:
                            # Load the Object
                            # This will either return dictionary (most common), or a list (for Objects with "plural" types)
                            obj = object_loader.load_object_by_object_data(object_data)
                            
                            # Dump the Object to the output file
                            object_printer.print_indented(0, '', output_pool_file)
                            object_printer.print_object(obj, '\'{}\''.format(ObjectID), 0, output_pool_file)
                        
                        # Warn about unknown object types
                        else:
                            print('Unknown object_type: {}'.format(object_type))


# Handle usage as script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump all Objects from all Pools of an MCD Project')
    parser.add_argument('project_folder_path', help='MCD Project (folder containing .db and .key files)')
    parser.add_argument('output_folder_path', help='Main output folder, in which another folder with the name of the Project will be added')
    args = parser.parse_args()
    
    # The project_folder_path argument must be a path to a folder
    if not os.path.isdir(args.project_folder_path):
        raise RuntimeError('Project must be folder')
    
    # Create the main output folder if it doesn't exist
    if not os.path.isdir(args.output_folder_path):
        os.makedirs(args.output_folder_path)
    
    # The Project's name is the name of the "last" folder in the path
    project_name = os.path.basename(args.project_folder_path)
    
    # Each Pool (.db+.key file pair) in the Project will become its own file
    # The file will contain a section for each Object in the Pool
    
    # Create the Project's output folder if it doesn't exist
    project_output_folder_path = os.path.join(args.output_folder_path, project_name)
    if not os.path.isdir(project_output_folder_path):
        os.makedirs(project_output_folder_path)
    
    # Create an instance of the StringStorage class, used for loading the strings database
    # The strings database is unique to each Project
    string_storage = StringStorage(args.project_folder_path)
    
    # Run the app
    app_dumpProject(string_storage, args.project_folder_path, project_output_folder_path)
