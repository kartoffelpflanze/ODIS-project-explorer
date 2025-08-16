import argparse
import os
import sys
import time
import traceback

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.StringStorage import StringStorage
from classes.ObjectLoader import ObjectLoader

from dumpMWB import get_protocol_layer_data_list, get_ecu_variant_map, get_ecu_variant_layer_data, parse_dop


# PBL is needed for parsing .key files, which will be done by the PblRecordManager class
# The file "pbl.dll" should be in the working directory, in the "bin" folder
pbl_dll_path = os.path.join(os.path.abspath(os.getcwd()), 'bin/pbl.dll')
pbl_record_manager = PblRecordManager(pbl_dll_path)


# Get the table (and its keys) necessary for Coding
def get_coding_keys_and_table(object_loader, layer_data_objects, project_folder_path, ecu_variant_layer_data):
    # Search for the DIAG-COMM reference with name 'DiagnServi_WriteDataByIdentVariaCodinTextu' (might not exist)
    diag_com_ref_WDBI = None
    for diag_com_ref in ecu_variant_layer_data['diag_com_refs']:
        if diag_com_ref['map_key'] == 'DiagnServi_WriteDataByIdentVariaCodinTextu':
            diag_com_ref_WDBI = diag_com_ref
            break
    
    # Return None for ECU-VARIANTs which do not have the Coding service defined
    if diag_com_ref_WDBI is None:
        return None
            
    # Load the DIAG-SERVICE object from its reference
    wdbi_service = object_loader.load_object_by_reference(project_folder_path, diag_com_ref_WDBI['reference']['attrib_obj_ref'])
    
    # Load the request from its reference in the service
    request = object_loader.load_object_by_reference(project_folder_path, wdbi_service['data_primitive']['diag_com_primitive']['request_ref'])
    
    # One parameter will be the table key (DID) and the other one will be the table structure (Coding data)
    data_record_table_key_parameter = None
    data_record_table_struct_parameter = None
    for request_parameter in request['request_parameters']:
        if request_parameter['#OBJECT_TYPE'] == 'MCD_DB_PARAMETER_TABLE_KEY':
            data_record_table_key_parameter = request_parameter
        if request_parameter['#OBJECT_TYPE'] == 'MCD_DB_PARAMETER_TABLESTRUCT':
            data_record_table_struct_parameter = request_parameter
    
    # The request parameters must have been found
    if data_record_table_key_parameter is None:
        raise RuntimeError('Could not find table key request parameter')
    if data_record_table_struct_parameter is None:
        raise RuntimeError('Could not find table struct request parameter')
    
    # In a service 0x2E request, the DID is expected at BYTE-POSITION 1 and the Coding data at BYTE-POSITION 3 (both at byte edge)
    if data_record_table_key_parameter['byte_position'] != 1 or data_record_table_key_parameter['bit_position'] != 0:
        raise RuntimeError('Expected BYTE-POSITION 1 and BIT-POSITION 0 for Coding table key, not {} and {}'.format(data_record_table_key_parameter['byte_position'], data_record_table_key_parameter['bit_position']))
    if data_record_table_struct_parameter['byte_position'] != 3 or data_record_table_struct_parameter['bit_position'] != 0:
        raise RuntimeError('Expected BYTE-POSITION 3 and BIT-POSITION 0 for Coding table struct, not {} and {}'.format(data_record_table_struct_parameter['byte_position'], data_record_table_struct_parameter['bit_position']))
    
    # Parse the table keys and table structure
    parsed_table_keys = parse_dop(object_loader, layer_data_objects, project_folder_path, data_record_table_key_parameter)
    parsed_table_struct = parse_dop(object_loader, layer_data_objects, project_folder_path, data_record_table_struct_parameter)
    
    # Convert the keys to a dictionary where a DID resolves to a LONG-NAME and LONG-NAME-ID
    coding_keys = {x['key_value']: {'long_name': x['long_name'], 'long_name_id': x['long_name_id']} for x in parsed_table_keys['keys']}
    # Convert the structure to a dictionary where a LONG-NAME resolves to a STRUCTURE
    coding_table = {x['long_name']: x for x in parsed_table_struct['table_rows']}
    return (coding_keys, coding_table)


