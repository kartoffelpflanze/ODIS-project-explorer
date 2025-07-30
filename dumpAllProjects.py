import argparse
import os
import traceback
import time

from classes.StringStorage import StringStorage
from dumpProject import app_dumpProject


# Unpack and dump the contents of all MCD Projects to a folder for each
### project_folder_path = Projects path (folder with folders with .db and .key files)
### output_folder_path  = path of folder where to create Project folder and write Pool files (dumps of .db files)
def app_dumpAllProjects(project_folder_path, output_folder_path):
    # Go through each Project in the folder
    for project_name in os.listdir(project_folder_path):
        project_path = os.path.join(project_folder_path, project_name)
        
        # Only parse folders
        if not os.path.isdir(project_path):
            continue
        
        # A valid Project must contain string databases
        # If an error occurs while trying to load them, the Project is invalid
        try:
            # Create an instance of the StringStorage class, used for loading the strings database
            # The strings database is unique to each Project
            string_storage = StringStorage(project_path)
        except:
            print('    Invalid project')
            if project_name == '_META':
                print('    Did you accidentally provide a specific project folder instead of the folder with all projects?')
            continue
        
        # Create the Project output folder if it doesn't exist
        project_output_folder_path = os.path.join(output_folder_path, project_name)
        if not os.path.isdir(project_output_folder_path):
            os.makedirs(project_output_folder_path)
        
        # Display the current Project being unpacked
        print('Unpacking {}'.format(project_name))
        
        # Dump the Project with the other module
        app_dumpProject(string_storage, project_path, project_output_folder_path, False)


# Handle usage as script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump all Objects from all Pools of all MCD Projects')
    parser.add_argument('projects_folder_path', help='MCD Projects (folder containing folders containing .db and .key files)')
    parser.add_argument('output_folder_path', help='Main output folder, in which other folders with the names of the Projects will be added')
    args = parser.parse_args()
    
    # The projects_folder_path argument must be a path to a folder
    if not os.path.isdir(args.projects_folder_path):
        raise RuntimeError('Must provide folder to all projects')
    
    # Create the main output folder if it doesn't exist
    if not os.path.isdir(args.output_folder_path):
        os.makedirs(args.output_folder_path)
    
    # Get the starting timestamp
    start_time = time.time()
    
    # Run the app
    # Catch any exceptions, so the elapsed time can be displayed even if an unpacking error occurs
    try:
        app_dumpAllProjects(args.projects_folder_path, args.output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))
