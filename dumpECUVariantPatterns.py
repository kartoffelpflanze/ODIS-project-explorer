import argparse
import os
import sys
import time
import traceback

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.StringStorage import StringStorage
from classes.ObjectLoader import ObjectLoader

from dumpMWB import get_ecu_variant_map, get_protocol_layer_data_list


# PBL is needed for parsing .key files, which will be done by the PblRecordManager class
# The file "pbl.dll" should be in the working directory, in the "bin" folder
pbl_dll_path = os.path.join(os.path.abspath(os.getcwd()), 'bin/pbl.dll')
pbl_record_manager = PblRecordManager(pbl_dll_path)


def dump_patterns_for_base_variant(object_loader, project_folder_path, base_variant_filename, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
    # The PoolID simply refers to the file's name (without extension)
    pool_id = base_variant_filename
    if base_variant_filename.endswith('.db'):
        pool_id = base_variant_filename[:-3]
    
    # Only parse a .bv.db file
    if enum_converters.get_db_file_type(pool_id) != 'Base Variant':
        raise RuntimeError('A BASE-VARIANT database must be provided (.bv.db)')
    
    # Load the Object with ID '#RtGen_DB_PROJECT_DATA', which contains info about the ECU-VARIANTs included in the BASE-VARIANT
    db_project_data = object_loader.load_object_by_id(project_folder_path, pool_id, '#RtGen_DB_PROJECT_DATA')
    
    # At least one ECU-VARIANT must exist
    ecu_variant_map = get_ecu_variant_map(db_project_data)
    if ecu_variant_map is None:
        object_printer.print_indented(debug_info_indentation_level, 'Has no ECU-VARIANTs')
        return
    
    # Get the BASE-VARIANT's name from the projectData (could get from filename too)
    base_variant_name = db_project_data['ecu_base_variant_ref']['object_id']
    
    # The output folder will be named like the BASE-VARIANT
    base_variant_output_folder_path = os.path.join(output_folder_path, base_variant_name)
    
    # Load the layer data for the BASE-VARIANT, which is contained in the current file
    base_variant_layer_data = object_loader.load_object_by_id(project_folder_path, pool_id, '#RtGen_DB_LAYER_DATA')
    
    # Go through each ECU-VARIANT referenced by the BASE-VARIANT
    for ecu_variant_name in ecu_variant_map:
        object_printer.print_indented(debug_info_indentation_level, 'ECU-VARIANT {}'.format(ecu_variant_name))
        
        # The patterns will be dumped into a file named like the ECU-VARIANT
        # The .c extension is only used for highlighting and block folding in a code editor
        ecu_variant_output_file_path = os.path.join(base_variant_output_folder_path, 'PAT_' + ecu_variant_name + '.c')
        
        # Only dump the patterns if the file doesn't already exist (or if overwriting is allowed)
        if not overwrite and (os.path.exists(ecu_variant_output_file_path) and os.path.isfile(ecu_variant_output_file_path)):
            object_printer.print_indented(debug_info_indentation_level + 1, 'Already done, skipping')
        else:
            # Load the ECU-VARIANT object by its reference
            ecu_variant = object_loader.load_object_by_reference(project_folder_path, ecu_variant_map[ecu_variant_name])
            
            # The file will contain the ECU-VARIANT's name, description and matching patterns
            output_object = {}
            output_object['name'] = ecu_variant['ecu']['long_name']
            output_object['description'] = ecu_variant['ecu']['description']
            output_object['matching_patterns'] = []
            
            # Go through each matching pattern of the ECU-VARIANT
            for matching_pattern in ecu_variant['matching_patterns']:
                # The "matching parameters" are the values requested from the ECU and checked against known constants
                matching_parameters = matching_pattern['matching_parameters']
                
                # Style 1: 2 parameters are used:
                # - the "ODX File Identifier" (DID 0xF19E: ASCII (ISO-8859-1) string with length 3-25 and 0x00 termination, starting with 'EV_')
                # - the "ODX File Version" (DID 0xF1A2: 3/6 character string, out of which only the first 3 characters are used)
                file_identifier = None
                file_version = None
                
                # Style 2: using a subsystem part number (DID 0xF110)
                # It is an ASCII (ISO-8859-1) string with length 0-655535 without termination
                subsystem_part_number = None
                
                # Get the parameters
                for matching_parameter in matching_parameters:
                    match matching_parameter['diag_com_primitive_ref']['attrib_obj_ref']['object_id']:
                        # ODX File Identifier
                        case 'DiagnServi_ReadDataByIdentASAMODXFileIdent':
                            file_identifier = matching_parameter['expected_value_string']
                        
                        # ODX File Version
                        case 'DiagnServi_ReadDataByIdentASAMODXFileVersi':
                            file_version = matching_parameter['expected_value_string']
                        
                        # Subsystem Specific Diagnostic Specification Part Number
                        case 'DS_ReadDataByIdentSubsySpeciDiagnSpeciPartNumbe':
                            subsystem_part_number = matching_parameter['expected_value_string']
                        
                        # These ones are used for KWP2000 ECU-VARIANT selection
                        case 'MB_Identification_Read' | 'DCX_Identification_Read' | 'ActiveDiagnosticInformation_Read':
                            object_printer.print_indented(debug_info_indentation_level + 1, 'Not for UDS')
                            return
                        
                        case _:
                            raise RuntimeError('Unknown matching parameter: {}'.format(matching_parameter['diag_com_primitive_ref']['attrib_obj_ref']['object_id']))
                
                # The pattern object contains the Identifier and Version, if defined
                output_matching_parameters = {
                    'odx_file_identifier': file_identifier,
                    'odx_file_version': file_version,
                    'subsystem_part_number': subsystem_part_number
                }
                
                # Add the matching pattern to the list
                output_object['matching_patterns'].append(output_matching_parameters)
            
            
            # Create the BASE-VARIANT's output folder if it doesn't exist
            if not os.path.isdir(base_variant_output_folder_path):
                os.makedirs(base_variant_output_folder_path)
            
            # Dump to the output file
            with open(ecu_variant_output_file_path, 'w', encoding='utf-8') as ecu_variant_output_file:
                object_printer.print_object(output_object, '\'{}\''.format(ecu_variant['ecu']['short_name']), 0, ecu_variant_output_file)
                object_printer.print_indented(0, '', ecu_variant_output_file)


def dump_patterns_for_all_base_variants_in_project(object_loader, project_folder_path, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
        
        # Dump the patterns with the other function
        dump_patterns_for_base_variant(object_loader, project_folder_path, PoolID, output_folder_path, overwrite, debug_info_indentation_level + 1)


def dump_patterns_for_all_base_variants_in_all_projects(project_folder_path, output_folder_path, debug_info_indentation_level = 0):
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
        
        # Dump the project's patterns with the other function
        dump_patterns_for_all_base_variants_in_project(object_loader, project_path, project_output_folder_path, False, debug_info_indentation_level + 1)


def dumpECUVariantPatterns_basevariant(project_folder_path, base_variant_filename, output_folder_path):
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
    
    # Run the app
    dump_patterns_for_base_variant(object_loader, project_folder_path, base_variant_filename, project_output_folder_path, True)


def dumpECUVariantPatterns_project(project_folder_path, output_folder_path):
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
        get_protocol_layer_data_list(object_loader, project_folder_path)
    except FileNotFoundError:
        print('    Not UDS project')
        sys.exit()
    
    # Run the app
    # Catch any exceptions, so the elapsed time can be displayed even if an unpacking error occurs
    try:
        dump_patterns_for_all_base_variants_in_project(object_loader, project_folder_path, project_output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


def dumpECUVariantPatterns_projects(projects_folder_path, output_folder_path):
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
        dump_patterns_for_all_base_variants_in_all_projects(projects_folder_path, output_folder_path)
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
    parser = argparse.ArgumentParser(description='Dump ECU-VARIANT matching pattern definitions')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # All matching patterns from all ECU-VARIANTs in a BASE-VARIANT of a project
    parser_basevariant = subparsers.add_parser('basevariant', help='Dump matching patterns for all ECU-VARIANTs in a BASE-VARIANT')
    parser_basevariant.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_basevariant.add_argument('base_variant_filename', help='Filename of BASE-VARIANT (.bv.db file)')
    parser_basevariant.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and BASE-VARIANT')
    parser_basevariant.set_defaults(func=dumpECUVariantPatterns_basevariant)
    
    # All matching patterns from all ECU-VARIANTs in all BASE-VARIANTs of a project
    parser_project = subparsers.add_parser('project', help='Dump matching patterns for all ECU-VARIANTs in all BASE-VARIANTs of a project')
    parser_project.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_project.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and each BASE-VARIANT')
    parser_project.set_defaults(func=dumpECUVariantPatterns_project)
    
    # All matching patterns from all ECU-VARIANTs in all BASE-VARIANTs of all projects
    parser_all_projects = subparsers.add_parser('projects', help='Dump matching patterns for all ECU-VARIANTs in all BASE-VARIANTs of all projects')
    parser_all_projects.add_argument('projects_folder_path', help='MCD projects (folder containing folders containing .db and .key files)')
    parser_all_projects.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for each project')
    parser_all_projects.set_defaults(func=dumpECUVariantPatterns_projects)
    
    # Parse the provided arguments and call the appropriate function based on the command
    args = parser.parse_args()
    filtered_args = {k: v for k, v in vars(args).items() if k not in ('func', 'command')}
    args.func(**filtered_args)