# Resolve a DID to its corresponding Coding (name and table row parameter)
def get_coding_name_and_table_row_parameter_by_did(object_loader, project_folder_path, coding_keys, coding_table, desired_did):
    # coding_keys: keyed by DID, resolves to {long_name, long_name_id}
    coding_long_name_and_id = coding_keys[desired_did]
    coding_long_name = coding_long_name_and_id['long_name']
    coding_long_name_id = coding_long_name_and_id['long_name_id']
    
    # coding_table: keyed by long_name, resolves to parsed row parameter
    # The key for the DID map is the Coding's long name directly
    
    # Return the parameter and its name
    return (coding_long_name, coding_long_name_id, coding_table[coding_long_name])


# Get the important fields of an Coding table row parameter
def parse_coding_table_row_parameter(coding_table_row_parameter):
    # Some sanity checks...
    if coding_table_row_parameter['default_value'] is not None:
        raise RuntimeError('Table row parameter has default')
    if coding_table_row_parameter['parameter_type'] != 'VALUE':
        raise RuntimeError('Wrong parameter type for table row parameter: {}'.format(coding_table_row_parameter['parameter_type']))
    # Return the important fields
    return (coding_table_row_parameter['long_name'], coding_table_row_parameter['description'], coding_table_row_parameter['byte_position'], coding_table_row_parameter['bit_position'])


# Get the structure referenced by an Coding table row parameter
def get_coding_structure(object_loader, project_folder_path, coding_table_row_parameter):
    if coding_table_row_parameter['dop']['type'] != 'STRUCTURE':
        raise RuntimeError('Wrong data type for parameter structure: {}'.format(coding_table_row_parameter['dop']['type']))
    return coding_table_row_parameter['dop']


