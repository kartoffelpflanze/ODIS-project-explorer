import argparse
import os
import math
from decimal import Decimal, ROUND_HALF_UP

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.ObjectLoader import ObjectLoader
from classes.StringStorage import StringStorage
from classes.LongNameTranslation import LongNameTranslation
from dumpMWB import pbl_record_manager, get_protocol_layer_data_list, get_ecu_variant_map, get_ecu_variant_layer_data, get_mwb_map, get_mwb_table, get_mwb_name_and_table_row_parameter_by_did, get_mwb_structure, parse_dop


# Convert a bytearray to a formatted string (2 HEX digits per byte, separated by spaces)
def bytearray_to_string(ba):
    return ''.join('{:02X} '.format(x) for x in ba)[:-1]


# Calculate how many bytes (from a response) a value needs
def get_byte_length(bit_position, bit_length):
    return math.ceil((bit_position + bit_length) / 8)


# Get the length value for a PARAM of DIAG-CODED-TYPE 'LEADING-LENGTH-INFO-TYPE'
### bit_position             = BIT-POSITION from which to extract the value (0-7)
### bit_length               = how many bits to extract
### endianness               = byte order ('big'/'little')
### dop_response_bytes_slice = bytes extracted starting from the appropriate BYTE-POSITION in the response
def get_leading_length_info_type_length_value(bit_position, bit_length, endianness, dop_response_bytes_slice):
    # Create a DOP that extracts an unsigned integer from the specified position in the response
    dummy_dop = {}
    dummy_dop['diag_coded_type'] = 'STANDARD-LENGTH-TYPE'
    dummy_dop['bit_length'] = bit_length
    dummy_dop['coded_base_data_type'] = 'A_UINT32'
    dummy_dop['encoding'] = 'NONE'
    dummy_dop['endianness'] = endianness
    dummy_dop['bit_mask'] = None
    dummy_dop['physical_base_data_type'] = 'A_UINT32'
    dummy_dop['display_radix'] = 10
    dummy_dop['units'] = None
    dummy_dop['internal_constraint'] = None
    dummy_dop['physical_constraint'] = None
    dummy_dop['calculation_type'] = 'A_UINT32'
    dummy_dop['compu_category'] = 'IDENTICAL'
    
    # The length value is the physical value of the DOP
    return get_dop_value(dummy_dop, dop_response_bytes_slice, bit_position)[1]


# Get the repetition number for a DYNAMIC-LENGTH-FIELD
### determine_number_of_items_dop                      = DOP referenced by the DYNAMIC-LENGTH-FIELD for determining the number of items (repetitions)
### determine_number_of_items_dop_response_bytes_slice = bytes extracted starting from the appropriate BYTE-POSITION in the response
### dop_bit_position                                   = BIT-POSITION from which to extract the value (0-7)
def get_dynamic_length_field_repetition_number(determine_number_of_items_dop, determine_number_of_items_dop_response_bytes_slice, bit_position):
    # Retrieve the physical value of the 'DETERMINE-NUMBER-OF-ITEMS' DOP
    return get_dop_value(determine_number_of_items_dop, determine_number_of_items_dop_response_bytes_slice, bit_position)[1]


# Apply linear interpolation between two points (for COMPU-METHOD 'TAB-INTP')
def linear_interpolation(x1, x2, y1, y2, x):
    return ((y2 - y1) * x + x2 * y1 - x1 * y2) / (x2 - x1)


