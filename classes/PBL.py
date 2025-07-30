import os
from ctypes import *


class PBL:
    # Constructor
    ### dll_path = path to "pbl.dll"
    def __init__(self, dll_path):
        # Load the DLL from the given path
        dll = CDLL(dll_path)
        
        # Store references to the necessary functions as private members
        self.__pblKfOpen = dll.pblKfOpen
        self.__pblKfClose = dll.pblKfClose
        self.__pblKfGetAbs = dll.pblKfGetAbs
        self.__pblKfGetRel = dll.pblKfGetRel
        self.__pblKfFind = dll.pblKfFind
        self.__pblKfRead = dll.pblKfRead
        
        # Set the argument and return types for pblKfOpen
        # `pblKeyFile_t *pblKfOpen(char *path, int update, void *filesettag)`
        self.__pblKfOpen.argtypes = [c_char_p, c_int, c_void_p]
        self.__pblKfOpen.restype = c_void_p
        
        # Set the argument and return types for pblKfClose
        # `int pblKfClose(pblKeyFile_t *k)`
        self.__pblKfClose.argtypes = [c_void_p]
        self.__pblKfClose.restype = c_int
        
        # Set the argument and return types for pblKfGetAbs
        # `long pblKfGetAbs(pblKeyFile_t *k, long absindex, void *okey, size_t *okeylen)`
        self.__pblKfGetAbs.argtypes = [c_void_p, c_long, c_void_p, POINTER(c_size_t)]
        self.__pblKfGetAbs.restype = c_long
        
        # Set the argument and return types for pblKfGetRel
        # `long pblKfGetRel(pblKeyFile_t *k, long relindex, void *okey, size_t *okeylen)`
        self.__pblKfGetRel.argtypes = [c_void_p, c_long, c_void_p, POINTER(c_size_t)]
        self.__pblKfGetRel.restype = c_long
        
        # Set the argument and return types for pblKfFind
        # `long pblKfFind(pblKeyFile_t *k, int mode, void *skey, size_t skeylen, void *okey, size_t *okeylen)`
        self.__pblKfFind.argtypes = [c_void_p, c_int, c_void_p, c_size_t, c_void_p, POINTER(c_size_t)]
        self.__pblKfFind.restype = c_long
        
        # Set the argument and return types for pblKfRead
        # `long pblKfRead(pblKeyFile_t *k, void *data, long datalen)`
        self.__pblKfRead.argtypes = [c_void_p, c_void_p, c_long]
        self.__pblKfRead.restype = c_long
    
    
    # Open a keyfile
    def pblKfOpen(self, file_path):
        # Ensure the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
        
        # Open the keyfile
        return self.__pblKfOpen(file_path.encode('ascii'), 0, None)
    
    
    # Close the opened keyfile
    def pblKfClose(self, kf):
        self.__pblKfClose(kf)
    
    
    # Set the current record to the first one (and get its key)
    def pblKfFirst(self, kf, max_key_len = 4):
        # Create objects for pointer parameters
        key_buf = create_string_buffer(max_key_len)
        output_key_length = c_size_t()
        
        # If the return value is positive, return the key as a bytearray and its length
        # Otherwise, return None
        ret = self.__pblKfGetAbs(kf, 0, key_buf, byref(output_key_length))
        return (bytearray(key_buf), output_key_length.value) if ret >= 0 else None
    
    
    # Set the current record to the next one (and get its key)
    def pblKfNext(self, kf, max_key_len = 4):
        # Create objects for pointer parameters
        key_buf = create_string_buffer(max_key_len)
        output_key_length = c_size_t()
        
        # If the return value is positive, return the key as a bytearray and its length
        # Otherwise, return None
        ret = self.__pblKfGetRel(kf, 1, key_buf, byref(output_key_length))
        return (bytearray(key_buf), output_key_length.value) if ret >= 0 else None
    
    
    # Set the current record to the one which has the provided key
    def pblKfFind(self, kf, key):
        # The key must be provided as bytes/bytearray
        if type(key) is not bytes:
            raise TypeError('pblKfFind: key must be bytes, not {}'.format(type(key)))
        
        # The return value is the length of the record's data, just convert it to boolean
        ret = self.__pblKfFind(kf, 1, key, len(key), None, None)
        return (ret >= 0)
    
    
    # Get the data of the current record
    def pblKfRead(self, kf, max_data_len = 12):
        # Create object for pointer parameter
        data_buf = create_string_buffer(max_data_len)
        
        # Read the current record's data
        data_len = self.__pblKfRead(kf, data_buf, max_data_len)
        if data_len < 0:
            raise RuntimeError('pblKfRead: fail ({})'.format(data_len))
        
        # Return the data as a bytearray of actual size
        return data_buf.raw[:data_len]
