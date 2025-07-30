import jpype
import jpype.imports
from jpype.types import *
import argparse
import os
import csv

# The file "hsqldb.jar" should be in the working directory, in the "bin" folder
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=['bin/hsqldb.jar'])

# The DriverManager needs the JVM to be started beforehand
from java.sql import DriverManager

# Register the JDBC driver
jpype.JClass('java.lang.Class').forName('org.hsqldb.jdbcDriver')


def dump_database(db_folder_path, db_name, output_folder_path):
    # Output folder for database
    output_path = os.path.join(output_folder_path, db_name)
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    
    # JDBC URL
    db_path = os.path.join(db_folder_path, db_name)
    url = 'jdbc:hsqldb:file:{};shutdown=true'.format(db_path)
    
    # Connect to the database
    conn = DriverManager.getConnection(url, 'VAUDASISTSUPER', 'ENMGZIRN')
    stmt = conn.createStatement()
    
    # Get tables
    metadata = conn.getMetaData()
    tables = metadata.getTables(None, None, None, ['TABLE'])
    
    # Dump each table
    while tables.next():
        table_name = tables.getString('TABLE_NAME')
        print('   Dumping table: {}'.format(table_name))
        
        # Get all rows for all columns
        rs = stmt.executeQuery('SELECT * FROM "{}"'.format(table_name))
        rsmd = rs.getMetaData()
        
        # Get the number of columns and their names
        col_count = rsmd.getColumnCount()
        col_names = [rsmd.getColumnName(i+1) for i in range(col_count)]
        
        # Dump the table into its own CSV file
        csv_file_path = os.path.join(output_path, '{}.csv'.format(table_name))
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(col_names)
            
            # Write the columns for each row
            while rs.next():
                row = [rs.getString(i+1) for i in range(col_count)]
                writer.writerow(row)
        
        # Cleanup
        rs.close()
    
    # Cleanup
    stmt.close()
    conn.close()


# Handle usage as script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump all tables of an HSQLDB database')
    parser.add_argument('db_folder_path', help='Folder containing .data, .inf, .properties, .script files)')
    parser.add_argument('db_name', help='Database name (without any extension)')
    parser.add_argument('output_folder_path', help='Folder where to dump all tables, in a separate folder for the database')
    args = parser.parse_args()
    
    # Input folder
    if not os.path.isdir(args.db_folder_path):
        raise RuntimeError('Input path must be folder')
    
    # Main output folder
    if not os.path.isdir(args.output_folder_path):
        os.makedirs(args.output_folder_path)
    
    # App
    dump_database(args.db_folder_path, args.db_name, args.output_folder_path)
    
    # Cleanup
    jpype.shutdownJVM()