# Convert response bytes to a value using the definition contained in a DOP
### dop                      = object of type 'DOP'
### dop_response_bytes_slice = bytes extracted starting from the appropriate BYTE-POSITION in the response
### dop_bit_position         = BIT-POSITION from which to extract the value (0-7)
def get_dop_value(dop, dop_response_bytes_slice, dop_bit_position):
    # DATA EXTRACTION: MCD-2D V2.2 - 7.3.6.3
    # In a DOP, data extraction takes place
    # For this, the following attributes are needed:
    #   - BYTE-POSITION and BIT-POSITION specified in the PARAM that contains this DOP
    #   - DIAG-CODED-TYPE
    #   - PHYSICAL-TYPE
    #   - COMPU-METHOD
    
    #print('Initial bytes: {}, BIT-POSITION {}'.format(bytearray_to_string(dop_response_bytes_slice), dop_bit_position))
    
    # a) Determination of the size of the parameter in bits
    # Depending on the actual type of DIAG-CODE-TYPE, the length may be described by another parameter, which shall be extracted before
    # In the case of MIN-MAX-LENGTH-TYPE, it is the net number of bits without the optional termination character
    match dop['diag_coded_type']:
        # For STANDARD-LENGTH-TYPE, the BIT-LENGTH is provided directly
        case 'STANDARD-LENGTH-TYPE':
            dop_bit_length = dop['bit_length']
        
        # For all other types, the size will be determined at runtime based on the response
        
        case 'LEADING-LENGTH-INFO-TYPE':
            # Get the length value; this is how many bytes are used after the length value itself
            dop_byte_length = get_leading_length_info_type_length_value(dop_bit_position, dop['bit_length'], dop['endianness'], dop_response_bytes_slice)
            dop_bit_length = 8 * dop_byte_length
            
            # The content (actual PARAM) starts at the byte edge (BIT-POSITION 0) following the length value
            dop_response_bytes_slice = dop_response_bytes_slice[get_byte_length(dop_bit_position, dop['bit_length']):]
            dop_bit_position = 0
        
        case 'MIN-MAX-LENGTH-TYPE':
            # Determine how many bytes are available for the PARAM
            available_byte_count = len(dop_response_bytes_slice)
            
            # At least 'MIN-LENGTH' bytes must be available
            if available_byte_count < dop['min_length']:
                raise RuntimeError('Need {} bytes for MIN-MAX-LENGTH-TYPE, have {}'.format(dop['min_length'], available_byte_count))
            
            # The TERMINATION value specifies a possible premature end of the PARAM
            match dop['termination']:
                # END-OF-PDU: parsing stops after reaching MAX-LENGTH bytes, or reaching the end of the PDU
                case 'END-OF-PDU':
                    # At least MAX-LENGTH bytes available: PARAM uses MAX-LENGTH bytes
                    if available_byte_count >= dop['max_length']:
                        dop_byte_length = dop['max_length']
                    # Otherwise, PARAM uses all available bytes
                    else:
                        dop_byte_length = available_byte_count
                
                # ZERO: parsing stops after reaching MAX-LENGTH bytes, finding 0x00 (or 0x0000), or reaching the end of the PDU
                case 'ZERO':
                    # For A_UNICODE2STRING, the termination sequence is 0x0000
                    # For all other types which support MIN-MAX-LENGTH-TYPE, it's 0x00
                    if dop['coded_base_data_type'] == 'A_UNICODE2STRING':
                        index_of_termination_in_response = dop_response_bytes_slice.find(bytearray.fromhex('0000'))
                    else:
                        index_of_termination_in_response = dop_response_bytes_slice.find(bytearray.fromhex('00'))
                    
                    # If the termination sequence was found, the bytes before it are used by the PARAM
                    if index_of_termination_in_response != -1:
                        dop_byte_length = index_of_termination_in_response
                    # Otherwise, check for MAX-LENGTH
                    else:
                        # At least MAX-LENGTH bytes available: PARAM uses MAX-LENGTH bytes
                        if available_byte_count >= dop['max_length']:
                            dop_byte_length = dop['max_length']
                        # Otherwise, PARAM uses all available bytes
                        else:
                            dop_byte_length = available_byte_count
                
                # HEX-FF: parsing stops after reaching MAX-LENGTH bytes, finding 0xFF (or 0xFFFF), or reaching the end of the PDU
                case 'HEX-FF':
                    # For A_UNICODE2STRING, the termination sequence is 0xFFFF
                    # For all other types which support MIN-MAX-LENGTH-TYPE, it's 0xFF
                    if dop['coded_base_data_type'] == 'A_UNICODE2STRING':
                        index_of_termination_in_response = dop_response_bytes_slice.find(bytearray.fromhex('FFFF'))
                    else:
                        index_of_termination_in_response = dop_response_bytes_slice.find(bytearray.fromhex('FF'))
                    
                    # If the termination sequence was found, the bytes before it are used by the PARAM
                    if index_of_termination_in_response != -1:
                        dop_byte_length = index_of_termination_in_response
                    # Otherwise, check for MAX-LENGTH
                    else:
                        # At least MAX-LENGTH bytes available: PARAM uses MAX-LENGTH bytes
                        if available_byte_count >= dop['max_length']:
                            dop_byte_length = dop['max_length']
                        # Otherwise, PARAM uses all available bytes
                        else:
                            dop_byte_length = available_byte_count
            
            # Get the BIT-LENGTH from the amount of bytes used
            dop_bit_length = 8 * dop_byte_length
        
        case _:
            raise RuntimeError('Unhandled DIAG-CODED-TYPE: {}'.format(dop['diag_coded_type']))
    
    #print('Size of parameter in bits: {}'.format(dop_bit_length))
    
    # b) Extraction of ByteCount bytes (counting starts from PARAM/BYTE-POSITION)
    dop_byte_count = get_byte_length(dop_bit_position, dop_bit_length)
    
    #print('Extracting {} bytes (from bit {}, {} bits)'.format(dop_byte_count, dop_bit_position, dop_bit_length))
    
    # Ensure the response contains at least the necessary amount of bytes
    if len(dop_response_bytes_slice) < dop_byte_count:
        raise RuntimeError('Not enough response bytes for DOP ({}), need {}'.format(len(dop_response_bytes_slice), dop_byte_count))
    
    # Extract the necessary bytes
    response_bytes = dop_response_bytes_slice[:dop_byte_count]
    
    #print('Extraction of ByteCount ({}) bytes: {}'.format(dop_byte_count, bytearray_to_string(response_bytes)))
    
    # c) Normalization of data: If IS-HIGHLOW-BYTE-ORDER="false" (Intel format), the extracted bytes are to be reversed, so that the byte order corresponds to the Motorola format (HIGHLOW)
    # This step is applied to the extracted bytes as a whole, if the coded type represents a numerical type
    if dop['endianness'] == 'little' and dop['coded_base_data_type'] not in ['A_BYTEFIELD', 'A_ASCIISTRING', 'A_UTF8STRING']:
        # In the case of A_UNICODE2STRING, it is separately applied to each character (pair of bytes)
        if dop['coded_base_data_type'] == 'A_UNICODE2STRING':
            if len(response_bytes) % 2 != 0:
                raise RuntimeError('Unicode string must have even number of bytes')
            
            original_response_bytes = response_bytes
            response_bytes = bytearray()
            for i in range(0, len(original_response_bytes), 2):
                response_bytes += original_response_bytes[i:i+2][::-1]
        else:
            # Reverse the order of the response bytes
            response_bytes = response_bytes[::-1]
        
        #print('Normalization of data: {}'.format(bytearray_to_string(response_bytes)))
    
    # d) Extraction of BIT-LENGTH bits from the normalized byte field starting at PARAM/BIT-POSITION
    
    # The valid value range of BIT-POSITION is 0 to 7
    if dop_bit_position not in range(0, 8):
        raise RuntimeError('BIT-POSITION must be between [0, 7], not {}'.format(dop_bit_position))
    
    # Convert the bytes to a string of bits
    response_bits = ''.join(format(byte, '08b') for byte in response_bytes)
    
    # Bit counting starts with the least significant (right-most) bit of the least significant byte (where BIT-POSITION is 0)
    response_bits = response_bits[::-1][dop_bit_position : dop_bit_position + dop_bit_length][::-1]
    
    #print('Extraction of BIT-LENGTH ({}) bits: {}'.format(dop_bit_length, response_bits))
    
    # e) Application of the BIT-MASK
    extracted_byte_count = (dop_bit_length + 7) // 8
    if dop['diag_coded_type'] == 'STANDARD-LENGTH-TYPE' and dop['bit_mask'] is not None:
        if len(dop['bit_mask']) != extracted_byte_count:
            raise RuntimeError('BIT-MASK should have {} bytes, not {}'.format(extracted_byte_count, len(dop['bit_mask'])))
        
        # Convert the BIT-MASK to a string of bits of the same length as the parameter
        bit_mask_bits = ''.join(format(byte, '08b') for byte in dop['bit_mask'])
        bit_mask_bits = bit_mask_bits[::-1][:dop_bit_length][::-1]
        
        # Perform a logical-AND between the strings of bits
        response_bits = ''.join('1' if x == '1' and y == '1' else '0' for x, y in zip(response_bits, bit_mask_bits))
        
        #print('Application of BIT-MASK: {}'.format(response_bits))
    
    # f) Decode the extracted bit field according to the bit length, the DIAG-CODED-TYPE/BASE-DATA-TYPE and the DIAG-CODED-TYPE/BASE-TYPE-ENCODING,
    # and assign the result to a variable containing the internal value of internal type
    match dop['coded_base_data_type']:
        # Unsigned integer
        case 'A_UINT32':
            if dop_bit_length not in range(1, 32 + 1):
                raise RuntimeError('A_UINT32 needs BIT-LENGTH between [1, 32], not {}'.format(dop_bit_length))
            
            # Parse the unsigned integer depending on its encoding
            match dop['encoding']:
                # NONE: the unsigned integer is encoded as usual
                case 'NONE':
                    internal_value = int(response_bits, 2)
                
                # BCD-P: each 4 bits represent a decimal digit (example: 0x12345678 = 12345678)
                case 'BCD-P':
                    # The BIT-LENGTH must be a multiple of 4
                    if dop_bit_length % 4 != 0:
                        raise RuntimeError('Need multiple of 4 bits for BCD-P, not {}'.format(dop_bit_length))
                    
                    # The number will be retrieved by concatenating to a string
                    bcd_number = ''
                    
                    # Go through each group of 4 bits
                    for i in range(0, dop_bit_length, 4):
                        # Parse the 4 bits as a value
                        bcd_digit = int(response_bits[i : i+4], 2)
                        
                        # Values between 0xA-0xF are forbidden
                        if bcd_digit not in range(0, 10):
                            raise RuntimeError('Invalid BCD digit: {:X}'.format(bcd_digit))
                        
                        # Concatenate the digit
                        bcd_number += str(bcd_digit)
                    
                    # Convert the string to an integer
                    internal_value = int(bcd_number)
                
                case _:
                    raise RuntimeError('Unhandled ENCODING {} for {}'.format(dop['encoding'], dop['coded_base_data_type']))
        
        # Signed integer
        case 'A_INT32':
            if dop_bit_length not in range(1, 32 + 1):
                raise RuntimeError('A_INT32 needs BIT-LENGTH between [1, 32], not {}'.format(dop_bit_length))
            
            # Parse the signed integer depending on its encoding
            match dop['encoding']:
                # Sign magnitude
                case 'SM':
                    internal_value = int(response_bits[1:], 2) if dop_bit_length > 1 else 0
                    if response_bits[0] == '1':
                        internal_value = -internal_value
                
                # One's complement
                case '1C':
                    if response_bits[0] == '0':
                        internal_value = int(response_bits, 2)
                    else:
                        flipped = ''.join('1' if b == '0' else '0' for b in response_bits)
                        internal_value = -int(flipped, 2)
                
                # Two's complement
                case '2C':
                    internal_value = int(response_bits, 2)
                    if response_bits[0] == '1':
                        internal_value -= (1 << dop_bit_length)
                
                case _:
                    raise RuntimeError('Unknown ENCODING {} for {}'.format(dop['encoding'], dop['coded_base_data_type']))
        
        # Single precision floating point
        case 'A_FLOAT32':
            if dop_bit_length != 32:
                raise RuntimeError('A_FLOAT32 needs BIT-LENGTH 32, not {}'.format(dop_bit_length))
            
            # Convert the bits to 4 bytes, then to float
            internal_value = struct.unpack('f', struct.pack('L', int(response_bits, 2)))[0]
        
        # Double precision floating point
        case 'A_FLOAT64':
            if dop_bit_length != 64:
                raise RuntimeError('A_FLOAT64 needs BIT-LENGTH 64, not {}'.format(dop_bit_length))
            
            # Convert the bits to 8 bytes, then to double
            internal_value = struct.unpack('d', struct.pack('Q', int(response_bits, 2)))[0]
        
        # Character array
        case 'A_ASCIISTRING':
            # Parse the string depending on its encoding
            match dop['encoding']:
                # Latin-1
                case 'ISO-8859-1':
                    internal_value = response_bytes.decode('iso-8859-1')
                
                case _:
                    raise RuntimeError('Unknown ENCODING {} for {}'.format(dop['encoding'], dop['coded_base_data_type']))
        
        # Byte array
        case 'A_BYTEFIELD':
            internal_value = response_bytes
        
        case _:
            raise RuntimeError('Unhandled coded BASE-DATA-TYPE {}'.format( dop['coded_base_data_type']))
    
    #print('{} ({}), internal value: {}'.format(dop['coded_base_data_type'], dop['encoding'], internal_value))
    
    # Check the internal value against the INTERNAL-CONSTR, if defined
    if 'internal_constraint' in dop and dop['internal_constraint'] is not None:
        # Ensure the internal value is within the LOWER-LIMIT
        match dop['internal_constraint']['lower_limit']['type']:
            case 'INFINITE':
                pass
            case 'OPEN':
                if internal_value <= dop['internal_constraint']['lower_limit']['value']:
                    raise RuntimeError('Internal value {} is lower than (open) IC lower limit {}'.format(internal_value, dop['internal_constraint']['lower_limit']['value']))
            case 'CLOSED':
                if internal_value < dop['internal_constraint']['lower_limit']['value']:
                    raise RuntimeError('Internal value {} is lower than (closed) IC lower limit {}'.format(internal_value, dop['internal_constraint']['lower_limit']['value']))
        
        # Ensure the internal value is within the UPPER-LIMIT
        match dop['internal_constraint']['upper_limit']['type']:
            case 'INFINITE':
                pass
            case 'OPEN':
                if internal_value >= dop['internal_constraint']['upper_limit']['value']:
                    raise RuntimeError('Internal value {} is higher than (open) IC upper limit {}'.format(internal_value, dop['internal_constraint']['upper_limit']['value']))
            case 'CLOSED':
                if internal_value > dop['internal_constraint']['upper_limit']['value']:
                    raise RuntimeError('Internal value {} is higher than (closed) IC upper limit {}'.format(internal_value, dop['internal_constraint']['upper_limit']['value']))
        
        # Check if the internal value falls inside an invalid SCALE-CONSTR
        if dop['internal_constraint']['scale_constraints'] is not None:
            for scale_constraint in dop['internal_constraint']['scale_constraints']:
                # Check if the value is within the LOWER-LIMIT
                match scale_constraint['lower_limit']['type']:
                    case 'INFINITE':
                        above_lower_limit = True
                    case 'OPEN':
                        above_lower_limit = (internal_value > scale_constraint['lower_limit']['value'])
                    case 'CLOSED':
                        above_lower_limit = (internal_value >= scale_constraint['lower_limit']['value'])
                
                # Check if the value is within the UPPER-LIMIT
                match scale_constraint['upper_limit']['type']:
                    case 'INFINITE':
                        below_upper_limit = True
                    case 'OPEN':
                        below_upper_limit = (internal_value < scale_constraint['upper_limit']['value'])
                    case 'CLOSED':
                        below_upper_limit = (internal_value <= scale_constraint['upper_limit']['value'])
                
                # If the value is in range and the SCALE-CONSTR is not VALID, raise an exception
                if above_lower_limit and below_upper_limit and scale_constraint['validity'] != 'VALID':
                    raise RuntimeError('Internal value {} falls in SCALE-CONSTR with validity {} (Label: {})'.format(internal_value, scale_constraint['validity'], scale_constraint['short_label']))
    
    # g) Computation of the physical value using COMPU-METHOD
    if 'compu_category' not in dop:
        # If not defined (e.g. for CODED-CONST), a COMPU-METHOD of type IDENTICAL is assumed
        physical_value = internal_value
    else:
        match dop['compu_category']:
            # The physical value is the same as the internal value
            case 'IDENTICAL':
                physical_value = internal_value
                
                # For IDENTICAL, the internal and phsyical BASE-DATA-TYPEs should match, but make an exception for strings of different encoding
                if dop['physical_base_data_type'] != dop['coded_base_data_type'] and not ('STRING' in dop['coded_base_data_type'] and 'STRING' in dop['physical_base_data_type']):
                    raise RuntimeError('Physical BASE-DATA-TYPE {} does not match coded BASE-DATA-TYPE {} for IDENTICAL'.format(dop['physical_base_data_type'], dop['coded_base_data_type']))
            
            # LINEAR: The physical value is obtained by applying a linear function to the internal value
            # RAT-FUNC: The physical value is obtained by applying a rational function to the internal value
            # These COMPU-METHODs can be combined because the 'formula' is already parsed as a string that will be evaluated
            case 'LINEAR' | 'RAT-FUNC':
                # Ensure the internal value is within the coded LOWER-LIMIT
                match dop['compu_scale']['coded_lower_limit']['type']:
                    case 'INFINITE':
                        pass
                    case 'OPEN':
                        if internal_value <= dop['compu_scale']['coded_lower_limit']['value']:
                            raise RuntimeError('Internal value {} is lower than (open) scale lower limit {}'.format(internal_value, dop['compu_scale']['coded_lower_limit']['value']))
                    case 'CLOSED':
                        if internal_value < dop['compu_scale']['coded_lower_limit']['value']:
                            raise RuntimeError('Internal value {} is lower than (closed) scale lower limit {}'.format(internal_value, dop['compu_scale']['coded_lower_limit']['value']))
                
                # Ensure the internal value is within the coded UPPER-LIMIT
                match dop['compu_scale']['coded_upper_limit']['type']:
                    case 'INFINITE':
                        pass
                    case 'OPEN':
                        if internal_value >= dop['compu_scale']['coded_upper_limit']['value']:
                            raise RuntimeError('Internal value {} is higher than (open) scale upper limit {}'.format(internal_value, dop['compu_scale']['coded_upper_limit']['value']))
                    case 'CLOSED':
                        if internal_value > dop['compu_scale']['coded_upper_limit']['value']:
                            raise RuntimeError('Internal value {} is higher than (closed) scale upper limit {}'.format(internal_value, dop['compu_scale']['coded_upper_limit']['value']))
                        
                # Apply the linear formula to the internal value
                physical_value = eval(dop['compu_scale']['formula'], {'x': internal_value})
                
                # Apply the calculation type
                match dop['calculation_type']:
                    # Integer
                    case 'A_UINT32' | 'A_INT32':
                        physical_value = int(physical_value)
                    
                    # Floating point
                    case 'A_FLOAT64':
                        physical_value = float(physical_value)
                        
                        # If the calculation type is A_FLOAT64 and a result type is either A_INT32 or A_UINT32, "commercial rounding" is applied
                        if dop['physical_base_data_type'] in ['A_UINT32', 'A_INT32']:
                            physical_value = Decimal(physical_value).to_integral_value(rounding=ROUND_HALF_UP)
                
                # Ensure the physical value is within the physical LOWER-LIMIT
                match dop['compu_scale']['physical_lower_limit']['type']:
                    case 'INFINITE':
                        pass
                    case 'OPEN':
                        if physical_value <= dop['compu_scale']['physical_lower_limit']['value']:
                            raise RuntimeError('Physical value {} is lower than (open) scale lower limit {}'.format(physical_value, dop['compu_scale']['physical_lower_limit']['value']))
                    case 'CLOSED':
                        if physical_value < dop['compu_scale']['physical_lower_limit']['value']:
                            raise RuntimeError('Physical value {} is lower than (closed) scale lower limit {}'.format(physical_value, dop['compu_scale']['physical_lower_limit']['value']))
                
                # Ensure the physical value is within the physical UPPER-LIMIT
                match dop['compu_scale']['physical_upper_limit']['type']:
                    case 'INFINITE':
                        pass
                    case 'OPEN':
                        if physical_value >= dop['compu_scale']['physical_upper_limit']['value']:
                            raise RuntimeError('Physical value {} is higher than (open) scale upper limit {}'.format(physical_value, dop['compu_scale']['physical_upper_limit']['value']))
                    case 'CLOSED':
                        if physical_value > dop['compu_scale']['physical_upper_limit']['value']:
                            raise RuntimeError('Physical value {} is higher than (closed) scale upper limit {}'.format(physical_value, dop['compu_scale']['physical_upper_limit']['value']))
            
            # Same as LINEAR/RAT-FUNC, but a different function can be defined for disjunctive intervals
            case 'SCALE-LINEAR' | 'SCALE-RAT-FUNC':
                # Search the internal value in the intervals of each COMPU-SCALE
                physical_value = None
                for compu_scale in dop['compu_scales']:
                    # Check if the internal value is within the coded LOWER-LIMIT
                    match compu_scale['coded_lower_limit']['type']:
                        case 'INFINITE':
                            above_lower_limit = True
                        case 'OPEN':
                            above_lower_limit = (internal_value > compu_scale['coded_lower_limit']['value'])
                        case 'CLOSED':
                            above_lower_limit = (internal_value >= compu_scale['coded_lower_limit']['value'])
                    
                    # Check if the internal value is within the coded UPPER-LIMIT
                    match compu_scale['coded_upper_limit']['type']:
                        case 'INFINITE':
                            below_upper_limit = True
                        case 'OPEN':
                            below_upper_limit = (internal_value < compu_scale['coded_upper_limit']['value'])
                        case 'CLOSED':
                            below_upper_limit = (internal_value <= compu_scale['coded_upper_limit']['value'])
                    
                    # If the internal value falls within the COMPU-SCALE's interval, use it to calculate the physical value
                    if above_lower_limit and below_upper_limit:
                        # Apply the linear formula to the internal value
                        physical_value = eval(compu_scale['formula'], {'x': internal_value})
                        
                        # Apply the calculation type
                        match dop['calculation_type']:
                            # Integer
                            case 'A_UINT32' | 'A_INT32':
                                physical_value = int(physical_value)
                            
                            # Floating point
                            case 'A_FLOAT64':
                                physical_value = float(physical_value)
                                
                                # If the calculation type is A_FLOAT64 and a result type is either A_INT32 or A_UINT32, "commercial rounding" is applied
                                if dop['physical_base_data_type'] in ['A_UINT32', 'A_INT32']:
                                    physical_value = Decimal(physical_value).to_integral_value(rounding=ROUND_HALF_UP)
                        
                        # Ensure the physical value is within the physical LOWER-LIMIT
                        match compu_scale['physical_lower_limit']['type']:
                            case 'INFINITE':
                                pass
                            case 'OPEN':
                                if physical_value <= compu_scale['physical_lower_limit']['value']:
                                    raise RuntimeError('Physical value {} is lower than (open) scale lower limit {}'.format(physical_value, compu_scale['physical_lower_limit']['value']))
                            case 'CLOSED':
                                if physical_value < compu_scale['physical_lower_limit']['value']:
                                    raise RuntimeError('Physical value {} is lower than (closed) scale lower limit {}'.format(physical_value, compu_scale['physical_lower_limit']['value']))
                        
                        # Ensure the physical value is within the physical UPPER-LIMIT
                        match compu_scale['physical_upper_limit']['type']:
                            case 'INFINITE':
                                pass
                            case 'OPEN':
                                if physical_value >= compu_scale['physical_upper_limit']['value']:
                                    raise RuntimeError('Physical value {} is higher than (open) scale upper limit {}'.format(physical_value, compu_scale['physical_upper_limit']['value']))
                            case 'CLOSED':
                                if physical_value > compu_scale['physical_upper_limit']['value']:
                                    raise RuntimeError('Physical value {} is higher than (closed) scale upper limit {}'.format(physical_value, compu_scale['physical_upper_limit']['value']))
                        
                        # A matching interval was found, stop searching
                        break
                
                # If a matching interval was not found, apply the default value if defined
                if physical_value is None:
                    if dop['compu_default_value'] is not None:
                        # The default value is given as a string
                        match dop['calculation_type']:
                            case 'A_UINT32' | 'A_INT32':
                                physical_value = int(dop['compu_default_value'])
                            case 'A_FLOAT64':
                                physical_value = float(dop['compu_default_value'])
                    else:
                        raise RuntimeError('Internal value {} falls out of all COMPU-SCALEs and no COMPU-DEFAULT-VALUE exists'.format(internal_value))
            
            # The internal value is transformed into a textual expression
            case 'TEXTTABLE':
                # Search the internal value in the intervals of each COMPU-SCALE
                physical_value = None
                for compu_scale in dop['compu_scales']:
                    # If the internal value falls within the range, get the textual expression and stop searching
                    # The LIMITs are always CLOSED
                    if internal_value >= compu_scale['lower_limit'] and internal_value <= compu_scale['upper_limit']:
                        physical_value = long_name_translation.get_long_name_translation(compu_scale['long_name_id'], compu_scale['long_name'])
                        break
                
                # If a matching text was not found, apply the default value if defined
                if physical_value is None:
                    if dop['compu_default_value'] is not None:
                        physical_value = dop['compu_default_value']
                    else:
                        raise RuntimeError('Internal value {} falls out of all COMPU-SCALEs and no COMPU-DEFAULT-VALUE exists'.format(internal_value))
            
            # A set of points is used to convert the internal value to the physical value by linear interpolation
            case 'TAB-INTP':
                # If the internal value is less than the smallest defined LOWER-LIMIT or greater than the greatest LOWER-LIMIT, a runtime error shall be indicated
                if internal_value < dop['compu_scales'][0]['limit']:
                    raise RuntimeError('The internal value is less than the smallest defined LOWER-LIMIT')
                if internal_value > dop['compu_scales'][len(dop['compu_scales']) - 1]['limit']:
                    raise RuntimeError('The internal value is greater than the greatest defined LOWER-LIMIT')
                
                # Search all intervals generated by two adjacent COMPU-SCALEs
                physical_value = None
                for i in range(0, len(dop['compu_scales']) - 1):
                    # Get the two COMPU-SCALEs
                    compu_scale_1 = dop['compu_scales'][i]
                    compu_scale_2 = dop['compu_scales'][i + 1]
                    
                    # Check if the internal value is within the interval defined by them
                    if internal_value >= compu_scale_1['limit'] and internal_value <= compu_scale_2['limit']:
                        # The values used for interpolation (the COMPU-CONSTs) are given as strings
                        # Apply linear interpolation
                        physical_value = linear_interpolation(compu_scale_1['limit'], compu_scale_2['limit'], int(compu_scale_1['compu_const']), int(compu_scale_2['compu_const']), internal_value)
                        break
                
                # An interval must have been found
                if physical_value is None:
                    raise RuntimeError('Failed to find interval for linear interpolation')
                
                # Apply the calculation type
                match dop['calculation_type']:
                    # Integer
                    case 'A_UINT32' | 'A_INT32':
                        physical_value = int(physical_value)
                    
                    # Floating point
                    case 'A_FLOAT64':
                        physical_value = float(physical_value)
            
            case _:
                raise RuntimeError('Unknown computation category {}'.format(dop['compu_category']))
    
    # Check the physical value against the PHYS-CONSTR, if defined
    if 'physical_constraint' in dop and dop['physical_constraint'] is not None:
        # Ensure the physical value is within the LOWER-LIMIT
        match dop['physical_constraint']['lower_limit']['type']:
            case 'INFINITE':
                pass
            case 'OPEN':
                if physical_value <= dop['physical_constraint']['lower_limit']['value']:
                    raise RuntimeError('Physical value {} is lower than (open) PC lower limit {}'.format(physical_value, dop['physical_constraint']['lower_limit']['value']))
            case 'CLOSED':
                if physical_value < dop['physical_constraint']['lower_limit']['value']:
                    raise RuntimeError('Physical value {} is lower than (closed) PC lower limit {}'.format(physical_value, dop['physical_constraint']['lower_limit']['value']))
        
        # Ensure the physical value is within the UPPER-LIMIT
        match dop['physical_constraint']['upper_limit']['type']:
            case 'INFINITE':
                pass
            case 'OPEN':
                if physical_value >= dop['physical_constraint']['upper_limit']['value']:
                    raise RuntimeError('Physical value {} is higher than (open) PC upper limit {}'.format(physical_value, dop['physical_constraint']['upper_limit']['value']))
            case 'CLOSED':
                if physical_value > dop['physical_constraint']['upper_limit']['value']:
                    raise RuntimeError('Physical value {} is higher than (closed) PC upper limit {}'.format(physical_value, dop['physical_constraint']['upper_limit']['value']))
        
        # Check if the physical value falls inside an invalid SCALE-CONSTR
        if dop['physical_constraint']['scale_constraints'] is not None:
            for scale_constraint in dop['physical_constraint']['scale_constraints']:
                # Check if the value is within the LOWER-LIMIT
                match scale_constraint['lower_limit']['type']:
                    case 'INFINITE':
                        above_lower_limit = True
                    case 'OPEN':
                        above_lower_limit = (physical_value > scale_constraint['lower_limit']['value'])
                    case 'CLOSED':
                        above_lower_limit = (physical_value >= scale_constraint['lower_limit']['value'])
                
                # Check if the value is within the UPPER-LIMIT
                match scale_constraint['upper_limit']['type']:
                    case 'INFINITE':
                        below_upper_limit = True
                    case 'OPEN':
                        below_upper_limit = (physical_value < scale_constraint['upper_limit']['value'])
                    case 'CLOSED':
                        below_upper_limit = (physical_value <= scale_constraint['upper_limit']['value'])
                
                # If the value is in range and the SCALE-CONSTR is not VALID, raise an exception
                if above_lower_limit and below_upper_limit and scale_constraint['validity'] != 'VALID':
                    raise RuntimeError('Physical value {} falls in SCALE-CONSTR with validity {} (SN {}, DESC {})'.format(physical_value, scale_constraint['validity'], scale_constraint['short_name'], scale_constraint['description']))
    
    #print('{} ({}), physical value: {}'.format(dop['physical_base_data_type'], dop['compu_category'], physical_value))
    
    # If the physical type is not defined (e.g. for CODED-CONST), it is assumed the physical BASE-DATA-TYPE is the same as coded
    if 'physical_base_data_type' not in dop:
        dop['physical_base_data_type'] = dop['coded_base_data_type']
        dop['display_radix'] = 10
        dop['precision'] = None
    
    # Generate the value to be displayed based on the physical data type
    match dop['physical_base_data_type']:
        # Signed integer
        case 'A_INT32':
            display_value = '{:d}'.format(physical_value)
        
        # Unsigned integer
        case 'A_UINT32':
            # Convert it to a string in the specified base
            match dop['display_radix']:
                # BIN
                case 2:
                    display_value = '0b{:0{}b}'.format(physical_value, dop_bit_length)
                # OCT
                case 8:
                    display_value = '0o{:o}'.format(physical_value)
                # DEC
                case 10:
                    display_value = '{:d}'.format(physical_value)
                # HEX
                case 16:
                    display_value = '0x{:X}'.format(physical_value)
        
        # Floating point
        case 'A_FLOAT32' | 'A_FLOAT64':
            # If the PRECISION is specified, use it as the number of digits after the decimal point
            if dop['precision'] is not None:
                display_value = '{:.{}f}'.format(physical_value, dop['precision'])
            else:
                display_value = '{:f}'.format(physical_value)
        
        # String
        case 'A_UNICODE2STRING':
            display_value = physical_value
        
        # Byte array
        case 'A_BYTEFIELD':
            display_value = bytearray_to_string(physical_value)
        
        case _:
            raise RuntimeError('Unknown how to get display value from {}'.format(dop['physical_base_data_type']))
    
    # If there are units defined, add them after the value
    if 'units' in dop and dop['units'] is not None:
        display_value += ' ' + dop['units']['display_name']
    
    #print('display value: {}'.format(display_value))
    
    # Return the 3 computed values
    return internal_value, physical_value, display_value


