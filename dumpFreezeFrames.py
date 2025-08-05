import argparse
import os
import sys
import time
import traceback

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.StringStorage import StringStorage
from classes.ObjectLoader import ObjectLoader

from parseMWB import get_protocol_layer_data_list, get_ecu_variant_map, get_ecu_variant_layer_data, parse_dop


# PBL is needed for parsing .key files, which will be done by the PblRecordManager class
# The file "pbl.dll" should be in the working directory, in the "bin" folder
pbl_dll_path = os.path.join(os.path.abspath(os.getcwd()), 'bin/pbl.dll')
pbl_record_manager = PblRecordManager(pbl_dll_path)


def dump_freezeframes_for_base_variant(object_loader, protocol_layer_data_list, project_folder_path, base_variant_filename, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
    
    # Add the BASE-VARIANT at the front of the map to also get its Freeze Frames
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
        
        # The Freeze Frames will be dumped into a file named like the ECU-VARIANT
        # The .c extension is only used for highlighting and block folding in a code editor
        ecu_variant_output_file_path = os.path.join(base_variant_output_folder_path, 'FF_' + ecu_variant_name + '.c')
        
        # Only dump if the file doesn't already exist (or if overwriting is allowed)
        if not overwrite and (os.path.exists(ecu_variant_output_file_path) and os.path.isfile(ecu_variant_output_file_path)):
            object_printer.print_indented(debug_info_indentation_level + 1, 'Already done, skipping')
        else:
            # If parsing the BASE-VARIANT, its layer data was retrieved previously
            if ecu_variant_name == base_variant_name:
                ecu_variant_layer_data = base_variant_layer_data
            # Otherwise, retrieve the ECU-VARIANT's layer data
            else:
                ecu_variant_layer_data = get_ecu_variant_layer_data(object_loader, project_folder_path, ecu_variant_map[ecu_variant_name])
            
            # Search for the Freeze Frame Multiplexer
            freeze_frame_dop = None
            for dop_ref_entry in ecu_variant_layer_data['dop_refs_map']:
                if dop_ref_entry['map_key'] == 'MUX_DTCExtenDataRecor':
                    freeze_frame_dop = object_loader.load_object_by_reference(project_folder_path, dop_ref_entry['reference'])
                    break
            
            # If it's not found, there is nothing more to do
            if freeze_frame_dop is None:
                object_printer.print_indented(debug_info_indentation_level + 1, 'Has no special Freeze Frames')
                continue
            
            # Create the BASE-VARIANT's output folder if it doesn't exist
            if not os.path.isdir(base_variant_output_folder_path):
                os.makedirs(base_variant_output_folder_path)
            
            # These objects will be used (in this order) for solving references which don't specify a PoolID
            layer_data_objects = [ecu_variant_layer_data, base_variant_layer_data] + protocol_layer_data_list
            
            # The object must be a MUX  
            if freeze_frame_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_MULTIPLEXER':
                raise RuntimeError('Freeze Frame DOP must be MUX, not {}'.format(freeze_frame_dop['#OBJECT_TYPE']))
            
            # The SWITCH-KEY should start at the edge of the first byte
            if freeze_frame_dop['switch_key']['bit_position'] != 0 or freeze_frame_dop['switch_key']['byte_position'] != 0:
                raise RuntimeError('Expected BYTE- and BIT-POSITION of Freeze Frame MUX SWITCH-KEY to be 0, not {} and {}'.format(freeze_frame_dop['switch_key']['bit_position'], freeze_frame_dop['switch_key']['byte_position']))
            
            # The SWITCH-KEY should take 8 bits
            mux_switch_key_dop = object_loader.load_object_by_reference(project_folder_path, freeze_frame_dop['switch_key']['dop_base_ref'])
            if mux_switch_key_dop['diag_coded_type']['bit_length'] != 8:
                raise RuntimeError('Expected Freeze Frame MUX SWITCH-KEY to take 8 bytes, not {}'.format(mux_switch_key_dop['diag_coded_type']['bit_length']))
            
            # Open the output file and dump the Freeze Frames
            with open(ecu_variant_output_file_path, 'w', encoding='utf-8') as ecu_variant_output_file:
                # Go through each CASE of the MUX
                for case in freeze_frame_dop['cases']:
                    # Both CASE limits should be CLOSED
                    if case['lower_limit']['limit_type'] != 'eLIMIT_CLOSED' or case['upper_limit']['limit_type'] != 'eLIMIT_CLOSED':
                        raise RuntimeError('Expected Freeze Frame MUX CASE LOWER- and UPPER-LIMIT types to be closed, not {} and {}'.format(case['lower_limit']['limit_type'] != 'eLIMIT_CLOSED', case['upper_limit']['limit_type'] != 'eLIMIT_CLOSED'))
                    
                    # Load the structure referenced by the CASE
                    mux_case_structure = object_loader.load_object_by_reference(project_folder_path, case['structure_dop_ref'])
                    
                    # Parse the MUX CASE structure
                    parsed_freeze_frame_mux_case_struct = parse_dop(object_loader, layer_data_objects, project_folder_path, mux_case_structure)
                    if parsed_freeze_frame_mux_case_struct['type'] != 'STRUCTURE':
                        raise RuntimeError('Freeze Frame MUX CASE DOP shoud be STRUCTURE, not {}'.format(parsed_freeze_frame_mux_case_struct['type']))
                    
                    # In at least one project, an ECU-VARIANT has the CASE's name and value swapped, so the value appears as a string... just keep it as a string
                    try:
                        lower_limit = int(case['lower_limit']['mcd_value']['value'])
                    except ValueError:
                        lower_limit = case['lower_limit']['mcd_value']['value']
                    try:
                        upper_limit = int(case['upper_limit']['mcd_value']['value'])
                    except ValueError:
                        upper_limit = case['upper_limit']['mcd_value']['value']
                    
                    # This object will be written to the output file
                    obj = {
                        'description': case['description'],
                        'lower_limit': lower_limit,
                        'upper_limit': upper_limit,
                        'data_offset': freeze_frame_dop['byte_position'],
                        'obj': parsed_freeze_frame_mux_case_struct
                    }
                    
                    # Dump to the output file
                    object_printer.print_object(obj, '\'{}\''.format(case['long_name']), 0, ecu_variant_output_file, False)
                    object_printer.print_indented(0, '', ecu_variant_output_file)


def dump_freezeframes_for_all_base_variants_in_project(object_loader, protocol_layer_data, project_folder_path, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
        
        # Dump the Freeze Frames with the other function
        dump_freezeframes_for_base_variant(object_loader, protocol_layer_data, project_folder_path, PoolID, output_folder_path, overwrite, debug_info_indentation_level + 1)


def dump_freezeframes_for_all_base_variants_in_all_projects(project_folder_path, output_folder_path, debug_info_indentation_level = 0):
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
        
        # Dump the Freeze Frames for each ECU-VARIANT in each BASE-VARIANT with the other function
        dump_freezeframes_for_all_base_variants_in_project(object_loader, protocol_layer_data_list, project_path, project_output_folder_path, False, debug_info_indentation_level + 1)


def dumpFreezeFrames_basevariant(project_folder_path, base_variant_filename, output_folder_path):
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
    dump_freezeframes_for_base_variant(object_loader, protocol_layer_data_list, project_folder_path, base_variant_filename, project_output_folder_path, True)


def dumpFreezeFrames_project(project_folder_path, output_folder_path):
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
        dump_freezeframes_for_all_base_variants_in_project(object_loader, protocol_layer_data_list, project_folder_path, project_output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


def dumpFreezeFrames_projects(projects_folder_path, output_folder_path):
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
        dump_freezeframes_for_all_base_variants_in_all_projects(projects_folder_path, output_folder_path)
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
    parser = argparse.ArgumentParser(description='Dump Freeze Frame (DTC extended data) definitions')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # All Freeze Frames from all ECU-VARIANTs in a BASE-VARIANT of a project
    parser_basevariant = subparsers.add_parser('basevariant', help='Dump Freeze Frames for all ECU-VARIANTs in a BASE-VARIANT')
    parser_basevariant.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_basevariant.add_argument('base_variant_filename', help='Filename of BASE-VARIANT (.bv.db file)')
    parser_basevariant.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and BASE-VARIANT')
    parser_basevariant.set_defaults(func=dumpFreezeFrames_basevariant)
    
    # All Freeze Frames from all ECU-VARIANTs in all BASE-VARIANTs of a project
    parser_project = subparsers.add_parser('project', help='Dump Freeze Frames for all ECU-VARIANTs in all BASE-VARIANTs of a project')
    parser_project.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_project.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and each BASE-VARIANT')
    parser_project.set_defaults(func=dumpFreezeFrames_project)
    
    # All Freeze Frames from all ECU-VARIANTs in all BASE-VARIANTs of all projects
    parser_all_projects = subparsers.add_parser('projects', help='Dump Freeze Frames for all ECU-VARIANTs in all BASE-VARIANTs of all projects')
    parser_all_projects.add_argument('projects_folder_path', help='MCD projects (folder containing folders containing .db and .key files)')
    parser_all_projects.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for each project')
    parser_all_projects.set_defaults(func=dumpFreezeFrames_projects)
    
    # Parse the provided arguments and call the appropriate function based on the command
    args = parser.parse_args()
    filtered_args = {k: v for k, v in vars(args).items() if k not in ('func', 'command')}
    args.func(**filtered_args)
