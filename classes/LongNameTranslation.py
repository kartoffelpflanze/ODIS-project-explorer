import jpype
import jpype.imports
from jpype.types import *
import os


class LongNameTranslation:
    def __init__(self, hsqldb_1_8_0_jar_path = None, didb_db_folder_path = None, language = None):
        self.__translations = {}
        if hsqldb_1_8_0_jar_path is None or didb_db_folder_path is None or language is None:
            return
        
        # Start the JVM
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[hsqldb_1_8_0_jar_path])
        
        
        # The DriverManager needs the JVM to be started beforehand
        from java.sql import DriverManager
        
        # Register the JDBC driver
        jpype.JClass('java.lang.Class').forName('org.hsqldb.jdbcDriver')
        
        # The name of the database contains the language, e.g. 'didb_Base-en_US'
        db_path = os.path.join(didb_db_folder_path, 'didb_Base-{}'.format(language))
        
        # JDBC URL
        url = 'jdbc:hsqldb:file:{};shutdown=true'.format(db_path)
        
        # Connect to the database
        conn = DriverManager.getConnection(url, 'VAUDASISTSUPER', 'ENMGZIRN')
        stmt = conn.createStatement()
        
        # Query all rows from TRANSLATEDTEXT
        rs = stmt.executeQuery('SELECT TEXTID, TEXT FROM TRANSLATEDTEXT')
        
        # Build the dictionary
        while rs.next():
            self.__translations[str(rs.getString('TEXTID'))] = str(rs.getString('TEXT'))
        
        # Clean up
        rs.close()
        stmt.close()
        conn.close()
    
    
    def __del__(self):
        try:
            jpype.shutdownJVM()
        except:
            pass
    
    
    # Get the translation for a LONG-NAME
    ### long_name_id = value that will be searched in the translation database
    ### long_name    = LONG-NAME to use if the provided ID is invalid or doesn't exist in the database
    def get_long_name_translation(self, long_name_id, long_name):
        # If the LONG-NAME-ID is not available, the LONG-NAME will be used, as no translation can be provided
        if long_name_id is None or long_name_id not in self.__translations:
            return long_name
        
        # Something is up with LONG-NAME-ID 'MAS00194'
        # It translates to '---' but is used for many different LONG-NAMEs
        if long_name_id == 'MAS00194':
            return long_name
        
        # Retrieve the translation for the LONG-NAME-ID
        return self.__translations[long_name_id]