# Get the amount of bytes needed by a STRUCTURE
### structure                      = object of type 'STRUCTURE'
### structure_response_bytes_slice = bytes extracted starting from the appropriate BYTE-POSITION in the response
def get_structure_byte_length(structure, structure_response_bytes_slice):
    if structure['type'] != 'STRUCTURE':
        raise RuntimeError('{} provided instead of STRUCTURE'.format(structure['type']))
    
    # If the STRUCTURE specifies its BYTE-SIZE directly, no more calculations are needed
    if structure['byte_size'] is not None:
        return structure['byte_size']
    
    # Otherwise, the size of the STRUCTURE is given by the "longest" PARAM inside it
    longest_parameter_byte_need = 0
    
    # Go through each PARAM of the STRUCTURE
    current_byte_position = 0
    for parameter in structure['parameters']:
        # If the PARAM is positioned (has BYTE-POSITION specified), use that as its BYTE-POSITION
        if parameter['byte_position'] is not None:
            current_byte_position = parameter['byte_position']
        
        # Get response bytes starting at the PARAM's BYTE-POSITION
        parameter_response_bytes_slice = structure_response_bytes_slice[current_byte_position:]
        
        # Calculate the amount of bytes this PARAM uses
        parameter_byte_length = get_parameter_byte_length(parameter, parameter_response_bytes_slice)
        
        # Determine how many bytes the STRUCTURE would need to have for this PARAM to exist
        parameter_byte_need = current_byte_position + parameter_byte_length
        
        # Update the maximum
        if parameter_byte_need > longest_parameter_byte_need:
            longest_parameter_byte_need = parameter_byte_need
        
        # If the next PARAM will be unpositioned, it will start right after this one
        current_byte_position += parameter_byte_length
    
    return longest_parameter_byte_need


