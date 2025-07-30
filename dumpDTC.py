import argparse
import os
import sys
import time
import traceback

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.StringStorage import StringStorage
from classes.ObjectLoader import ObjectLoader
from classes.LongNameTranslation import LongNameTranslation

from dumpMWB import get_ecu_variant_map, get_ecu_variant_layer_data, get_protocol_layer_data_list


# PBL is needed for parsing .key files, which will be done by the PblRecordManager class
# The file "pbl.dll" should be in the working directory, in the "bin" folder
pbl_dll_path = os.path.join(os.path.abspath(os.getcwd()), 'bin/pbl.dll')
pbl_record_manager = PblRecordManager(pbl_dll_path)


def dump_dtcs_for_base_variant(object_loader, long_name_translation, project_folder_path, base_variant_filename, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
    
    # Add the BASE-VARIANT at the front of the map to also get its MWBs
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
        
        # If parsing the BASE-VARIANT, its layer data was retrieved previously
        if ecu_variant_name == base_variant_name:
            ecu_variant_layer_data = base_variant_layer_data
        # Otherwise, retrieve the ECU-VARIANT's layer data
        else:
            ecu_variant_layer_data = get_ecu_variant_layer_data(object_loader, project_folder_path, ecu_variant_map[ecu_variant_name])
        
        # Get all DTC DOP names
        dtc_dops = ecu_variant_layer_data['dtc_dops']
        
        # If there are none, there is nothing left to do
        if len(dtc_dops) == 0:
            object_printer.print_indented(debug_info_indentation_level + 1, 'Has no DTCs')
            continue
            
        # Create the BASE-VARIANT's output folder if it doesn't exist
        if not os.path.isdir(base_variant_output_folder_path):
            os.makedirs(base_variant_output_folder_path)
        
        # Go through each DTC DOP, creating a file for each
        for dtc_dop in dtc_dops:
            # The DTCs will be dumped into a file named like the ECU-VARIANT and DTC DOP
            # The .c extension is only used for highlighting and block folding in a code editor
            ecu_variant_output_file_path = os.path.join(base_variant_output_folder_path, dtc_dop + '_' + ecu_variant_name + '.c')
            
            # Only dump the DTCs if the file doesn't already exist (or if overwriting is allowed)
            if not overwrite and (os.path.exists(ecu_variant_output_file_path) and os.path.isfile(ecu_variant_output_file_path)):
                object_printer.print_indented(debug_info_indentation_level + 1, 'Already done, skipping')
            else:
                # Load the DOP, which is given without PoolID, so will be searched in a reference map
                dummy_reference = {'object_id': dtc_dop, 'pool_id': None}
                dtc_dop = object_loader.load_DOP_by_reference_without_PoolID(project_folder_path, [ecu_variant_layer_data], dummy_reference)
                
                # Add each DTC definition to a list
                dtcs_output_object = []
                for dtc_ref in dtc_dop['diag_trouble_codes_ref_map']:
                    # Load the table row and ensure the key matches
                    trouble_code = dtc_ref['map_key']
                    dtc_object = object_loader.load_object_by_reference(project_folder_path, dtc_ref['reference'])
                    if dtc_object['trouble_code'] != trouble_code:
                        raise RuntimeError('DTC table row key {} does not match map key {}'.format(dtc_object['trouble_code'], trouble_code))
                    
                    # Get the fields of the definition
                    output_object = {}
                    output_object['trouble_code'] = trouble_code
                    output_object['dtc'] = dtc_object['trouble_code_text']
                    output_object['level'] = dtc_object['level']
                    output_object['raw_description'] = dtc_object['description']
                    
                    # The "LONG-NAME" is used as a LONG-NAME-ID to get a more detailed description
                    output_object['translated_description'] = long_name_translation.get_long_name_translation(dtc_object['long_name'], 'No translation database provided')
                    
                    # Add the definition to the list
                    dtcs_output_object.append(output_object)
                
                # Dump to the output file
                with open(ecu_variant_output_file_path, 'w', encoding='utf-8') as ecu_variant_output_file:
                    object_printer.print_object(dtcs_output_object, '', 0, ecu_variant_output_file)


def dump_dtcs_for_all_base_variants_in_project(object_loader, long_name_translation, project_folder_path, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
        
        # Dump the DTCs with the other function
        dump_dtcs_for_base_variant(object_loader, long_name_translation, project_folder_path, PoolID, output_folder_path, overwrite, debug_info_indentation_level + 1)


def dump_dtcs_for_all_base_variants_in_all_projects(long_name_translation, project_folder_path, output_folder_path, debug_info_indentation_level = 0):
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
        object_loader = ObjectLoader(pbl_record_manager, string_storage)
        
        # The project must contain the UDS protocol definition
        try:
            get_protocol_layer_data_list(object_loader, project_path)
        except FileNotFoundError:
            object_printer.print_indented(debug_info_indentation_level + 1, 'Not UDS project')
            continue
        
        # Create the project output folder if it doesn't exist
        project_output_folder_path = os.path.join(output_folder_path, project_name)
        if not os.path.isdir(project_output_folder_path):
            os.makedirs(project_output_folder_path)
        
        # Dump the project's DTCs with the other function
        dump_dtcs_for_all_base_variants_in_project(object_loader, long_name_translation, project_path, project_output_folder_path, False, debug_info_indentation_level + 1)


def dumpDTC_basevariant(project_folder_path, base_variant_filename, output_folder_path, translation_database_folder_path, translation_language):
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
    
    # Initialize the LONG-NAME translation (if the optional arguments are not given, nothing is really done)
    # It will be used for retrieving a more detailed description for DTCs
    # The file "hsqldb.jar" should be in the working directory, in the "bin" folder
    long_name_translation = LongNameTranslation('bin/hsqldb.jar', translation_database_folder_path, translation_language)
    
    # Run the app
    dump_dtcs_for_base_variant(object_loader, long_name_translation, project_folder_path, base_variant_filename, project_output_folder_path, True)


def dumpDTC_project(project_folder_path, output_folder_path, translation_database_folder_path, translation_language):
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
    
    # Initialize the LONG-NAME translation (if the optional arguments are not given, nothing is really done)
    # It will be used for retrieving a more detailed description for DTCs
    # The file "hsqldb.jar" should be in the working directory, in the "bin" folder
    long_name_translation = LongNameTranslation('bin/hsqldb.jar', translation_database_folder_path, translation_language)
    
    # Get the starting timestamp
    start_time = time.time()
    
    # The project must contain the UDS protocol definition
    try:
        get_protocol_layer_data_list(object_loader, project_folder_path)
    except FileNotFoundError:
        print('    Not UDS project')
        sys.exit()
    
    # Run the app
    # Catch any exceptions, so the elapsed time can be displayed even if an unpacking error occurs
    try:
        dump_dtcs_for_all_base_variants_in_project(object_loader, long_name_translation, project_folder_path, project_output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


def dumpDTC_projects(projects_folder_path, output_folder_path, translation_database_folder_path, translation_language):
    if not os.path.isdir(projects_folder_path):
        raise RuntimeError('Must provide folder to all projects')
    
    # Create the main output folder if it doesn't exist
    if not os.path.isdir(output_folder_path):
        os.makedirs(output_folder_path)
    
    # Initialize the LONG-NAME translation (if the optional arguments are not given, nothing is really done)
    # It will be used for retrieving a more detailed description for DTCs
    # The file "hsqldb.jar" should be in the working directory, in the "bin" folder
    long_name_translation = LongNameTranslation('bin/hsqldb.jar', translation_database_folder_path, translation_language)
    
    # Get the starting timestamp
    start_time = time.time()
    
    # Run the app
    # Catch any exceptions, so the elapsed time can be displayed even if an unpacking error occurs
    try:
        dump_dtcs_for_all_base_variants_in_all_projects(long_name_translation, projects_folder_path, output_folder_path)
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
    parser = argparse.ArgumentParser(description='Dump DTC (trouble code) definitions')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # All DTCs from all ECU-VARIANTs in a BASE-VARIANT of a project
    parser_basevariant = subparsers.add_parser('basevariant', help='Dump DTCs for all ECU-VARIANTs in a BASE-VARIANT')
    parser_basevariant.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_basevariant.add_argument('base_variant_filename', help='Filename of BASE-VARIANT (.bv.db file)')
    parser_basevariant.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and BASE-VARIANT')
    parser_basevariant.add_argument('translation_database_folder_path', help='Folder containing the translation database (e.g. ".../DIDB/db")', nargs='?')
    parser_basevariant.add_argument('translation_language', help='Language for translations (e.g. "en_US")', nargs='?')
    parser_basevariant.set_defaults(func=dumpDTC_basevariant)
    
    # All DTCs from all ECU-VARIANTs in all BASE-VARIANTs of a project
    parser_project = subparsers.add_parser('project', help='Dump DTCs for all ECU-VARIANTs in all BASE-VARIANTs of a project')
    parser_project.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_project.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and each BASE-VARIANT')
    parser_project.add_argument('translation_database_folder_path', help='Folder containing the translation database (e.g. ".../DIDB/db")', nargs='?')
    parser_project.add_argument('translation_language', help='Language for translations (e.g. "en_US")', nargs='?')
    parser_project.set_defaults(func=dumpDTC_project)
    
    # All DTCs from all ECU-VARIANTs in all BASE-VARIANTs of all projects
    parser_all_projects = subparsers.add_parser('projects', help='Dump DTCs for all ECU-VARIANTs in all BASE-VARIANTs of all projects')
    parser_all_projects.add_argument('projects_folder_path', help='MCD projects (folder containing folders containing .db and .key files)')
    parser_all_projects.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for each project')
    parser_all_projects.add_argument('translation_database_folder_path', help='Folder containing the translation database (e.g. ".../DIDB/db")', nargs='?')
    parser_all_projects.add_argument('translation_language', help='Language for translations (e.g. "en_US")', nargs='?')
    parser_all_projects.set_defaults(func=dumpDTC_projects)
    
    # Parse the provided arguments and call the appropriate function based on the command
    args = parser.parse_args()
    filtered_args = {k: v for k, v in vars(args).items() if k not in ('func', 'command')}
    args.func(**filtered_args)