def dump_codings_for_base_variant(object_loader, protocol_layer_data_list, project_folder_path, base_variant_filename, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
    # The PoolID simply refers to the file's name (without extension)
    pool_id = base_variant_filename
    if base_variant_filename.endswith('.db'):
        pool_id = base_variant_filename[:-3]
    
    # Only parse a .bv.db file
    if enum_converters.get_db_file_type(pool_id) != 'Base Variant':
        raise RuntimeError('A BASE-VARIANT database must be provided (.bv.db)')
    
    # Load the Object with ID '#RtGen_DB_PROJECT_DATA', which contains info about the ECU-VARIANTs included in the BASE-VARIANT
    db_project_data = object_loader.load_object_by_id(project_folder_path, pool_id, '#RtGen_DB_PROJECT_DATA')
    
    # At least one ECU-VARIANT should exist
    ecu_variant_map = get_ecu_variant_map(db_project_data)
    if ecu_variant_map is None:
        object_printer.print_indented(debug_info_indentation_level, 'Has no ECU-VARIANTs')
    
    # Get the BASE-VARIANT's name from the "project data" (could get from filename too)
    base_variant_name = db_project_data['ecu_base_variant_ref']['object_id']
    
    # The output folder will be named like the BASE-VARIANT
    base_variant_output_folder_path = os.path.join(output_folder_path, base_variant_name)
    
    # Load the layer data for the BASE-VARIANT, which is contained in the current file
    base_variant_layer_data = object_loader.load_object_by_id(project_folder_path, pool_id, '#RtGen_DB_LAYER_DATA')
    
    # Add the BASE-VARIANT at the front of the map to also get its Coding
    if ecu_variant_map is not None:
        original_ecu_variant_map = ecu_variant_map
        ecu_variant_map = {base_variant_name: None}
        ecu_variant_map.update(original_ecu_variant_map)
    else:
        ecu_variant_map = {base_variant_name: None}
    
    # Go through each ECU-VARIANT referenced by the BASE-VARIANT (and the BASE-VARIANT itself)
    for ecu_variant_name in ecu_variant_map:
        if ecu_variant_name == base_variant_name:
            object_printer.print_indented(debug_info_indentation_level, 'BASE-VARIANT {}'.format(ecu_variant_name))
        else:
            object_printer.print_indented(debug_info_indentation_level, 'ECU-VARIANT {}'.format(ecu_variant_name))
        
        # The Coding will be dumped into a file named like the ECU-VARIANT
        # The .c extension is only used for highlighting and block folding in a code editor
        ecu_variant_output_file_path = os.path.join(base_variant_output_folder_path, 'VRC_' + ecu_variant_name + '.c')
        
        # Only dump the Coding if the file doesn't already exist (or if overwriting is allowed)
        if not overwrite and (os.path.exists(ecu_variant_output_file_path) and os.path.isfile(ecu_variant_output_file_path)):
            object_printer.print_indented(debug_info_indentation_level + 1, 'Already done, skipping')
        else:
            # The layer data will be needed for getting a list of all Coding and also for solving some references
            
            # If parsing the BASE-VARIANT, its layer data was retrieved previously
            if ecu_variant_name == base_variant_name:
                ecu_variant_layer_data = base_variant_layer_data
            # Otherwise, retrieve the ECU-VARIANT's layer data
            else:
                ecu_variant_layer_data = get_ecu_variant_layer_data(object_loader, project_folder_path, ecu_variant_map[ecu_variant_name])
    
            # These objects will be used (in this order) for solving references which don't specify a PoolID
            layer_data_objects = [ecu_variant_layer_data, base_variant_layer_data] + protocol_layer_data_list
            
            # Get a map of all available Coding = calibration data
            coding_keys_and_table_result = get_coding_keys_and_table(object_loader, layer_data_objects, project_folder_path, ecu_variant_layer_data)
            
            # Skip ECU-VARIANTs which do not have the Coding service defined (no file will be created)
            if coding_keys_and_table_result is None:
                object_printer.print_indented(debug_info_indentation_level + 1, 'Has no Coding')
                continue
            
            # Unpack the result
            coding_keys, coding_table = coding_keys_and_table_result
            
            # Create the BASE-VARIANT's output folder if it doesn't exist
            if not os.path.isdir(base_variant_output_folder_path):
                os.makedirs(base_variant_output_folder_path)
            
            # Open the output file and dump the Coding
            with open(ecu_variant_output_file_path, 'w', encoding='utf-8') as ecu_variant_output_file:
                for coding_did in coding_keys:
                    # Get the definition for the current DID
                    table_row_result = get_coding_name_and_table_row_parameter_by_did(object_loader, project_folder_path, coding_keys, coding_table, coding_did)
                    if table_row_result is None:
                        raise RuntimeError('Failed to find Coding table row')
                    
                    # Unpack the result
                    coding_long_name, coding_long_name_id, coding_table_row_parameter = table_row_result
                    
                    # Parse the parameter
                    coding_table_row_parameter_long_name, coding_description, coding_byte_position, coding_bit_position = parse_coding_table_row_parameter(coding_table_row_parameter)
                    
                    # Get the object of type 'STRUCTURE'
                    coding_structure = get_coding_structure(object_loader, project_folder_path, coding_table_row_parameter)
                    
                    # Create an object (dictionary) with the fields retrieved from the table row and the parameter structure
                    obj = {
                        'did': coding_did,
                        'long_name': coding_long_name,
                        'long_name_id': coding_long_name_id,
                        'description': coding_description,
                        'byte_position': coding_byte_position,
                        'bit_position': coding_bit_position,
                        'structure': coding_structure
                    }
                    
                    # Dump to the output file
                    object_printer.print_object(obj, '0x{:04X}: {} - {}'.format(coding_did, coding_long_name_id, coding_long_name), 0, ecu_variant_output_file, False)
                    object_printer.print_indented(0, '', ecu_variant_output_file)


def dump_codings_for_all_base_variants_in_project(object_loader, protocol_layer_data, project_folder_path, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
    # Go through each file (Pool) in the project folder
    for current_filename in os.listdir(project_folder_path):
        # The PoolID simply refers to the file's name (without extension)
        (PoolID, extension) = os.path.splitext(current_filename)
        
        # Only parse .db files
        db_file_path = os.path.join(project_folder_path, current_filename)
        if not os.path.isfile(db_file_path) or extension != '.db':
            continue
        
        # Only parse .bv.db files
        if enum_converters.get_db_file_type(PoolID) != 'Base Variant':
            continue
        
        # Display the current BASE-VARIANT being dumped
        object_printer.print_indented(debug_info_indentation_level, 'Dumping {}'.format(PoolID))
        
        # Dump the Coding with the other function
        dump_codings_for_base_variant(object_loader, protocol_layer_data, project_folder_path, PoolID, output_folder_path, overwrite, debug_info_indentation_level + 1)


def dump_codings_for_all_base_variants_in_all_projects(project_folder_path, output_folder_path, debug_info_indentation_level = 0):
    # Go through each project in the folder
    for project_name in os.listdir(project_folder_path):
        project_path = os.path.join(project_folder_path, project_name)
        
        # Only parse folders
        if not os.path.isdir(project_path):
            continue
        
        # Display the current project being unpacked
        object_printer.print_indented(debug_info_indentation_level, 'Unpacking {}'.format(project_name))
        
        # A valid project must contain string databases
        # If an error occurs while trying to load them, the project is invalid
        try:
            # Create an instance of the StringStorage class, used for loading the strings database
            # The strings database is unique to each project
            string_storage = StringStorage(project_path)
        except FileNotFoundError:
            object_printer.print_indented(debug_info_indentation_level + 1, 'Invalid project')
            if project_name == '_META':
                object_printer.print_indented(debug_info_indentation_level + 1, 'Did you accidentally provide a specific project folder instead of the folder with all projects?')
            continue
        
        # An instance of the ObjectLoader class is used for loading Objects and References from the BASE-VARIANT Pool
        # The first parameter (instance of the PblRecordManager class) is needed here since PBL records will be handled "internally"
        object_loader = ObjectLoader(pbl_record_manager, string_storage)
        
        # Some references will only specify the ObjectID (object name) and not the PoolID (file name)
        # To resolve them, there are 3 maps that link an ObjectID with a PoolID: one for the ECU-VARIANT, one for the BASE-VARIANT, and one for the protocol
        # Here, the layer data for the protocol must be loaded, since it's common for all BASE-VARIANTs in a project
        # The rest will be loaded by the other module
        
        # The project must contain the UDS protocol definition
        try:
            protocol_layer_data_list = get_protocol_layer_data_list(object_loader, project_path)
        except FileNotFoundError:
            object_printer.print_indented(debug_info_indentation_level + 1, 'Not UDS project')
            continue
        
        # Create the project output folder if it doesn't exist
        project_output_folder_path = os.path.join(output_folder_path, project_name)
        if not os.path.isdir(project_output_folder_path):
            os.makedirs(project_output_folder_path)
        
        # Dump the Coding for each ECU-VARIANT in each BASE-VARIANT with the other function
        dump_codings_for_all_base_variants_in_project(object_loader, protocol_layer_data_list, project_path, project_output_folder_path, False, debug_info_indentation_level + 1)


def dumpCoding_basevariant(project_folder_path, base_variant_filename, output_folder_path):
    if not os.path.isdir(project_folder_path):
        raise RuntimeError('Project must be folder')
    
    # Create the main output folder if it doesn't exist
    if not os.path.isdir(output_folder_path):
        os.makedirs(output_folder_path)
    
    # The project name is the name of the last folder in the path
    project_name = os.path.basename(project_folder_path)
    
    # Create the project's output folder if it doesn't exist
    project_output_folder_path = os.path.join(output_folder_path, project_name)
    if not os.path.isdir(project_output_folder_path):
        os.makedirs(project_output_folder_path)
    
    # Create an instance of the StringStorage class, used for loading the strings database
    # The strings database is unique to each project
    string_storage = StringStorage(project_folder_path)
    
    # An instance of the ObjectLoader class is used for loading Objects and references from the BASE-VARIANT Pool
    object_loader = ObjectLoader(pbl_record_manager, string_storage)
    
    # Some references will only specify the ObjectID (object name) and not the PoolID (file name)
    # To resolve them, there are 3 maps that link an ObjectID with a PoolID: one for the ECU-VARIANT, one for the BASE-VARIANT, and one for the protocol
    # The ObjectID will be searched in them, in that order
    # The maps are contained in the "layer data" object of each database
    
    # Since the protocol is common for all BASE-VARIANTS, it's better to load it only once for the whole project
    protocol_layer_data_list = get_protocol_layer_data_list(object_loader, project_folder_path)
    
    # Run the app
    dump_codings_for_base_variant(object_loader, protocol_layer_data_list, project_folder_path, base_variant_filename, project_output_folder_path, True)


def dumpCoding_project(project_folder_path, output_folder_path):
    if not os.path.isdir(project_folder_path):
        raise RuntimeError('Project must be folder')
    
    # Create the main output folder if it doesn't exist
    if not os.path.isdir(output_folder_path):
        os.makedirs(output_folder_path)
    
    # The project name is the name of the last folder in the path
    project_name = os.path.basename(project_folder_path)
    
    # Create the project's output folder if it doesn't exist
    project_output_folder_path = os.path.join(output_folder_path, project_name)
    if not os.path.isdir(project_output_folder_path):
        os.makedirs(project_output_folder_path)
    
    # Create an instance of the StringStorage class, used for loading the strings database
    # The strings database is unique to each project
    string_storage = StringStorage(project_folder_path)
    
    # An instance of the ObjectLoader class is used for loading Objects and References from the BASE-VARIANT Pool
    object_loader = ObjectLoader(pbl_record_manager, string_storage)
    
    # Get the starting timestamp
    start_time = time.time()
    
    # The project must contain the UDS protocol definition
    try:
        protocol_layer_data_list = get_protocol_layer_data_list(object_loader, project_folder_path)
    except FileNotFoundError:
        print('    Not UDS project')
        sys.exit()
    
    # Run the app
    # Catch any exceptions, so the elapsed time can be displayed even if an unpacking error occurs
    try:
        dump_codings_for_all_base_variants_in_project(object_loader, protocol_layer_data_list, project_folder_path, project_output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


def dumpCoding_projects(projects_folder_path, output_folder_path):
    if not os.path.isdir(projects_folder_path):
        raise RuntimeError('Must provide folder to all projects')
    
    # Create the main output folder if it doesn't exist
    if not os.path.isdir(output_folder_path):
        os.makedirs(output_folder_path)
    
    # Get the starting timestamp
    start_time = time.time()
    
    # Run the app
    # Catch any exceptions, so the elapsed time can be displayed even if an unpacking error occurs
    try:
        dump_codings_for_all_base_variants_in_all_projects(projects_folder_path, output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


# Handle usage as script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump Coding (calibration data) definitions')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # All Coding from all ECU-VARIANTs in a BASE-VARIANT of a project
    parser_basevariant = subparsers.add_parser('basevariant', help='Dump Coding for all ECU-VARIANTs in a BASE-VARIANT')
    parser_basevariant.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_basevariant.add_argument('base_variant_filename', help='Filename of BASE-VARIANT (.bv.db file)')
    parser_basevariant.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and BASE-VARIANT')
    parser_basevariant.set_defaults(func=dumpCoding_basevariant)
    
    # All Coding from all ECU-VARIANTs in all BASE-VARIANTs of a project
    parser_project = subparsers.add_parser('project', help='Dump Coding for all ECU-VARIANTs in all BASE-VARIANTs of a project')
    parser_project.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_project.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and each BASE-VARIANT')
    parser_project.set_defaults(func=dumpCoding_project)
    
    # All Coding from all ECU-VARIANTs in all BASE-VARIANTs of all projects
    parser_all_projects = subparsers.add_parser('projects', help='Dump Coding for all ECU-VARIANTs in all BASE-VARIANTs of all projects')
    parser_all_projects.add_argument('projects_folder_path', help='MCD projects (folder containing folders containing .db and .key files)')
    parser_all_projects.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for each project')
    parser_all_projects.set_defaults(func=dumpCoding_projects)
    
    # Parse the provided arguments and call the appropriate function based on the command
    args = parser.parse_args()
    filtered_args = {k: v for k, v in vars(args).items() if k not in ('func', 'command')}
    args.func(**filtered_args)