# Get the amount of bytes needed by a PARAMETER
### parameter                      = object of type 'PARAMETER'
### parameter_response_bytes_slice = bytes extracted starting from the appropriate BYTE-POSITION in the response
def get_parameter_byte_length(parameter, parameter_response_bytes_slice):
    if parameter['type'] != 'PARAMETER':
        raise RuntimeError('{} provided instead of PARAMETER'.format(parameter['type']))
    
    # Get the PARAM's length based on its DOP type
    match parameter['dop']['type']:
        case 'DOP':
            # Get the DOP's length based on its DIAG-CODED-TYPE
            match parameter['dop']['diag_coded_type']:
                # For STANDARD-LENGTH-TYPE, the BIT-LENGTH is provided directly
                case 'STANDARD-LENGTH-TYPE':
                    parameter_bit_position = parameter['bit_position']
                    parameter_bit_length = parameter['dop']['bit_length']
        
                # For all other types, the size will be determined at runtime based on the response
                
                case 'LEADING-LENGTH-INFO-TYPE':
                    leading_length_value_bit_position = parameter['bit_position']
                    leading_length_value_bit_length = parameter['dop']['bit_length']
                    
                    # Get the length value, which starts at the first byte of the PARAM's bytes
                    content_byte_length = get_leading_length_info_type_length_value(leading_length_value_bit_position, leading_length_value_bit_length, parameter['dop']['endianness'], parameter_response_bytes_slice)
                    
                    # Calculate how many bytes the length value itself takes
                    leading_length_value_byte_length = get_byte_length(leading_length_value_bit_position, leading_length_value_bit_length)
                    
                    # The PARAM's length includes the length value's length and the content's length
                    parameter_byte_length = leading_length_value_byte_length + content_byte_length
                    
                    # The content (actual PARAM) starts at the byte edge (BIT-POSITION 0) following the length value
                    parameter_bit_position = 0
                    parameter_bit_length = 8 * parameter_byte_length
                
                case 'MIN-MAX-LENGTH-TYPE':
                    # Determine how many bytes are available for the PARAM
                    available_byte_count = len(parameter_response_bytes_slice)
                    
                    # At least 'MIN-LENGTH' bytes must be available
                    if available_byte_count < parameter['dop']['min_length']:
                        raise RuntimeError('Need {} bytes for MIN-MAX-LENGTH-TYPE, have {}'.format(parameter['dop']['min_length'], available_byte_count))
                    
                    # The TERMINATION value specifies a possible premature end of the PARAM
                    match parameter['dop']['termination']:
                        # END-OF-PDU: parsing stops after reaching MAX-LENGTH bytes, or reaching the end of the PDU
                        case 'END-OF-PDU':
                            # At least MAX-LENGTH bytes available: PARAM uses MAX-LENGTH bytes
                            if available_byte_count >= parameter['dop']['max_length']:
                                parameter_byte_length = parameter['dop']['max_length']
                            # Otherwise, PARAM uses all available bytes
                            else:
                                parameter_byte_length = available_byte_count
                        
                        # ZERO: parsing stops after reaching MAX-LENGTH bytes, finding 0x00 (or 0x0000), or reaching the end of the PDU
                        case 'ZERO':
                            # For A_UNICODE2STRING, the termination sequence is 0x0000
                            # For all other types which support MIN-MAX-LENGTH-TYPE, it's 0x00
                            if parameter['dop']['coded_base_data_type'] == 'A_UNICODE2STRING':
                                index_of_termination_in_response = (bytearray.fromhex('0000') in parameter_response_bytes_slice)
                            else:
                                index_of_termination_in_response = (bytearray.fromhex('00') in parameter_response_bytes_slice)
                            
                            # If the termination sequence was found, the bytes before it are used by the PARAM
                            if index_of_termination_in_response != -1:
                                parameter_byte_length = index_of_termination_in_response
                            # Otherwise, check for MAX-LENGTH
                            else:
                                # At least MAX-LENGTH bytes available: PARAM uses MAX-LENGTH bytes
                                if available_byte_count >= parameter['dop']['max_length']:
                                    parameter_byte_length = parameter['dop']['max_length']
                                # Otherwise, PARAM uses all available bytes
                                else:
                                    parameter_byte_length = available_byte_count
                        
                        # HEX-FF: parsing stops after reaching MAX-LENGTH bytes, finding 0xFF (or 0xFFFF), or reaching the end of the PDU
                        case 'HEX-FF':
                            # For A_UNICODE2STRING, the termination sequence is 0xFFFF
                            # For all other types which support MIN-MAX-LENGTH-TYPE, it's 0xFF
                            if parameter['dop']['coded_base_data_type'] == 'A_UNICODE2STRING':
                                index_of_termination_in_response = (bytearray.fromhex('FFFF') in parameter_response_bytes_slice)
                            else:
                                index_of_termination_in_response = (bytearray.fromhex('FF') in parameter_response_bytes_slice)
                            
                            # If the termination sequence was found, the bytes before it are used by the PARAM
                            if index_of_termination_in_response != -1:
                                parameter_byte_length = index_of_termination_in_response
                            # Otherwise, check for MAX-LENGTH
                            else:
                                # At least MAX-LENGTH bytes available: PARAM uses MAX-LENGTH bytes
                                if available_byte_count >= parameter['dop']['max_length']:
                                    parameter_byte_length = parameter['dop']['max_length']
                                # Otherwise, PARAM uses all available bytes
                                else:
                                    parameter_byte_length = available_byte_count
                    
                    # The PARAMETER starts where its BIT-POSITION specifies, and does not include the TERMINATION sequence if it was found
                    parameter_bit_position = parameter['bit_position']
                    parameter_bit_length = 8 * parameter_byte_length
                
                case _:
                    raise RuntimeError('Unhandled DIAG-CODED-TYPE type: {}'.format(parameter['dop']['diag_coded_type']))
        
        case 'STRUCTURE':
            # Determine how many bytes the STRUCTURE needs
            structure_byte_length = get_structure_byte_length(parameter['dop'], parameter_response_bytes_slice)
            
            # The PARAMETER, being a COMPLEX-DOP, starts at byte edge (BIT-POSITION = 0)
            parameter_bit_position = 0
            parameter_bit_length = 8 * structure_byte_length
        
        case 'STATIC-FIELD':
            # The FIELD will always have 'FIXED-NUMBER-OF-ITEMS' children
            number_of_repetitions = parameter['dop']['fixed_number_of_items']
            
            # Determine how many bytes the FIELD needs
            field_byte_length = number_of_repetitions * parameter['dop']['item_byte_size']
            
            # The PARAMETER, being a COMPLEX-DOP, starts at byte edge (BIT-POSITION = 0)
            parameter_bit_position = 0
            parameter_bit_length = 8 * field_byte_length
        
        case 'DYNAMIC-LENGTH-FIELD':
            # The number of repetitions is a value that needs to be extracted from the response
            determine_number_of_items_dop_response_bytes_slice = parameter_response_bytes_slice[parameter['dop']['determine_number_of_items']['byte_position']:]
            number_of_repetitions = get_dynamic_length_field_repetition_number(
                parameter['dop']['determine_number_of_items'],
                determine_number_of_items_dop_response_bytes_slice,
                parameter['dop']['determine_number_of_items']['bit_position']
            )
            
            # For the first item, the byte position is given by OFFSET relatively to the byte position of the DYNAMIC-LENGTH-FIELD
            field_byte_length = 0
            current_byte_position = parameter['dop']['offset']
            for i in range(number_of_repetitions):
                # Get the bytes for the referenced STRUCTURE
                structure_response_bytes_slice = parameter_response_bytes_slice[current_byte_position:]
                
                # The COMPLEX-DOP referenced by a FIELD is a STRUCTURE
                # Determine how many bytes it needs
                structure_byte_length = get_structure_byte_length(parameter['dop']['structure'], structure_response_bytes_slice)
                
                # Add the STRUCTURE's length to the total
                field_byte_length += structure_byte_length
                
                # Each further item starts at the byte edge following the item before
                current_byte_position += structure_byte_length
            
            # Determine how many bytes the FIELD needs
            field_byte_length = parameter['dop']['offset'] + field_byte_length
            
            # The PARAMETER, being a COMPLEX-DOP, starts at byte edge (BIT-POSITION = 0)
            parameter_bit_position = 0
            parameter_bit_length = 8 * field_byte_length
        
        case 'DYNAMIC-ENDMARKER-FIELD':
            # A STRUCTURE is repeated until the TERMINATION-VALUE is found or the end of the PDU is reached
            termination_value = int(parameter['dop']['termination_value'])
            
            # Parse until the TERMINATION-VALUE is found
            field_byte_length = 0
            current_byte_position = 0
            while True:
                # Stop parsing if the end of the PDU is reached
                if len(parameter_response_bytes_slice) == current_byte_position:
                    break
                
                # Get the bytes for the termination parameter that needs to be checked
                termination_parameter_response_bytes_slice = parameter_response_bytes_slice[current_byte_position:]
                
                # Calculate the parameter which might be equal to TERMINATION-VALUE by the referenced DOP
                termination_parameter_value = get_dop_value(parameter['dop']['determine_termination_parameter'], termination_parameter_response_bytes_slice, parameter['bit_position'])[1]
                
                # Calculate how many bytes the termination parameter itself takes
                termination_parameter_byte_length = get_byte_length(parameter['bit_position'], parameter['dop']['determine_termination_parameter']['bit_length'])
                
                # Stop parsing if the TERMINATION-VALUE is found
                if termination_parameter_value == termination_value:
                    field_byte_length += termination_parameter_byte_length
                    break
                
                # The same bytes are used for the STRUCTURE as for the termination value
                structure_response_bytes_slice = termination_parameter_response_bytes_slice
                
                # The COMPLEX-DOP referenced by a FIELD is a STRUCTURE
                # Determine how many bytes it needs
                structure_byte_length = get_structure_byte_length(parameter['dop']['structure'], structure_response_bytes_slice)
                
                # Add the STRUCTURE's length to the total
                field_byte_length += structure_byte_length
                
                # Each further item starts at the byte edge following the item before
                current_byte_position += structure_byte_length
            
            # The PARAMETER, being a COMPLEX-DOP, starts at byte edge (BIT-POSITION = 0)
            parameter_bit_position = 0
            parameter_bit_length = 8 * field_byte_length
        
        case 'END-OF-PDU-FIELD':
            # Parse until the end of the PDU
            field_byte_length = 0
            current_byte_position = 0
            while True:
                # Stop parsing if the end of the PDU is reached
                if len(parameter_response_bytes_slice) == current_byte_position:
                    break
                
                # Get the bytes needed for the STRUCTURE
                structure_response_bytes_slice = parameter_response_bytes_slice[current_byte_position:]
                
                # The COMPLEX-DOP referenced by a FIELD is a STRUCTURE
                # Determine how many bytes it needs
                structure_byte_length = get_structure_byte_length(parameter['dop']['structure'], structure_response_bytes_slice)
                
                # Add the STRUCTURE's length to the total
                field_byte_length += structure_byte_length
                
                # Each further item starts at the byte edge following the item before
                current_byte_position += structure_byte_length
            
            # The PARAMETER, being a COMPLEX-DOP, starts at byte edge (BIT-POSITION = 0)
            parameter_bit_position = 0
            parameter_bit_length = 8 * field_byte_length
        
        case 'MUX':
            # For MUXes, their length is given by the "longest" CASE
            longest_case_byte_length = 0
            
            # The bytes needed by any CASE starts at the specified MUX/BYTE-POSITION
            case_response_bytes_slice = parameter_response_bytes_slice[parameter['dop']['byte_position']:]
            
            # Go through each CASE
            for case in parameter['dop']['cases']:
                # Get the length of the CASE, which is a STRUCTURE
                case_byte_length = get_structure_byte_length(case['structure'], case_response_bytes_slice)
                
                # Update the maximum
                if case_byte_length > longest_case_byte_length:
                    longest_case_byte_length = case_byte_length
            
            # Check the DEFAULT-CASE too
            if parameter['dop']['default_case'] is not None:
                # Get the length of the DEFAULT-CASE, which is a STRUCTURE
                case_byte_length = get_structure_byte_length(parameter['dop']['default_case']['structure'], case_response_bytes_slice)
                
                # Update the maximum
                if case_byte_length > longest_case_byte_length:
                    longest_case_byte_length = case_byte_length
            
            # Determine how many bytes the (longest CASE of the) MUX would need to have
            mux_byte_need = parameter['dop']['byte_position'] + longest_case_byte_length
            
            # The PARAMETER, being a COMPLEX-DOP, starts at byte edge (BIT-POSITION = 0)
            parameter_bit_position = 0
            parameter_bit_length = 8 * mux_byte_need
        
        case 'DTC':
            # DTCs are guaranteed to start at byte edge and take 3 bytes
            parameter_bit_position = 0
            parameter_bit_length = 24
        
        case _:
            raise RuntimeError('Unhandled PARAMETER DOP type: {}'.format(parameter['dop']['type']))
    
    return get_byte_length(parameter_bit_position, parameter_bit_length)


# Parse a MWB response, returning a dictionary where inheritance is shown as nesting
### dop                      = object of any type
### dop_response_bytes_slice = bytes extracted starting from the appropriate BYTE-POSITION in the response
### dop_bit_position         = BIT-POSITION from which to extract the value (0-7)
def parse_mwb_dop(dop, dop_response_bytes_slice, dop_bit_position = 0):
    # Parse the object depending on its type
    match dop['type']:
        case 'PARAMETER':
            # Get the PARAM's name
            parameter_name = long_name_translation.get_long_name_translation(dop['long_name_id'], dop['long_name'])
            
            # Only PARAMs referencing COMPLEX-DOPs will have "children"
            output_object = {'type': 'PAR', 'name': parameter_name, 'is_reserved': False}
            
            # Parse the PARAM depending on its type
            match dop['parameter_type']:
                # RESERVED parameters are not displayed
                case 'RESERVED':
                    output_object['is_reserved'] = True
                
                # An exception should be thrown if the extracted internal value doesn't match the expected constant
                case 'CODED-CONST':
                    # Parse the DOP, which must be a simple value
                    # Even though there is technically no conversion from internal to physical value, the "display value" will contain the coded value as expected
                    child = parse_mwb_dop(dop['dop'], dop_response_bytes_slice, dop['bit_position'])
                    if child['type'] != 'VAL':
                        raise RuntimeError('DOP for CODED-CONST must be simple value, not {}'.fornat(child['type']))
                    
                    # Get the constant value as a string, depending on its data type
                    match dop['constant']['data_type']:
                        case 'A_INT32' | 'A_UINT32':
                            constant = '{:d}'.format(dop['constant']['value'])
                        case 'A_FLOAT32' | 'A_FLOAT64':
                            constant = '{:f}'.format(dop['constant']['value'])
                        case 'A_UNICODE2STRING':
                            constant = dop['constant']['value']
                        case 'A_BYTEFIELD':
                            constant = bytearray_to_string(dop['constant']['value'])
                        case _:
                            raise RuntimeError('Unknown how to get constant from {}'.format(dop['constant']['data_type']))
                    
                    # Ensure the parsed internal value matches the expected constant
                    if child['value'] != constant:
                        raise RuntimeError('Received coded value ({}) does not match constant ({})'.format(child['value'], constant))
                    
                    # The constant will be displayed as the parameter's value
                    output_object['value'] = child['value']
                
                # VALUE parameters might be simple values (or DTCs) or complex objects like structures, fields and multiplexers
                # PHYS-CONST values seem to be treated like VALUE by the MCD Kernel, without checking the physical value (the constant value is defined strangely anyways)
                case 'VALUE' | 'PHYS-CONST':
                    # Parse the DOP
                    child = parse_mwb_dop(dop['dop'], dop_response_bytes_slice, dop['bit_position'])
                    
                    match child['type']:
                        # If the "child" is a value (or DTC), the PARAM is a SIMPLE-DOP (has no children)
                        case 'VAL' | 'DTC':
                            output_object['value'] = child['value']
                        
                        # For FIELDs, move its children so that they belong to the PARAM
                        case 'FLD':
                            output_object['children'] = child['children']
                        
                        # For STRUCTUREs and MUXes, add them as the PARAM's only child
                        case 'STR' | 'MUX':
                            output_object['children'] = [child]
                        
                        case _:
                            raise RuntimeError('Unexpected type: {}'.format(child['type']))
                
                case _:
                    raise RuntimeError('Unhandled PARAMETER type: {}'.format(dop['parameter_type']))
            
            return output_object
        
        case 'DOP':
            # Parse the response bytes against the definition
            display_value = get_dop_value(dop, dop_response_bytes_slice, dop_bit_position)[2]
            
            # The object only has a value
            output_object = {'type': 'VAL', 'value': display_value}
            return output_object
        
        case 'STRUCTURE':
            # STRUCTUREs don't have a LONG-NAME-ID, so it can't be translated anyways
            # Its children will be its parameters
            output_object = {'type': 'STR', 'name': dop['long_name'], 'children': []}
            
            # Go through each PARAM of the STRUCTURE
            current_byte_position = 0
            for parameter in dop['parameters']:
                # Items inside STRUCTURE must be PARAMs
                if parameter['type'] != 'PARAMETER':
                    raise RuntimeError('STRUCTURE child must be PARAM, not {}'.format(parameter['type']))
                
                # If the PARAM is positioned (has BYTE-POSITION specified), use that as its BYTE-POSITION
                if parameter['byte_position'] is not None:
                    current_byte_position = parameter['byte_position']
                
                # Get response bytes starting at the PARAM's BYTE-POSITION
                parameter_response_bytes_slice = dop_response_bytes_slice[current_byte_position:]
                
                # Parse the PARAM
                child = parse_mwb_dop(parameter, parameter_response_bytes_slice)
                
                # Only add the PARAM if it's not RESERVED
                if not child['is_reserved']:
                    output_object['children'].append(child)
                
                # Calculate the amount of bytes needed by the PARAM
                parameter_byte_length = get_parameter_byte_length(parameter, parameter_response_bytes_slice)
                
                # If the next PARAM will be unpositioned, it will start right after this one
                current_byte_position += parameter_byte_length
            
            return output_object
        
        case 'STATIC-FIELD':
            # The FIELD will always have 'FIXED-NUMBER-OF-ITEMS' children
            output_object = {'type': 'FLD', 'children': []}
            
            # The number of repetitions is given via the attribute FIXED-NUMBER-OF-ITEMS
            number_of_repetitions = dop['fixed_number_of_items']
            
            # The COMPLEX-DOP referenced by a FIELD must be a STRUCTURE
            if dop['structure']['type'] != 'STRUCTURE':
                raise RuntimeError('FIELD child must be STRUCTURE, not {}'.format(dop['structure']['type']))
            
            # The first item starts at the same byte position as the STATIC-FIELD
            current_byte_position = 0
            for i in range(number_of_repetitions):
                # Get the bytes for the referenced STRUCTURE
                structure_response_bytes_slice = dop_response_bytes_slice[current_byte_position:]
                
                # Parse the referenced STRUCTURE
                output_object['children'].append(parse_mwb_dop(dop['structure'], structure_response_bytes_slice, 0))
                
                # For each further item, the byte position is increased by ITEM-BYTE-SIZE, which determines the length of one item in the field
                current_byte_position += dop['item_byte_size']
            
            return output_object
        
        case 'DYNAMIC-LENGTH-FIELD':
            # The FIELD might have no children
            output_object = {'type': 'FLD', 'children': []}
            
            # The determination of the number of repetitions is described by DETERMINE-NUMBER-OF-ITEMS
            # The DATA-OBJECT-PROP referenced to is used to calculate the repetition number, which is contained in its physical value of type A_UINT32
            # Its BYTE-POSITION is relative to that of the DYNAMIC-LENGTH-FIELD
            # The optional BIT-POSITION shall be between 0 and 7
            determine_number_of_items_bit_position = dop['determine_number_of_items']['bit_position']
            
            # Determine the number of repetitions by parsing the DOP and retrieving the physical value
            determine_number_of_items_dop_response_bytes_slice = dop_response_bytes_slice[dop['determine_number_of_items']['byte_position']:]
            number_of_repetitions = get_dynamic_length_field_repetition_number(
                dop['determine_number_of_items'],
                determine_number_of_items_dop_response_bytes_slice,
                determine_number_of_items_bit_position
            )
            
            # The COMPLEX-DOP referenced by a FIELD must be a STRUCTURE
            if dop['structure']['type'] != 'STRUCTURE':
                raise RuntimeError('FIELD child must be STRUCTURE, not {}'.format(dop['structure']['type']))
            
            # For the first item, the byte position is given by OFFSET relatively to the byte position of the DYNAMIC-LENGTH-FIELD
            current_byte_position = dop['offset']
            for i in range(number_of_repetitions):
                # Get the bytes for the referenced STRUCTURE
                structure_response_bytes_slice = dop_response_bytes_slice[current_byte_position:]
                
                # Parse the referenced STRUCTURE
                output_object['children'].append(parse_mwb_dop(dop['structure'], structure_response_bytes_slice, 0))
                
                # Determine how many bytes the referenced STRUCTURE uses
                structure_byte_length = get_structure_byte_length(dop['structure'], structure_response_bytes_slice)
                
                # Each further item starts at the byte edge following the item before
                current_byte_position += structure_byte_length
            
            return output_object
        
        case 'DYNAMIC-ENDMARKER-FIELD':
            # The FIELD might have no children
            output_object = {'type': 'FLD', 'children': []}
            
            # The value inside the TERMINATION-VALUE shall be given in the physical type of the referenced DATA-OBJECT-PROP
            # But it's actually a string...
            termination_value = int(dop['termination_value'])
            
            # The COMPLEX-DOP referenced by a FIELD must be a STRUCTURE
            if dop['structure']['type'] != 'STRUCTURE':
                raise RuntimeError('FIELD child must be STRUCTURE, not {}'.format(dop['structure']['type']))
            
            # Parse until the TERMINATION-VALUE is found
            current_byte_position = 0
            while True:
                # Stop parsing if the end of the PDU is reached
                if len(dop_response_bytes_slice) == current_byte_position:
                    break
                
                # Get the bytes for the termination parameter that needs to be checked
                termination_parameter_response_bytes_slice = dop_response_bytes_slice[current_byte_position:]
                
                # Calculate the parameter which might be equal to TERMINATION-VALUE by the referenced DOP
                termination_parameter_value = get_dop_value(dop['determine_termination_parameter'], termination_parameter_response_bytes_slice, dop_bit_position)[1]
                
                # Stop parsing if the TERMINATION-VALUE is found
                if termination_parameter_value == termination_value:
                    break
                
                # The same bytes are used for the STRUCTURE as for the termination value
                structure_response_bytes_slice = termination_parameter_response_bytes_slice
                
                # Parse the referenced STRUCTURE
                output_object['children'].append(parse_mwb_dop(dop['structure'], structure_response_bytes_slice, 0))
                
                # Determine how many bytes the referenced STRUCTURE uses
                structure_byte_length = get_structure_byte_length(dop['structure'], structure_response_bytes_slice)
                
                # Each further item starts at the byte edge following the item before
                current_byte_position += structure_byte_length
            
            return output_object
        
        case 'END-OF-PDU-FIELD':
            # The FIELD might have no children
            output_object = {'type': 'FLD', 'children': []}
            
            # The COMPLEX-DOP referenced by a FIELD must be a STRUCTURE
            if dop['structure']['type'] != 'STRUCTURE':
                raise RuntimeError('FIELD child must be STRUCTURE, not {}'.format(dop['structure']['type']))
            
            # Parse until the end of the PDU
            current_byte_position = 0
            while True:
                # Stop parsing if the end of the PDU is reached
                if len(dop_response_bytes_slice) == current_byte_position:
                    break
                # If there are still some bytes left, but not enough for the referenced STRUCTURE, an exception will be raised below
                
                # Get the bytes for the referenced STRUCTURE
                structure_response_bytes_slice = dop_response_bytes_slice[current_byte_position:]
                
                # Parse the referenced STRUCTURE
                output_object['children'].append(parse_mwb_dop(dop['structure'], structure_response_bytes_slice, 0))
                
                # Determine how many bytes the referenced STRUCTURE uses
                structure_byte_length = get_structure_byte_length(dop['structure'], structure_response_bytes_slice)
                
                # Each further item starts at the byte edge following the item before
                current_byte_position += structure_byte_length
            
            return output_object
        
        case 'MUX':
            # A multiplexer will only have one child (guaranteed, otherwise an exception is thrown)
            # The 'name' will be the LONG-NAME of the CASE (or DEFAULT-CASE)
            output_object = {'type': 'MUX', 'name': '', 'children': []}
            
            # The SWITCH-KEY starts at the PARAM/BYTE-POSITION ("parent")
            # Determine it by parsing the DOP and retrieving the physical value
            switch_key_value = get_dop_value(dop['switch_key'], dop_response_bytes_slice, dop_bit_position)[1]
            
            # Search for a matching CASE for the extracted SWITCH-KEY
            found_case = False
            for case in dop['cases']:
                # The limits are always specified as strings (for some reason)
                if switch_key_value >= int(case['lower_limit']) and switch_key_value <= int(case['upper_limit']):
                    # There is no LONG-NAME-ID so a translation can't be determined
                    output_object['name'] = case['long_name']
                    
                    # The COMPLEX-DOP referenced by a CASE must be a STRUCTURE
                    if case['structure']['type'] != 'STRUCTURE':
                        raise RuntimeError('CASE child must be STRUCTURE, not {}'.format(case['structure']['type']))
                    
                    # The CASE's data starts at MUX/BYTE-POSITION, starting from PARAM/BYTE-POSITION
                    structure_response_bytes_slice = dop_response_bytes_slice[dop['byte_position']:]
                    output_object['children'] = [parse_mwb_dop(case['structure'], structure_response_bytes_slice, 0)]
                    
                    # Stop searching
                    found_case = True
                    break
            
            # If no matching CASE was found, try the DEFAULT-CASE
            if not found_case:
                if dop['default_case'] is not None:
                    # There is no LONG-NAME-ID so a translation can't be determined
                    output_object['name'] = dop['default_case']['long_name']
                    
                    # The COMPLEX-DOP referenced by a CASE must be a STRUCTURE
                    if dop['default_case']['structure']['type'] != 'STRUCTURE':
                        raise RuntimeError('DEFAULT-CASE child must be STRUCTURE, not {}'.format(dop['default_case']['structure']['type']))
                    
                    # The CASE's data starts at MUX/BYTE-POSITION, starting from PARAM/BYTE-POSITION
                    structure_response_bytes_slice = dop_response_bytes_slice[dop['byte_position']:]
                    output_object['children'] = [parse_mwb_dop(dop['default_case']['structure'], structure_response_bytes_slice, 0)]
                
                # If no CASE is found, raise an exception
                else:
                    raise RuntimeError('Failed to find MUX SWITCH-CASE for SWITCH-KEY {} and no DEFAULT-CASE exists'.format(switch_key_value))
            
            return output_object
        
        case 'DTC':
            # A DTC will have a 'value' field, containing a formatted string of the fault
            output_object = {'type': 'DTC'}
            
            # The "trouble code" is the value received in the response
            # It is guaranteed to have BIT- and BYTE-POSITION both 0
            trouble_code = get_dop_value(dop, dop_response_bytes_slice, 0)[1]
            
            # Search the trouble code in the list of supported DTCs
            found_dtc = None
            for dtc_definition in dop['dtc_list']:
                if dtc_definition['trouble_code'] == trouble_code:
                    found_dtc = dtc_definition
                    break
            if found_dtc is None:
                raise RuntimeError('Could not find trouble code {:06X} in DTC list'.format(trouble_code))
            
            # Format a string as the object's value
            output_object['value'] = '{}({}): {}'.format(found_dtc['dtc'], found_dtc['level'], found_dtc['description'])
            return output_object
        
        case _:
            raise RuntimeError('Unhandled DOP type: {}'.format(dop['type']))


# Parse UDS response bytes as a MWB = Measured Value (Block)
### mwb_long_name_id     = LONG-NAME-ID, used for translating the measurement's name
### mwb_long_name        = LONG-NAME, used in case translation is not possible
### parsed_mwb_structure = object of type 'STRUCTURE' containing all parameters of the measurement
### response_bytes       = UDS response bytes, without the header (0x64, DID, etc.)
def parse_mwb_response(mwb_long_name_id, mwb_long_name, parsed_mwb_structure, response_bytes):
    # The top MWB level is simply a STRUCTURE
    output_object = parse_mwb_dop(parsed_mwb_structure, response_bytes)
    
    # Get the MWB's (translated) name
    output_object['name'] = long_name_translation.get_long_name_translation(mwb_long_name_id, mwb_long_name)
    
    # The returned object will contain each parameter of the MWB
    return output_object


# Convert a nested MWB dictionary to an "indented" list (each item has a 'level' attribute)
### parsed_mwb_response = dictionary returned by `parse_mwb_response()`
def process_parsed_mwb_response(parsed_mwb_response):
    # This function modifies a list passed "as reference", the outside function will return it
    def process(item, table, level):
        # Give each item a "description" depending on its type
        match item['type']:
            case 'STR':
                row_type = '[S]'
            case 'PAR':
                row_type = '[P]'
            case 'MUX':
                row_type = '[M]'
            case 'DTC':
                row_type = '[D]'
            case _:
                raise RuntimeError('{} unhandled'.format(item['type']))
        
        # Relationship will be shown by indentation level
        row = {'level': level, 'type': row_type, 'name': item['name']}
        
        # If the item already has a value, use that
        if 'value' in item:
            row['value'] = item['value']
        # Otherwise, the "value" will be the number of children
        else:
            row['value'] = len(item['children'])
        
        # Add the line to the table
        table.append(row)
        
        # If the item has children, add a row for each child (indented one level further)
        if 'children' in item:
            for child in item['children']:
                process(child, table, level + 1)
    
    # Convert the parsed MWB response to a "table", with each "row" representing a parameter
    processed_mwb_response = []
    process(parsed_mwb_response, processed_mwb_response, 0)
    return processed_mwb_response


# Display an indented MWB list in the console
### processed_mwb_response = list returned by `process_parsed_mwb_response()`
def dump_processed_mwb_response(processed_mwb_response):
    # Display each item with its associated indentation level
    for item in processed_mwb_response:
        object_printer.print_indented(item['level'], '{} {} - {}'.format(item['type'], item['name'], item['value']))


# Parse the UDS service 0x22 response of an ECU-VARIANT from an MCD Project
### object_loader         = instance of ObjectLoader, with StringStorage instance loaded from the target Project
### long_name_translation = instance of LongNameTranslation, for translating LONG-NAMEs
### project_folder_path   = Project path (folder with .db and .key files)
### base_variant_filename = path of desired BASE-VARIANT file (.bv.db), with or without the .db extension
### desired_ecu_variant   = ECU-VARIANT name (included in BASE-VARIANT) for which to parse the response
### response              = string of UDS response bytes in HEX, without header bytes
def app_parseMWB(object_loader, long_name_translation, project_folder_path, base_variant_filename, desired_ecu_variant, desired_did, response):
    # The PoolID simply refers to the file's name (without extension)
    pool_id = base_variant_filename
    if base_variant_filename.endswith('.db'):
        pool_id = base_variant_filename[:-3]
    
    # Only parse a .bv.db file
    if enum_converters.get_db_file_type(pool_id) != 'Base Variant':
        raise RuntimeError('A BASE-VARIANT database must be provided (.bv.db)')
    
    # Some references will only specify the ObjectID (object name) and not the PoolID (file name)
    # To resolve them, there are 3(+) maps that link an ObjectID with a PoolID: one for the ECU-VARIANT, one for the BASE-VARIANT, and one (or more) for the protocol
    # The ObjectID will be searched in them, in that order
    # The maps are contained in the "layer data" object of each database
    protocol_layer_data_list = get_protocol_layer_data_list(object_loader, project_folder_path)
    
    # Load the Object with ID '#RtGen_DB_PROJECT_DATA', which contains info about the ECU-VARIANTs included in the BASE-VARIANT
    db_project_data = object_loader.load_object_by_id(project_folder_path, pool_id, '#RtGen_DB_PROJECT_DATA')
    
    # Get the BASE-VARIANT's name
    base_variant_name = db_project_data['ecu_base_variant_ref']['object_id']
    
    # Load the layer data for the BASE-VARIANT, which is contained in the current file
    base_variant_layer_data = object_loader.load_object_by_id(project_folder_path, pool_id, '#RtGen_DB_LAYER_DATA')
    
    # Get a map of available ECU-VARIANTs (each name resolves to a reference)
    ecu_variant_map = get_ecu_variant_map(db_project_data)
    
    # If there are no ECU-VARIANTs, there is nothing to do
    if ecu_variant_map is None:
        raise RuntimeError('BASE-VARIANT {} contains no ECU-VARIANTs'.format(base_variant_name))
    
    # Get the reference for the requested ECU-VARIANT
    try:
        ecu_variant_reference = ecu_variant_map[desired_ecu_variant]
    
    # If the requested ECU-VARIANT doesn't exist, print the list of available ECU-VARIANTs
    except KeyError:
        object_printer.print_indented(0, 'Available ECU-VARIANTs:')
        for ecu_variant in ecu_variant_map:
            object_printer.print_indented(1, ecu_variant)
        object_printer.print_indented(0, '')
        raise RuntimeError('Could not find ECU-VARIANT {}'.format(desired_ecu_variant))
    
    # Load the layer data for the ECU-VARIANT
    ecu_variant_layer_data = get_ecu_variant_layer_data(object_loader, project_folder_path, ecu_variant_reference)
    
    # Get a map of available MWBs (each DID resolves to a dictionary with a LONG-NAME and LONG-NAME-ID)
    mwb_map_result = get_mwb_map(object_loader, project_folder_path, ecu_variant_layer_data)
    
    # If there are no MWBs, there is nothing to do
    if mwb_map_result is None:
        raise RuntimeError('ECU-VARIANT {} contains no MWBs'.format(desired_ecu_variant))
    else:
        mwb_map, response_parameter_table = mwb_map_result
    
    # If the DID was provided as a string, convert it to an integer, assuming it's in HEX format
    if isinstance(desired_did, str):
        desired_did = int(desired_did, 16)
    else:
        desired_did = int(desired_did)
    
    # If the requested DID does not exist, print the list of available DIDs
    if desired_did not in mwb_map:
        object_printer.print_indented(0, 'Available DIDs:')
        for did in sorted(mwb_map):
            object_printer.print_indented(1, '{:04X}'.format(did))
        object_printer.print_indented(0, '')
        raise RuntimeError('DID {:04X} does not exist'.format(desired_did))
    
    # Get the table of MWBs (a MWB LONG-NAME resolves to the corresponding table row's reference)
    mwb_table = get_mwb_table(response_parameter_table)
    
    # Get the request MWB's name and corresponding table row parameter
    table_row_result = get_mwb_name_and_table_row_parameter_by_did(object_loader, project_folder_path, mwb_table, mwb_map, desired_did)
    if table_row_result is None:
        raise RuntimeError('Failed to find MWB table row')
    else:
        mwb_long_name, mwb_long_name_id, mwb_table_row_parameter = table_row_result
    
    # Get the corresponding STRUCTURE parameter of the requested MWB
    mwb_structure = get_mwb_structure(object_loader, project_folder_path, mwb_table_row_parameter)
                
    # These objects will be used (in this order) for solving references which don't specify a PoolID
    layer_data_objects = [ecu_variant_layer_data, base_variant_layer_data] + protocol_layer_data_list
    
    # Parse the MWB STRUCTURE
    parsed_mwb_structure = parse_dop(object_loader, layer_data_objects, project_folder_path, mwb_structure)
    
    # The top level is simply a STRUCTURE, so, being a COMPLEX-DOP, must start at byte edge (BIT-POSITION = 0)
    # It should probably start at the first byte too
    if mwb_table_row_parameter['byte_position'] != 0 or mwb_table_row_parameter['bit_position'] != 0:
        raise RuntimeError('Expected BYTE- and BIT-POSITION 0 for top MWB level, not {} and {}'.format(mwb_table_row_parameter['byte_position'], mwb_table_row_parameter['bit_position']))
    
    # Convert the response string to a bytearray
    response_bytes = bytearray.fromhex(response)
    
    # Parse the response and display it
    parsed_mwb_response = parse_mwb_response(mwb_long_name_id, mwb_long_name, parsed_mwb_structure, response_bytes)
    processed_mwb_response = process_parsed_mwb_response(parsed_mwb_response)
    dump_processed_mwb_response(processed_mwb_response)


# Handle usage as script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('project_folder_path', help='MCD Project (folder containing .db and .key files)')
    parser.add_argument('base_variant_filename', help='Filename of BASE-VARIANT (.bv.db) whose MWB to parse')
    parser.add_argument('ecu_variant_name', help='Name of desired ECU-VARIANT')
    parser.add_argument('did', help='Desired UDS DID, specified as two HEX bytes')
    parser.add_argument('response', help='Bytes of UDS response, written in HEX (without the positive response byte, DID, etc.)')
    parser.add_argument('translation_database_folder_path', help='Folder containing the translation database (e.g. ".../DIDB/db")', nargs='?')
    parser.add_argument('translation_language', help='Language for translations (e.g. "en_US")', nargs='?')
    args = parser.parse_args()
    
    # The project_folder_path argument must be a path to a folder
    if not os.path.isdir(args.project_folder_path):
        raise RuntimeError('Project must be folder')
    
    # The project name is the name of the last folder in the path
    project_name = os.path.basename(args.project_folder_path)
    
    # Create an instance of the StringStorage class, used for loading the strings database
    # The strings database is unique to each Project
    string_storage = StringStorage(args.project_folder_path)
    
    # An instance of the ObjectLoader class is used for loading Objects and references from the BASE-VARIANT Pool
    # The first parameter (instance of the PblRecordManager class) is needed here since PBL records will be handled "internally"
    object_loader = ObjectLoader(pbl_record_manager, string_storage)
    
    # Initialize the LONG-NAME translation (if the optional arguments are not given, nothing is really done)
    # The file "hsqldb.jar" should be in the working directory, in the "bin" folder
    long_name_translation = LongNameTranslation('bin/hsqldb.jar', args.translation_database_folder_path, args.translation_language)
    
    # Run the app
    app_parseMWB(object_loader, long_name_translation, args.project_folder_path, args.base_variant_filename, args.ecu_variant_name, args.did, args.response)
