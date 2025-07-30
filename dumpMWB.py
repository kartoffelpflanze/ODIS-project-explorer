import argparse
import os
import sys
import time
import traceback

from common_utils import enum_converters, object_printer
from classes.PblRecordManager import PblRecordManager
from classes.StringStorage import StringStorage
from classes.ObjectLoader import ObjectLoader


# PBL is needed for parsing .key files, which will be done by the PblRecordManager class
# The file "pbl.dll" should be in the working directory, in the "bin" folder
pbl_dll_path = os.path.join(os.path.abspath(os.getcwd()), 'bin/pbl.dll')
pbl_record_manager = PblRecordManager(pbl_dll_path)


# Get a list of "layer data" objects necessary for resolving DOP references with the UDS protocol, in order of relevance
### object_loader       = instance of ObjectLoader, with StringStorage instance loaded from the target project
### project_folder_path = project path (folder with .db and .key files)
def get_protocol_layer_data_list(object_loader, project_folder_path):
    # Load the layer data for the UDS protocol, which is always 'UDSOnCAN', with its associated PoolID
    uds_protocol_layer_data = object_loader.load_object_by_id(project_folder_path, '0.0.0@PR_UDSOnCAN.pr', '#RtGen_DB_LAYER_DATA')
    
    # In some rare cases, even the definition for standard OBD protocol will be needed, if the reference isn't found in UDS
    obd_protocol_layer_data = object_loader.load_object_by_id(project_folder_path, '0.0.0@PR_OBDOnCAN.pr', '#RtGen_DB_LAYER_DATA')
                    
    # The UDS protocol's layer data may reference "parent layers" which will have layer data objects too
    protocol_layer_data_list = []
    for protocol_parent_layer_PoolID in uds_protocol_layer_data['parent_layers_vector']:
        protocol_layer_data_list.append(object_loader.load_object_by_id(project_folder_path, protocol_parent_layer_PoolID, '#RtGen_DB_LAYER_DATA'))
    
    # Add the main protocols layer data at the end of the list, since they will be parsed in this order and these are the least important layers
    protocol_layer_data_list.append(uds_protocol_layer_data)
    protocol_layer_data_list.append(obd_protocol_layer_data)
    return protocol_layer_data_list


# Convert a list of coefficients to a polynomial
### coefficients = list of coefficients for each term
def polynomial_to_string(coefficients):
    # This list will contain all terms of the polynomial, as formatted strings
    terms = []
    
    # The coefficients are given in ascending order of power (0 to n)
    for power, coefficient in enumerate(coefficients):
        # Don't write terms with the coefficient 0
        if coefficient == 0:
            continue
        
        # The first term has no "x"
        if power == 0:
            term = '{}'.format(coefficient)
        
        # The second term has no "power"
        elif power == 1:
            term = '{} * x'.format(coefficient)
        
        # All other terms have a coefficient and power
        else:
            term = '{} * x**{}'.format(coefficient, power)
        
        # Add the term to the list
        terms.append(term)
    
    # Construct the polynomial as all terms added together
    return ' + '.join(terms) or '0'


# Parse an object, returning a dictionary with its important fields
### object_loader       = instance of ObjectLoader, with StringStorage instance loaded from the target project
### layer_data_objects  = list or "layer data" objects, used for solving references which don't specify the PoolID (file name)
### project_folder_path = project path (folder with .db and .key files)
### dop                 = object to parse
def parse_dop(object_loader, layer_data_objects, project_folder_path, dop):
    # Create the dictionary which will be filled with the object's parsed fields
    output_object = {}
    
    # Parse the object, depending on its type
    match dop['#OBJECT_TYPE']:
        # Parameter: MCD-2D V2.2 - 7.3.5.4
        case 'MCD_DB_PARAMETER_SIMPLE':
            output_object['type'] = 'PARAMETER'
            
            # Get the LONG-NAME, LONG-NAME-ID and DESCRIPTION of the parameter
            output_object['long_name'] = dop['long_name']
            output_object['long_name_id'] = dop['long_name_id']
            output_object['description'] = dop['description']
            
            # BYTE-POSITION and BIT-POSITION specify the start position of the parameter in the PDU, where the counting starts with 0
            output_object['byte_position'] = dop['byte_position'] if dop['is_byte_pos_available'] else None
            output_object['bit_position'] = dop['bit_position']
            
            # BIT-POSITION shall not have a value greater than 7
            if output_object['bit_position'] not in range(0, 8):
                raise RuntimeError('BIT-POSITION {} not between [0, 7]'.format(output_object['bit_position']))
            
            # Parse the PARAM, depending on its type
            match dop['mcd_parameter_type']:
                # VALUE parameter: MCD-2D V2.2 - page 78, paragraph 1
                case 'eVALUE':
                    # A VALUE parameter is a frequently used parameter type
                    # It references a DOP, which converts a value from coded into physical representation (and vice versa)
                    output_object['parameter_type'] = 'VALUE'
                    
                    # In a response message, PHYSICAL-DEFAULT-VALUE is used for verification of the received value
                    # In this case, the received coded value shall be converted into the physical representation
                    # After that, the specified and the received values can be compared
                    output_object['default_value'] = None
                    if dop['default_mcd_value'] is not None:
                        # Ensure the default value's data type is valid
                        if not dop['default_mcd_value']['data_type'].startswith('eA_'):
                            raise RuntimeError('Strange PHYSICAL-DEFAULT-VALUE type: {}'.format(dop['default_mcd_value']['data_type']))
                        
                        # Store the default value
                        output_object['default_value'] = {}
                        output_object['default_value']['data_type'] = dop['default_mcd_value']['data_type'][1:]
                        output_object['default_value']['value'] = dop['default_mcd_value']['value']
                    
                    # The referenced DOP might be missing the PoolID
                    # The following function will try to find it using the DOP reference maps found in the database's LayerData
                    try:
                        parameter_dop = object_loader.load_DOP_by_reference_without_PoolID(project_folder_path, layer_data_objects, dop['db_object_ref'])
                    
                    # If not found (error in project), mimic the MCD error that is thrown on projects with this sort of problem
                    except:
                        output_object['dop'] = {'#error': 'Access to database element failed - DOP with name: {}'.format(dop['db_object_ref']['object_id'])}
                    
                    # The DOP is usually found
                    else:
                        # Add the referenced DOP to the object
                        output_object['dop'] = parse_dop(object_loader, layer_data_objects, project_folder_path, parameter_dop)
                
                # RESERVED parameter: MCD-2D V2.2 - page 78, paragraph 2
                case 'eRESERVED':
                    # A parameter of type RESERVED is used when the parameter should be ignored by the D-server
                    # Such parameters are not interpreted and are not shown on the user's display
                    output_object['parameter_type'] = 'RESERVED'
                    
                    # RESERVED parameters must have a default value
                    if dop['default_mcd_value'] is None:
                        raise RuntimeError('RESERVED has no default')
                    
                    # Ensure the default value's data type is valid
                    if not dop['default_mcd_value']['data_type'].startswith('eA_'):
                        raise RuntimeError('Strange DEFAULT-VALUE type: {}'.format(dop['default_mcd_value']['data_type']))
                    
                    # Store the default value
                    output_object['default_value'] = {}
                    output_object['default_value']['data_type'] = dop['default_mcd_value']['data_type'][1:]
                    output_object['default_value']['value'] = dop['default_mcd_value']['value']
                    
                    # A parameter of type RESERVED shouldn't reference any DOP
                    if dop['db_object_ref'] is not None:
                        raise RuntimeError('CODED-CONST references DOP')
                    
                    # Instead, the DIAG-CODED-TYPE is included in the RESERVED PARAM's definition
                    # "Pretend" the current object is of type 'DOP', in order to add it as a field like with all other PARAMs
                    dummy_dop = dop
                    dummy_dop['#OBJECT_TYPE'] = 'DB_DOP_SIMPLE_BASE'
                    output_object['dop'] = parse_dop(object_loader, layer_data_objects, project_folder_path, dummy_dop)
                
                # CODED-CONST parameter: MCD-2D V2.2 - page 79, paragraph 1
                case 'eCODED_CONST':
                    # CODED-CONST parameters can be used in a response for verification of the received value without converting it into the physical representation
                    output_object['parameter_type'] = 'CODED-CONST'
                    
                    # CODED-CONST parameters must have a default value
                    if dop['default_mcd_value'] is None:
                        raise RuntimeError('CODED-CONST has no default')
                    
                    # Ensure the default value's data type is valid
                    if not dop['default_mcd_value']['data_type'].startswith('eA_'):
                        raise RuntimeError('Strange CODED-DEFAULT-VALUE type: {}'.format(dop['default_mcd_value']['data_type']))
                    
                    # Store the constant value
                    output_object['constant'] = {}
                    output_object['constant']['data_type'] = dop['default_mcd_value']['data_type'][1:]
                    output_object['constant']['value'] = dop['default_mcd_value']['value']
                    
                    # A parameter of type CODED-CONST shouldn't reference any DOP
                    if dop['db_object_ref'] is not None:
                        raise RuntimeError('CODED-CONST references DOP')
                    
                    # Instead, the DIAG-CODED-TYPE is included in the CODED-CONST PARAM's definition
                    # "Pretend" the current object is of type 'DOP', in order to add it as a field like with all other PARAMs
                    dummy_dop = dop
                    dummy_dop['#OBJECT_TYPE'] = 'DB_DOP_SIMPLE_BASE'
                    output_object['dop'] = parse_dop(object_loader, layer_data_objects, project_folder_path, dummy_dop)
                
                # PHYS-CONST parameter: MCD-2D V2.2 - page 79, paragraph 2
                case 'ePHYS_CONST':
                    # PHYS-CONST is an alternative for CODED-CONST with the difference that the value is given in the physical representation
                    output_object['parameter_type'] = 'PHYS-CONST'
                    
                    # In a response, the received coded value shall be converted into the physical representation
                    # After that, the specified and the calculated values can be compared
                    
                    # PHYS-CONST parameters must have a default value
                    if dop['default_mcd_value'] is None:
                        raise RuntimeError('PHYS-CONST has no default')
                    
                    # Ensure the default value's data type is valid
                    if not dop['default_mcd_value']['data_type'].startswith('eA_'):
                        raise RuntimeError('Strange PHYSICAL-DEFAULT-VALUE type: {}'.format(dop['default_mcd_value']['data_type']))
                    
                    # Store the constant value
                    output_object['constant'] = {}
                    output_object['constant']['data_type'] = dop['default_mcd_value']['data_type'][1:]
                    output_object['constant']['value'] = dop['default_mcd_value']['value']
                    
                    # The referenced DOP might be missing the PoolID
                    # The following function will try to find it using the DOP reference maps found in the database's LayerData
                    parameter_dop = object_loader.load_DOP_by_reference_without_PoolID(project_folder_path, layer_data_objects, dop['db_object_ref'])
                    
                    # Add the referenced DOP to the object
                    output_object['dop'] = parse_dop(object_loader, layer_data_objects, project_folder_path, parameter_dop)
                
                case _:
                    object_printer.print_indented(0, '') 
                    object_printer.print_object(dop, 'dop', 0)
                    object_printer.print_indented(0, '')
                    raise RuntimeError('Unknown MCD type: {}'.format(dop['mcd_parameter_type']))
        
        # Data object property: MCD-2D V2.2 - 7.3.6.2
        case 'DB_DOP_SIMPLE_BASE':
            output_object['type'] = 'DOP'
            
            # The class `DATA-OBJECT-PROP` describes how to extract and decode a single data item from the byte stream of the response message,
            # and how to transform the internal value into its physical representation using a computational method (COMPU-METHOD)
            # A DATA-OBJECT-PROP consists of a COMPU-METHOD, a DIAG-CODED-TYPE and a PHYSICAL-TYPE
            # Optionally, an INTERNAL-CONSTR and a PHYS-CONSTR can be given for a DATA-OBJECT-PROP, and a UNIT may be referenced
            
            # DIAG-CODED-TYPE is responsible for extraction of the coded value out of the byte stream
            diag_coded_type = dop['diag_coded_type']
            
            # Some sanity checks...
            if diag_coded_type['is_condensed_bit_mask']:
                raise RuntimeError('BITMASK is CONDENSED')
            if not diag_coded_type['base_data_type_as_mcd_data_type'].startswith('eA_'):
                raise RuntimeError('Strange BASE-DATA-TYPE: {}'.format(diag_coded_type['base_data_type_as_mcd_data_type']))
            
            # The coded value type inside the message is described by the member BASE-DATA-TYPE of the DIAG-CODED-TYPE
            # Get the coded value's BASE-DATA-TYPE (without the 'e' enum prefix)
            output_object['coded_base_data_type'] = diag_coded_type['base_data_type_as_mcd_data_type'][1:]
            
            # Handle the DIAG-CODED-TYPE based on its type
            match diag_coded_type['type']:
                # The length of the parameter is to be extracted from the PDU
                case 'eLEADING_LENGTH_INFO_TYPE':
                    output_object['diag_coded_type'] = 'LEADING-LENGTH-INFO-TYPE'
                    
                    # BIT-LENGTH specifies the bit count at the beginning of this parameter and shall be greater than 0
                    output_object['bit_length'] = diag_coded_type['bit_length']
                    if output_object['bit_length'] <= 0:
                        raise RuntimeError('Invalid BIT-LENGTH: {}'.format(output_object['bit_length']))
                    
                    # These bits contain the length of the parameter, in bytes
                    # The bits of length information are not part of the coded value
                    # That means the data extraction of the coded value starts at the byte edge to this length information
                
                # The minimum and the maximum length of a parameter in a message are specified by MIN-LENGTH and MAX-LENGTH
                case 'eMIN_MAX_LENGTH_TYPE':
                    output_object['diag_coded_type'] = 'MIN-MAX-LENGTH-TYPE'
                    
                    # Get the MIN-LENGTH and MAX-LENGTH
                    output_object['min_length'] = diag_coded_type['min_length']
                    output_object['max_length'] = diag_coded_type['max_length']
                    
                    # TERMINATION specifies a possible premature end of a parameter in the message,
                    # that is, the end of the parameteris reached before MAX-LENGTH bytes have been read
                    match diag_coded_type['termination']:
                        # The byte stream to be extracted is terminated by the first of the following conditions:
                        # - finding termination character 0x00 (A_ASCIISTRING and A_UTF8STRING*) or 0x0000 (A_UNICODE2STRING) after MIN-LENGTH bytes
                        # - reaching MAX-LENGTH bytes
                        # - reaching end of PDU
                        case 'eZERO':
                            output_object['termination'] = 'ZERO'
                        
                        # The byte stream to be extracted is terminated by the first of the following conditions:
                        # - finding termination character 0xFF (A_ASCIISTRING and A_UTF8STRING) or 0xFFFF (A_UNICODE2STRING) after MIN-LENGTH bytes
                        # - reaching MAX-LENGTH bytes
                        # - reaching end of PDU
                        case 'eHEX_FF':
                            output_object['termination'] = 'HEX-FF'
                        
                        # The byte stream to be extracted is terminated by the first of the following conditions:
                        # - reaching MAX-LENGTH bytes
                        # - reaching end of PDU
                        case 'eENDOFPDU':
                            output_object['termination'] = 'END-OF-PDU'
                        
                        case _:
                            raise RuntimeError('Unknown TERMINATION for MIN-MAX-LENGTH-TYPE: {}'.format(diag_coded_type['termination']))
                    
                    # In the case of A_UNICODE2STRING, the length of the actual payload and the values of MIN-LENGTH and MAX-LENGTH shall be even
                    #if output_object['coded_base_data_type'] == 'A_UNICODE2STRING' and (output_object['min_length'] % 2 != 0 or output_object['max_length'] % 2 != 0):
                    #    raise RuntimeError('MIN-LENGTH and MAX-LENGTH for coded BASE-DATA-TYPE A_UNICODE2STRING should be even, not {}, {}'.format(output_object['min_length'], output_object['max_length']))
                    ### Encountered A_UNICODE2STRING with MAX-LENGTH 4095, so...
                
                # The parameter always occupies the specified length of BIT-LENGTH bits inside the message
                case 'eSTANDARD_LENGTH_TYPE':
                    output_object['diag_coded_type'] = 'STANDARD-LENGTH-TYPE'
                    
                    # Get the BIT-LENGTH
                    output_object['bit_length'] = diag_coded_type['bit_length']
                    
                    # The value of BIT-LENGTH shall be greater than 0
                    if output_object['bit_length'] <= 0:
                        raise RuntimeError('Invalid BIT-LENGTH: {}'.format(output_object['bit_length']))
                    
                    # Optionally, an attribute BIT-MASK can be specified, if some bits inside the response message should be masked out
                    
                    # Get the BIT-MASK and save it as None if it's empty
                    output_object['bit_mask'] = diag_coded_type['bit_mask'] if diag_coded_type['bit_mask'] != bytearray() else None
                    
                    # The CONDENSED attribute, if True, will raise an exception above, it's not important yet, has not been encountered
                
                # I have not encountered other types yet
                case _:
                    raise RuntimeError('Unknown DIAG-CODED-TYPE type: {}'.format(diag_coded_type['type']))
            
            # MIN-MAX-LENGTH-TYPE is only allowed for the internal data types A_BYTEFIELD, A_ASCIISTRING, A_UNICODE2STRING and A_UTF8STRING
            if diag_coded_type['type'] == 'eMIN_MAX_LENGTH_TYPE':
                if output_object['coded_base_data_type'] not in ['A_BYTEFIELD', 'A_ASCIISTRING', 'A_UNICODE2STRING', 'A_UTF8STRING']:
                    raise RuntimeError('MIN-MAX-LENGTH-TYPE not allowed for BASE-DATA-TYPE {}'.format(output_object['coded_base_data_type']))
            
            # Regardless of the type of length specification, the following additional restrictions have to be considered depending on the BASE-DATA-TYPE
            else:
                if output_object['coded_base_data_type'] in ['A_INT32', 'A_UINT32'] and output_object['bit_length'] not in range(1, 32 +1):
                    #raise RuntimeError('BIT-LENGTH for {} must be between 1 and 32, not {}'.format(output_object['coded_base_data_type'], output_object['bit_length']))
                    output_object['#error'] = 'BIT-LENGTH for {} must be between 1 and 32, not {}'.format(output_object['coded_base_data_type'], output_object['bit_length'])
                    return output_object
                if output_object['coded_base_data_type'] == 'A_FLOAT32' and output_object['bit_length'] != 32:
                    raise RuntimeError('BIT-LENGTH for A_FLOAT32 must be 32, not {}'.format(output_object['bit_length']))
                if output_object['coded_base_data_type'] == 'A_FLOAT64' and output_object['bit_length'] != 64:
                    raise RuntimeError('BIT-LENGTH for A_FLOAT64 must be 64, not {}'.format(output_object['bit_length']))
                if output_object['coded_base_data_type'] in ['A_ASCIISTRING', 'A_UTF8STRING'] and output_object['bit_length'] % 8 != 0: # for A_BYTEFIELD too, but encountered BIT-LENGTH 12 for it...
                    raise RuntimeError('BIT-LENGTH for {} must be multiple of 8, not {}'.format(output_object['coded_base_data_type'], output_object['bit_length']))
                if output_object['coded_base_data_type'] == 'A_UNICODE2STRING' and output_object['bit_length'] % 16 != 0:
                    #raise RuntimeError('BIT-LENGTH for A_UNICODE2STRING must be multiple of 16, not {}'.format(output_object['bit_length']))
                    output_object['#error'] = 'BIT-LENGTH for A_UNICODE2STRING must be multiple of 16, not {}'.format(output_object['bit_length'])
                    return output_object
            
            # The member ENCODING of the DIAG-CODED-TYPE gives the method used for encoding of the value in the PDU
            # Remove the 'e' prefix and replace underscores by dashes, to convert the enum value to a standard ODX name
            output_object['encoding'] = diag_coded_type['encoding'][1:].replace('_', '-')
            
            # 
            if output_object['encoding'] == 'NONE' and output_object['coded_base_data_type'] == 'A_FLOAT64':
                output_object['#error'] = 'Invalid ENCODING for {}: {}'.format(output_object['coded_base_data_type'], output_object['encoding'])
                return output_object
            
            # The loader has already checked that the ENCODING attribute is valid for the BASE-DATA-TYPE,
            # but it is checked here again against the documentation
            if ((output_object['encoding'] == 'BCD-UP'     and output_object['coded_base_data_type'] not in ['A_BYTEFIELD'                          ]) or
                (output_object['encoding'] == 'BCD-P'      and output_object['coded_base_data_type'] not in ['A_UINT32', 'A_BYTEFIELD'              ]) or
                (output_object['encoding'] == '2C'         and output_object['coded_base_data_type'] not in ['A_INT32'                              ]) or
                (output_object['encoding'] == '1C'         and output_object['coded_base_data_type'] not in ['A_INT32'                              ]) or
                (output_object['encoding'] == 'SM'         and output_object['coded_base_data_type'] not in ['A_INT32'                              ]) or
                (output_object['encoding'] == 'IEEE754'    and output_object['coded_base_data_type'] not in ['A_FLOAT32', 'A_FLOAT64'               ]) or
                (output_object['encoding'] == 'ISO-8859-1' and output_object['coded_base_data_type'] not in ['A_ASCIISTRING'                        ]) or
                (output_object['encoding'] == 'UCS-2'      and output_object['coded_base_data_type'] not in ['A_UNICODE2STRING'                     ]) or
                (output_object['encoding'] == 'UTF-8'      and output_object['coded_base_data_type'] not in ['A_UNICODE2STRING'                     ]) or # should use UCS-2... idk
                (output_object['encoding'] == 'NONE'       and output_object['coded_base_data_type'] not in ['A_UINT32', 'A_BYTEFIELD', 'A_BITFIELD'])):
                    raise RuntimeError('Invalid ENCODING for {}: {}'.format(output_object['coded_base_data_type'], output_object['encoding']))
            if output_object['encoding'] not in ['BCD-UP', 'BCD-P', '2C', '1C', 'SM', 'IEEE754', 'ISO-8859-1', 'UCS-2', 'UTF-8', 'NONE']:
                raise RuntimeError('Unknown ENCODING (for {}): {}'.format(output_object['coded_base_data_type'], output_object['encoding']))
            
            # Store the IS-HIGHLOW-BYTE-ORDER attribute as 'big'/'little' endianness
            output_object['endianness'] = 'big' if diag_coded_type['is_high_low_byte_order'] else 'little'
            
            # PHYSICAL-TYPE specifies the physical representation of the value
            if 'physical_type' in dop:
                physical_type = dop['physical_type']
                
                # Some sanity checks...
                if not physical_type['base_data_type_as_mcd_data_type'].startswith('eA_'):
                    raise RuntimeError('Strange PHYSICAL-TYPE BASE-DATA-TYPE: {}'.format(physical_type['base_data_type_as_mcd_data_type']))
                
                # The member BASE-DATA-TYPE of PHYSICAL-TYPE gives the type and encoding of the physical value
                output_object['physical_base_data_type'] = physical_type['base_data_type_as_mcd_data_type'][1:]
                
                # Get the DISPLAY-RADIX (numeric representation: 2 = BIN, 8 = OCT, 10 = DEC, 16 = HEX)
                output_object['display_radix'] = physical_type['display_radix']
                if output_object['display_radix'] not in [2, 8, 10, 16]:
                    raise RuntimeError('Invalid DISPLAY-RADIX: {}'.format(output_object['display_radix']))
                
                # The DISPLAY-RADIX is only applicable to the physical data type A_UINT32
                if output_object['physical_base_data_type'] != 'A_UINT32':
                    output_object['display_radix'] = None
                
                # There is also a possibility to specify the number of digits to be displayed after the decimal point by the member PRECISION
                output_object['precision'] = physical_type['precision'] if physical_type['is_precision_available'] else None
                
                # PRECISION can be given for A_FLOAT32 and A_FLOAT64 physical data types
                if output_object['precision'] is not None and output_object['physical_base_data_type'] not in ['A_FLOAT32', 'A_FLOAT64']:
                    raise RuntimeError('PRECISION available for non-FLOAT PHYSICAL-TYPE {}: {}'.format(output_object['physical_base_data_type'], output_object['precision']))
            
            # The calculated physical value can be directly displayed on the tester
            # Usually, units are used to augment this displayed value with additional information
            # The declaration of the unit to be used is given via the reference UNIT-REF
            if 'units_ref' in dop:
                output_object['units'] = None
                if dop['units_ref'] is not None:
                    # Get the UNIT
                    units_dop = object_loader.load_object_by_reference(project_folder_path, dop['units_ref']) # MCD_DB_UNIT
                    
                    # Store the UNIT's fields
                    output_object['units'] = {}
                    output_object['units']['long_name'] = units_dop['long_name']
                    output_object['units']['long_name_id'] = units_dop['long_name_id']
                    output_object['units']['description'] = units_dop['description']
                    output_object['units']['display_name'] = units_dop['display_name']
                    output_object['units']['factor_si_to_unit'] = units_dop['factor_si_to_unit']
                    output_object['units']['offset_si_to_unit'] = units_dop['offset_si_to_unit']
                    
                    # Store the PHYSICAL-DIMENSION's fields, if specified
                    output_object['units']['si_unit'] = None
                    if units_dop['physical_dimension'] is not None:
                        output_object['units']['si_unit'] = {}
                        output_object['units']['si_unit']['length_exponent']             = units_dop['physical_dimension']['length_exponent']
                        output_object['units']['si_unit']['mass_exponent']               = units_dop['physical_dimension']['mass_exponent']
                        output_object['units']['si_unit']['time_exponent']               = units_dop['physical_dimension']['time_exponent']
                        output_object['units']['si_unit']['current_exponent']            = units_dop['physical_dimension']['current_exponent']
                        output_object['units']['si_unit']['temperature_exponent']        = units_dop['physical_dimension']['temperature_exponent']
                        output_object['units']['si_unit']['molar_amount_exponent']       = units_dop['physical_dimension']['molar_amount_exponent']
                        output_object['units']['si_unit']['luminous_intensity_exponent'] = units_dop['physical_dimension']['luminous_intensity_exponent']
            
            # The validity of the internal value can be restricted to a given interval via the INTERNAL-CONSTR and its members LOWER-LIMIT and UPPER-LIMIT
            if 'internal_constraint_ref' in dop:
                output_object['internal_constraint'] = None
                if dop['internal_constraint_ref'] is not None:
                    # Get the INTERNAL-CONSTR
                    internal_constraint = object_loader.load_object_by_reference(project_folder_path, dop['internal_constraint_ref']) # MCD_CONSTRAINT
                    
                    # Sanity check...
                    if internal_constraint['is_computed']:
                        raise RuntimeError('IC should not be computed')
                    
                    # The LIMITs' data types should match the coded data type
                    if internal_constraint['interval']['lower_limit']['data_type'] != 'e'+output_object['coded_base_data_type'] or internal_constraint['interval']['lower_limit']['data_type'] != 'e'+output_object['coded_base_data_type']:
                        raise RuntimeError('IC limit data types do not match coded type: {}, {} vs {}'.format(internal_constraint['interval']['lower_limit']['data_type'], internal_constraint['interval']['upper_limit']['data_type'], output_object['coded_base_data_type']))
                    
                    # Get the LIMITs
                    output_object['internal_constraint'] = {'lower_limit': {}, 'upper_limit': {}}
                    # LOWER-LIMIT
                    output_object['internal_constraint']['lower_limit']['type'] = internal_constraint['interval']['lower_limit_type'].replace('eLIMIT_', '')
                    output_object['internal_constraint']['lower_limit']['value'] = None if output_object['internal_constraint']['lower_limit']['type'] == 'INFINITE' else internal_constraint['interval']['lower_limit']['value']
                    # UPPER-LIMIT
                    output_object['internal_constraint']['upper_limit']['type'] = internal_constraint['interval']['upper_limit_type'].replace('eLIMIT_', '')
                    output_object['internal_constraint']['upper_limit']['value'] = None if output_object['internal_constraint']['upper_limit']['type'] == 'INFINITE' else internal_constraint['interval']['upper_limit']['value']
                    
                    # Additionally, SCALE-CONSTRS can be used to define valid, non-valid, non-defined or non-available sub-intervals within the interval spanned by INTERNAL-CONSTR
                    # The limits of the sub-intervals are defined with LOWER-LIMIT and UPPER-LIMIT in the same way as in INTERNAL-CONSTR
                    
                    # Sanity check...
                    if internal_constraint['scale_constraints'] is None:
                        raise RuntimeError('IC has no SCALE-CONSTRS')
                    
                    # Go through all SCALE-CONSTRs inside SCALE-CONSTRS
                    output_object['internal_constraint']['scale_constraints'] = []
                    for scale_constraint in internal_constraint['scale_constraints']:
                        # The LIMITs' data types should match the coded data type
                        if scale_constraint['interval']['lower_limit']['data_type'] != 'e'+output_object['coded_base_data_type'] or scale_constraint['interval']['lower_limit']['data_type'] != 'e'+output_object['coded_base_data_type']:
                            raise RuntimeError('IC SCALE-CONSTR limit data types do not match coded type: {}, {} vs {}'.format(scale_constraint['interval']['lower_limit']['data_type'], scale_constraint['interval']['upper_limit']['data_type'], output_object['coded_base_data_type']))
                        
                        # Get the LIMITs
                        scale_constraint_output_object = {'lower_limit': {}, 'upper_limit': {}}
                        # LOWER-LIMIT
                        scale_constraint_output_object['lower_limit']['type'] = scale_constraint['interval']['lower_limit_type'].replace('eLIMIT_', '')
                        scale_constraint_output_object['lower_limit']['value'] = None if scale_constraint_output_object['lower_limit']['type'] == 'INFINITE' else scale_constraint['interval']['lower_limit']['value']
                        # UPPER-LIMIT
                        scale_constraint_output_object['upper_limit']['type'] = scale_constraint['interval']['upper_limit_type'].replace('eLIMIT_', '')
                        scale_constraint_output_object['upper_limit']['value'] = None if scale_constraint_output_object['upper_limit']['type'] == 'INFINITE' else scale_constraint['interval']['upper_limit']['value']
                        
                        # The attribute VALIDITY of each SCALE-CONSTR can take the values VALID, NOT-VALID, NOT-DEFINED or NOT-AVAILABLE
                        scale_constraint_output_object['validity'] = scale_constraint['range_info'][7:].replace('_', '-')
                        
                        # Optionally, a SHORT-LABEL can be used to add an identifier to a SCALE-CONSTR
                        scale_constraint_output_object['short_label'] = scale_constraint['short_label']
                        scale_constraint_output_object['description'] = scale_constraint['description']
                        
                        # Add the SCALE-CONSTR to the list
                        output_object['internal_constraint']['scale_constraints'].append(scale_constraint_output_object)
                    
                    # The implicit valid range of a data type is defined by BASE-DATA-TYPE, restricted by ENCODING and size of parameter which is defined by the BIT-LENGTH
                    # The explicit valid range is defined by UPPER-LIMIT and LOWER-LIMIT, minus all SCALE-CONSTRs with VALIDITY != VALID
                    # If UPPER-LIMIT or LOWER-LIMIT is missing, the explicit valid range is not restricted in that direction
                    # The valid range is defined by the intersection of the implicit and the explicit valid range
                    
                    # If the DATA-OBJECT-PROP is used for calculation of physical value from the internal one, the internal value is matched against the valid range directly
            
            # In a similar way, it is possible to specify constraints for the physical value inside PHYS-CONSTR, if the physical type of the DATA-OBJECT-PROP is a numerical type
            if 'physical_constraint_ref' in dop:
                output_object['physical_constraint'] = None
                if dop['physical_constraint_ref'] is not None:
                    if output_object['physical_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64', 'A_BYTEFIELD']:
                        raise RuntimeError('PC only allowed for numerical physical types, not {}'.format(output_object['physical_base_data_type']))
                    
                    # Get the PHYS-CONSTR
                    physical_constraint = object_loader.load_object_by_reference(project_folder_path, dop['physical_constraint_ref']) # MCD_CONSTRAINT
                    
                    # Sanity check...
                    if not physical_constraint['is_computed']:
                        raise RuntimeError('PC should be computed')
                    
                    # If UPPER-LIMIT or LOWER-LIMIT is missing, the explicit valid range is not restricted in that direction
                    
                    # Get the LIMITs
                    output_object['physical_constraint'] = {'lower_limit': {}, 'upper_limit': {}}
                    # LOWER-LIMIT
                    if physical_constraint['interval']['lower_limit'] is None:
                        output_object['physical_constraint']['lower_limit']['type'] = 'INFINITE'
                        output_object['physical_constraint']['lower_limit']['value'] = None
                    else:
                        # The LOWER-LIMIT's data type should match the physical data type
                        if physical_constraint['interval']['lower_limit']['data_type'] != 'e'+output_object['physical_base_data_type']:
                            raise RuntimeError('PC LOWER-LIMIT data type does not match physical type: {} vs {}'.format(physical_constraint['interval']['lower_limit']['data_type'], output_object['physical_base_data_type']))
                        
                        output_object['physical_constraint']['lower_limit']['type'] = physical_constraint['interval']['lower_limit_type'].replace('eLIMIT_', '')
                        output_object['physical_constraint']['lower_limit']['value'] = None if output_object['physical_constraint']['lower_limit']['type'] == 'INFINITE' else physical_constraint['interval']['lower_limit']['value']
                    # UPPER-LIMIT
                    if physical_constraint['interval']['upper_limit'] is None:
                        output_object['physical_constraint']['upper_limit']['type'] = 'INFINITE'
                        output_object['physical_constraint']['upper_limit']['value'] = None
                    else:
                        # The UPPER-LIMIT's data type should match the physical data type
                        if physical_constraint['interval']['upper_limit']['data_type'] != 'e'+output_object['physical_base_data_type']:
                            raise RuntimeError('PC UPPER-LIMIT data type does not match physical type: {} vs {}'.format(physical_constraint['interval']['upper_limit']['data_type'], output_object['physical_base_data_type']))
                        
                        output_object['physical_constraint']['upper_limit']['type'] = physical_constraint['interval']['upper_limit_type'].replace('eLIMIT_', '')
                        output_object['physical_constraint']['upper_limit']['value'] = None if output_object['physical_constraint']['upper_limit']['type'] == 'INFINITE' else physical_constraint['interval']['upper_limit']['value']
                    
                    # SCALE-CONSTRS can be defined for PHYS-CONSTRs too
                    output_object['physical_constraint']['scale_constraints'] = []
                    for scale_constraint in physical_constraint['scale_constraints']:
                        # Get the LIMITs
                        scale_constraint_output_object = {'lower_limit': {}, 'upper_limit': {}}
                        # LOWER-LIMIT
                        if scale_constraint['interval']['lower_limit'] is None:
                            scale_constraint_output_object['lower_limit']['type'] = 'INFINITE'
                            scale_constraint_output_object['lower_limit']['value'] = None
                        else:
                            # The LOWER-LIMIT's data type should match the physical data type
                            if scale_constraint['interval']['lower_limit']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                raise RuntimeError('IC SCALE-CONSTR LOWER-LIMIT data type does not match coded type: {} vs {}'.format(scale_constraint['interval']['lower_limit']['data_type'], output_object['physical_base_data_type']))
                            
                            scale_constraint_output_object['lower_limit']['type'] = scale_constraint['interval']['lower_limit_type'].replace('eLIMIT_', '')
                            scale_constraint_output_object['lower_limit']['value'] = None if scale_constraint_output_object['lower_limit']['type'] == 'INFINITE' else scale_constraint['interval']['lower_limit']['value']
                        # UPPER-LIMIT
                        scale_constraint_output_object['upper_limit'] = {}
                        if scale_constraint['interval']['upper_limit'] is None:
                            scale_constraint_output_object['upper_limit']['type'] = 'INFINITE'
                            scale_constraint_output_object['upper_limit']['value'] = None
                        else:
                            # The UPPER-LIMIT's data type should match the physical data type
                            if scale_constraint['interval']['upper_limit']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                raise RuntimeError('IC SCALE-CONSTR UPPER-LIMIT data type does not match coded type: {} vs {}'.format(scale_constraint['interval']['upper_limit']['data_type'], output_object['physical_base_data_type']))
                            
                            scale_constraint_output_object['upper_limit']['type'] = scale_constraint['interval']['upper_limit_type'].replace('eLIMIT_', '')
                            scale_constraint_output_object['upper_limit']['value'] = None if scale_constraint_output_object['upper_limit']['type'] == 'INFINITE' else scale_constraint['interval']['upper_limit']['value']
                        
                        # The attribute VALIDITY of each SCALE-CONSTR can take the values VALID, NOT-VALID, NOT-DEFINED or NOT-AVAILABLE
                        scale_constraint_output_object['validity'] = scale_constraint['range_info'][7:].replace('_', '-')
                        
                        # Optionally, a SHORT-LABEL can be used to add an identifier to a SCALE-CONSTR
                        scale_constraint_output_object['short_label'] = scale_constraint['short_label']
                        scale_constraint_output_object['description'] = scale_constraint['description']
                        
                        # Add the SCALE-CONSTR to the list
                        output_object['physical_constraint']['scale_constraints'].append(scale_constraint_output_object)
                    
                    # The implicit valid range is not restricted by the size or encoding of the data type, only by the general restriction given by the BASE-DATA-TYPE
                    
                    # If the DATA-OBJECT-PROP is used for calculation of physical value from the internal one, the physical value is matched against the valid physical range after applying the conversion method
            
            # Computational methods (COMPU-METHOD) are needed to calculate between the internal (coded) type and the physical type of the diagnostic values
            if 'compu_method' in dop:
                # A COMPU-METHOD can specify a COMPU-INTERNAL-TO-PHYS and/or a COMPU-PHYS-TO-INTERNAL element, which specifies the transformation
                # of a coded value read out of the PDU into a physical value of a type compliant to the DOP-BASE this COMPU-METHOD belongs to
                compu_method = dop['compu_method']
                
                # Get the COMPU-METHOD's CATEGORY (type)
                compu_category = compu_method['compu_category']
                
                # For all COMPU-METHODs, except those of categories IDENTICAL, TEXTTABLE and COMPUCODE, the calculation type (float or integer) is deduced from the type of the internal and physical values
                # It has a decisive influence on the precision of the calculation
                output_object['calculation_type'] = None
                if compu_category not in ['eIDENTICAL', 'eTEXTTABLE']:
                    # In any other case, the calculation is of type A_INT32
                    output_object['calculation_type'] = 'A_INT32'
                    
                    # If one of the types (physical or internal) is A_FLOAT32 or A_FLOAT64, the calculation is of type A_FLOAT64
                    if output_object['coded_base_data_type'] in ['A_FLOAT32', 'A_FLOAT64'] or output_object['physical_base_data_type'] in ['A_FLOAT32', 'A_FLOAT64']:
                        output_object['calculation_type'] = 'A_FLOAT64'
                    
                    # If both types are A_UINT32, the calculation is of type A_UINT32
                    if output_object['coded_base_data_type'] == 'A_UINT32' and output_object['physical_base_data_type'] == 'A_UINT32':
                        output_object['calculation_type'] = 'A_UINT32'
                
                # Computational methods: MCD-2D V2.2 - 7.3.6.6
                match compu_category:
                    # The internal value and the physical value are identical
                    case 'eIDENTICAL':
                        output_object['compu_category'] = 'IDENTICAL'
                        
                        # For COMPU-METHODs of this type, the data objects COMPU-INTERNAL-TO-PHYS and COMPU-PHYS-TO-INTERNAL are not allowed
                        if compu_method['compu_internal_to_phys'] is not None or compu_method['compu_phys_to_internal'] is not None:
                            raise RuntimeError('COMPU-INTERNAL-TO-PHYS and COMPU-PHYS-TO-INTERNAL are not allowed for COMPU-METHOD of type IDENTICAL')
                    
                    # The input value is multiplied by a factor and an offset is added, optionally the sum is then divided by an unsigned integer
                    case 'eLINEAR':
                        output_object['compu_category'] = 'LINEAR'
                        
                        # Exactly one COMPU-SCALE must be defined
                        if len(compu_method['compu_internal_to_phys']['compu_scales']) != 1:
                            raise RuntimeError('Exactly one COMPU-SCALE must be defined, not {}'.format(len(compu_method['compu_internal_to_phys']['compu_scales'])))
                        
                        # Get the only COMPU-SCALE
                        compu_scale = compu_method['compu_internal_to_phys']['compu_scales'][0]
                        
                        # It contains COMPU-RATIONAL-COEFFS, within which COMPU-NUMERATOR and COMPU-DENOMINATOR are declared
                        compu_rational_coeffs = compu_scale['compu_rational_coeffs']
                        compu_numerator = compu_rational_coeffs['numerator']
                        compu_denominator = compu_rational_coeffs['denominator']
                            
                        # The numerator should contain two values
                        if len(compu_numerator) == 2:
                            # The first one is the offset (VN0), the second one is the factor (VN1)
                            offset = compu_numerator[0]
                            factor = compu_numerator[1]
                        # If it contains one value, use the default factor
                        elif len(compu_numerator) == 1:
                            offset = compu_numerator[0]
                            factor = 1
                        # If it contains no values, use the default offset and factor
                        elif len(compu_numerator) == 0:
                            offset = 0
                            factor = 1
                        else:
                            raise RuntimeError('Unexpected amount of values in numerator: {}'.format(len(compu_numerator)))
                        
                        # If the denominator is present, it shall specify exactly one unsigned integer value
                        if len(compu_denominator) not in [0, 1]:
                            raise RuntimeError('The denominator should contain zero or one values; contains: {}'.format(len(compu_denominator)))
                        
                        # If the COMPU-DENOMINATOR is not specified, the numerical value 1 is assumed for the denominator
                        divisor = 1 if len(compu_denominator) == 0 else compu_denominator[0]
                        
                        # The LIMITs at COMPU-SCALE can be used to restrict the value domain
                        compu_scale_output_object = {'coded_lower_limit': {}, 'coded_upper_limit': {}, 'physical_lower_limit': {}, 'physical_upper_limit': {}}
                        # Coded LOWER-LIMIT
                        if compu_scale['lower_limit_as_coded_value'] is None:
                            compu_scale_output_object['coded_lower_limit']['type'] = 'INFINITE'
                            compu_scale_output_object['coded_lower_limit']['value'] = None
                        else:
                            compu_scale_output_object['coded_lower_limit']['type'] = compu_scale['lower_limit_as_coded_value']['limit_type'].replace('eLIMIT_', '')
                            if compu_scale_output_object['coded_lower_limit']['type'] == 'INFINITE':
                                compu_scale_output_object['coded_lower_limit']['value'] = None
                            else:
                                compu_scale_output_object['coded_lower_limit']['value'] = compu_scale['lower_limit_as_coded_value']['mcd_value']['value']
                                if compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                    raise RuntimeError('COMPU-SCALE coded LOWER-LIMIT data type does not match coded type: {} vs {}'.format(compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'], output_object['coded_base_data_type']))
                        # Coded UPPER-LIMIT
                        if compu_scale['upper_limit_as_coded_value'] is None:
                            compu_scale_output_object['coded_upper_limit']['type'] = 'INFINITE'
                            compu_scale_output_object['coded_upper_limit']['value'] = None
                        else:
                            compu_scale_output_object['coded_upper_limit']['type'] = compu_scale['upper_limit_as_coded_value']['limit_type'].replace('eLIMIT_', '')
                            if compu_scale_output_object['coded_upper_limit']['type'] == 'INFINITE':
                                compu_scale_output_object['coded_upper_limit']['value'] = None
                            else:
                                compu_scale_output_object['coded_upper_limit']['value'] = compu_scale['upper_limit_as_coded_value']['mcd_value']['value']
                                if compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                    raise RuntimeError('COMPU-SCALE coded UPPER-LIMIT data type does not match coded type: {} vs {}'.format(compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'], output_object['coded_base_data_type']))
                        # Physical LOWER-LIMIT
                        if compu_scale['lower_limit'] is None:
                            compu_scale_output_object['physical_lower_limit']['type'] = 'INFINITE'
                            compu_scale_output_object['physical_lower_limit']['value'] = None
                        else:
                            compu_scale_output_object['physical_lower_limit']['type'] = compu_scale['lower_limit']['limit_type'].replace('eLIMIT_', '')
                            if compu_scale_output_object['physical_lower_limit']['type'] == 'INFINITE':
                                compu_scale_output_object['physical_lower_limit']['value'] = None
                            else:
                                compu_scale_output_object['physical_lower_limit']['value'] = compu_scale['lower_limit']['mcd_value']['value']
                                if compu_scale['lower_limit']['mcd_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                    raise RuntimeError('COMPU-SCALE physical LOWER-LIMIT data type does not match physical type: {} vs {}'.format(compu_scale['lower_limit']['mcd_value']['data_type'], output_object['physical_base_data_type']))
                        # Physical UPPER-LIMIT
                        if compu_scale['upper_limit'] is None:
                            compu_scale_output_object['physical_upper_limit']['type'] = 'INFINITE'
                            compu_scale_output_object['physical_upper_limit']['value'] = None
                        else:
                            compu_scale_output_object['physical_upper_limit']['type'] = compu_scale['upper_limit']['limit_type'].replace('eLIMIT_', '')
                            if compu_scale_output_object['physical_upper_limit']['type'] == 'INFINITE':
                                compu_scale_output_object['physical_upper_limit']['value'] = None
                            else:
                                compu_scale_output_object['physical_upper_limit']['value'] = compu_scale['upper_limit']['mcd_value']['value']
                                if compu_scale['upper_limit']['mcd_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                    raise RuntimeError('COMPU-SCALE physical UPPER-LIMIT data type does not match physical type: {} vs {}'.format(compu_scale['upper_limit']['mcd_value']['data_type'], output_object['physical_base_data_type']))
                        
                        # Generate the mathematical expression (linear function) of the COMPU-SCALE
                        compu_scale_output_object['formula'] = '({} + (x * {})) / {}'.format(offset, factor, divisor)
                        
                        # Store the COMPU-SCALE
                        output_object['compu_scale'] = compu_scale_output_object
                        
                        # Check possible data types
                        if output_object['coded_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Coded BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['coded_base_data_type']))
                        if output_object['physical_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Physical BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['physical_base_data_type']))
                    
                    # Same as LINEAR, but multiple COMPU-SCALES (intervals) can be defined, each with its own formula
                    case 'eSCALE_LINEAR':
                        output_object['compu_category'] = 'SCALE-LINEAR'
                        
                        # At least one COMPU-SCALE must be defined
                        if len(compu_method['compu_internal_to_phys']['compu_scales']) < 1:
                            raise RuntimeError('At least one COMPU-SCALE must be defined, not {}'.format(len(compu_method['compu_internal_to_phys']['compu_scales'])))
                        
                        # Go through each COMPU-SCALE
                        output_object['compu_scales'] = []
                        for compu_scale in compu_method['compu_internal_to_phys']['compu_scales']:
                            # A COMPU-SCALE contains COMPU-RATIONAL-COEFFS, within which COMPU-NUMERATOR and COMPU-DENOMINATOR are declared
                            compu_rational_coeffs = compu_scale['compu_rational_coeffs']
                            compu_numerator = compu_rational_coeffs['numerator']
                            compu_denominator = compu_rational_coeffs['denominator']
                            
                            # The numerator should contain two values
                            if len(compu_numerator) == 2:
                                # The first one is the offset (VN0), the second one is the factor (VN1)
                                offset = compu_numerator[0]
                                factor = compu_numerator[1]
                            # If it contains one value, that is the offset, use the default factor
                            elif len(compu_numerator) == 1:
                                offset = compu_numerator[0]
                                factor = 1
                            # If it contains no values, use the default offset and factor
                            elif len(compu_numerator) == 0:
                                offset = 0
                                factor = 1
                            else:
                                raise RuntimeError('Unexpected amount of values in numerator: {}'.format(len(compu_numerator)))
                            
                            # If the denominator is present, it shall specify exactly one unsigned integer value
                            if len(compu_denominator) not in [0, 1]:
                                raise RuntimeError('The denominator should contain zero or one values; contains: {}'.format(len(compu_denominator)))
                            
                            # If the COMPU-DENOMINATOR is not specified, the numerical value 1 is assumed for the denominator
                            divisor = 1 if len(compu_denominator) == 0 else compu_denominator[0]
                        
                            # The LIMITs at COMPU-SCALE can be used to restrict the value domain
                            compu_scale_output_object = {'coded_lower_limit': {}, 'coded_upper_limit': {}, 'physical_lower_limit': {}, 'physical_upper_limit': {}}
                            # Coded LOWER-LIMIT
                            if compu_scale['lower_limit_as_coded_value'] is None:
                                compu_scale_output_object['coded_lower_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['coded_lower_limit']['value'] = None
                            else:
                                compu_scale_output_object['coded_lower_limit']['type'] = compu_scale['lower_limit_as_coded_value']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['coded_lower_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['coded_lower_limit']['value'] = None
                                else:
                                    compu_scale_output_object['coded_lower_limit']['value'] = compu_scale['lower_limit_as_coded_value']['mcd_value']['value']
                                    if compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE coded LOWER-LIMIT data type does not match coded type: {} vs {}'.format(compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'], output_object['coded_base_data_type']))
                            # Coded UPPER-LIMIT
                            if compu_scale['upper_limit_as_coded_value'] is None:
                                compu_scale_output_object['coded_upper_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['coded_upper_limit']['value'] = None
                            else:
                                compu_scale_output_object['coded_upper_limit']['type'] = compu_scale['upper_limit_as_coded_value']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['coded_upper_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['coded_upper_limit']['value'] = None
                                else:
                                    compu_scale_output_object['coded_upper_limit']['value'] = compu_scale['upper_limit_as_coded_value']['mcd_value']['value']
                                    if compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE coded UPPER-LIMIT data type does not match coded type: {} vs {}'.format(compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'], output_object['coded_base_data_type']))
                            # Physical LOWER-LIMIT
                            if compu_scale['lower_limit'] is None:
                                compu_scale_output_object['physical_lower_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['physical_lower_limit']['value'] = None
                            else:
                                compu_scale_output_object['physical_lower_limit']['type'] = compu_scale['lower_limit']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['physical_lower_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['physical_lower_limit']['value'] = None
                                else:
                                    compu_scale_output_object['physical_lower_limit']['value'] = compu_scale['lower_limit']['mcd_value']['value']
                                    if compu_scale['lower_limit']['mcd_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE physical LOWER-LIMIT data type does not match physical type: {} vs {}'.format(compu_scale['lower_limit']['mcd_value']['data_type'], output_object['physical_base_data_type']))
                            # Physical UPPER-LIMIT
                            if compu_scale['upper_limit'] is None:
                                compu_scale_output_object['physical_upper_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['physical_upper_limit']['value'] = None
                            else:
                                compu_scale_output_object['physical_upper_limit']['type'] = compu_scale['upper_limit']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['physical_upper_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['physical_upper_limit']['value'] = None
                                else:
                                    compu_scale_output_object['physical_upper_limit']['value'] = compu_scale['upper_limit']['mcd_value']['value']
                                    if compu_scale['upper_limit']['mcd_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE physical UPPER-LIMIT data type does not match physical type: {} vs {}'.format(compu_scale['upper_limit']['mcd_value']['data_type'], output_object['physical_base_data_type']))
                            
                            # Generate the mathematical expression (linear function) of the COMPU-SCALE
                            compu_scale_output_object['formula'] = '({} + (x * {})) / {}'.format(offset, factor, divisor)
                            
                            # Add the COMPU-SCALE to the list
                            output_object['compu_scales'].append(compu_scale_output_object)
                        
                        # The category SCALE-LINEAR may define an optionally default scale, COMPU-DEFAULT-VALUE
                        output_object['compu_default_value'] = None
                        if compu_method['compu_internal_to_phys']['compu_default_value'] is not None:
                            output_object['compu_default_value'] = compu_method['compu_internal_to_phys']['compu_default_value']['value']
                            
                            # The COMPU-DEFAULT-VALUE's data type seems to be Unicode string...?
                            if compu_method['compu_internal_to_phys']['compu_default_value']['data_type'] != 'eA_UNICODE2STRING':
                                raise RuntimeError('COMPU-DEFAULT-VALUE ({}) data type is not A_UNICODE2STRING: {}'.format(compu_method['compu_internal_to_phys']['compu_default_value']['data_type']))
                        
                        # Check possible data types
                        if output_object['coded_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Coded BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['coded_base_data_type']))
                        if output_object['physical_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Physical BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['physical_base_data_type']))
                    
                    # A rational function (numerator and denominator are polynomials) can be defined for multiple disjunctive intervals
                    case 'eSCALE_RAT_FUNC':
                        output_object['compu_category'] = 'SCALE-RAT-FUNC'
                        
                        # At least one COMPU-SCALE must be defined
                        if len(compu_method['compu_internal_to_phys']['compu_scales']) < 1:
                            raise RuntimeError('At least one COMPU-SCALE must be defined, not {}'.format(len(compu_method['compu_internal_to_phys']['compu_scales'])))
                        
                        # Go through each COMPU-SCALE
                        output_object['compu_scales'] = []
                        for compu_scale in compu_method['compu_internal_to_phys']['compu_scales']:
                            # A COMPU-SCALE contains COMPU-RATIONAL-COEFFS, within which COMPU-NUMERATOR and COMPU-DENOMINATOR are declared
                            compu_rational_coeffs = compu_scale['compu_rational_coeffs']
                            compu_numerator = compu_rational_coeffs['numerator']
                            compu_denominator = compu_rational_coeffs['denominator']
                            
                            # The LIMITs at COMPU-SCALE can be used to restrict the value domain
                            compu_scale_output_object = {'coded_lower_limit': {}, 'coded_upper_limit': {}, 'physical_lower_limit': {}, 'physical_upper_limit': {}}
                            # Coded LOWER-LIMIT
                            if compu_scale['lower_limit_as_coded_value'] is None:
                                compu_scale_output_object['coded_lower_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['coded_lower_limit']['value'] = None
                            else:
                                compu_scale_output_object['coded_lower_limit']['type'] = compu_scale['lower_limit_as_coded_value']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['coded_lower_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['coded_lower_limit']['value'] = None
                                else:
                                    compu_scale_output_object['coded_lower_limit']['value'] = compu_scale['lower_limit_as_coded_value']['mcd_value']['value']
                                    if compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE coded LOWER-LIMIT data type does not match coded type: {} vs {}'.format(compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'], output_object['coded_base_data_type']))
                            # Coded UPPER-LIMIT
                            if compu_scale['upper_limit_as_coded_value'] is None:
                                compu_scale_output_object['coded_upper_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['coded_upper_limit']['value'] = None
                            else:
                                compu_scale_output_object['coded_upper_limit']['type'] = compu_scale['upper_limit_as_coded_value']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['coded_upper_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['coded_upper_limit']['value'] = None
                                else:
                                    compu_scale_output_object['coded_upper_limit']['value'] = compu_scale['upper_limit_as_coded_value']['mcd_value']['value']
                                    if compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE coded UPPER-LIMIT data type does not match coded type: {} vs {}'.format(compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'], output_object['coded_base_data_type']))
                            # Physical LOWER-LIMIT
                            if compu_scale['lower_limit'] is None:
                                compu_scale_output_object['physical_lower_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['physical_lower_limit']['value'] = None
                            else:
                                compu_scale_output_object['physical_lower_limit']['type'] = compu_scale['lower_limit']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['physical_lower_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['physical_lower_limit']['value'] = None
                                else:
                                    compu_scale_output_object['physical_lower_limit']['value'] = compu_scale['lower_limit']['mcd_value']['value']
                                    if compu_scale['lower_limit']['mcd_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE physical LOWER-LIMIT data type does not match physical type: {} vs {}'.format(compu_scale['lower_limit']['mcd_value']['data_type'], output_object['physical_base_data_type']))
                            # Physical UPPER-LIMIT
                            if compu_scale['upper_limit'] is None:
                                compu_scale_output_object['physical_upper_limit']['type'] = 'INFINITE'
                                compu_scale_output_object['physical_upper_limit']['value'] = None
                            else:
                                compu_scale_output_object['physical_upper_limit']['type'] = compu_scale['upper_limit']['limit_type'].replace('eLIMIT_', '')
                                if compu_scale_output_object['physical_upper_limit']['type'] == 'INFINITE':
                                    compu_scale_output_object['physical_upper_limit']['value'] = None
                                else:
                                    compu_scale_output_object['physical_upper_limit']['value'] = compu_scale['upper_limit']['mcd_value']['value']
                                    if compu_scale['upper_limit']['mcd_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                        raise RuntimeError('COMPU-SCALE physical UPPER-LIMIT data type does not match physical type: {} vs {}'.format(compu_scale['upper_limit']['mcd_value']['data_type'], output_object['physical_base_data_type']))
                            
                            # Generate the mathematical expression (linear function) of the COMPU-SCALE
                            numerator = polynomial_to_string(compu_numerator)
                            denominator = polynomial_to_string(compu_denominator)
                            compu_scale_output_object['formula'] = '({}) / ({})'.format(numerator, denominator)
                            
                            # Do not allow division by zero
                            if denominator == '0':
                                raise RuntimeError('Denominator is 0')
                            
                            # Add the COMPU-SCALE to the list
                            output_object['compu_scales'].append(compu_scale_output_object)
                        
                        # The category SCALE-RAT-FUNC may define an optionally default scale, COMPU-DEFAULT-VALUE
                        output_object['compu_default_value'] = None
                        if compu_method['compu_internal_to_phys']['compu_default_value'] is not None:
                            output_object['compu_default_value'] = compu_method['compu_internal_to_phys']['compu_default_value']['value']
                            
                            # The COMPU-DEFAULT-VALUE's data type seems to be Unicode string...?
                            if compu_method['compu_internal_to_phys']['compu_default_value']['data_type'] != 'eA_UNICODE2STRING':
                                raise RuntimeError('COMPU-DEFAULT-VALUE ({}) data type is not A_UNICODE2STRING: {}'.format(compu_method['compu_internal_to_phys']['compu_default_value']['data_type']))
                        
                        # Check possible data types
                        if output_object['coded_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Coded BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['coded_base_data_type']))
                        if output_object['physical_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Physical BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['physical_base_data_type']))
                    
                    # The internal value is transformed into a textual expression
                    case 'eTEXTTAB':
                        output_object['compu_category'] = 'TEXTTABLE'
                        
                        # At least one COMPU-SCALE must be defined
                        if len(compu_method['compu_internal_to_phys']['compu_scales']) < 1:
                            raise RuntimeError('At least one COMPU-SCALE must be defined for TEXTTABLE; defined: {}'.format(len(compu_method['compu_internal_to_phys']['compu_scales'])))
                        
                        # In each COMPU-SCALE, LOWER-LIMIT and UPPER-LIMIT define an interval
                        output_object['compu_scales'] = []
                        for compu_scale in compu_method['compu_internal_to_phys']['compu_scales']:
                            # Only the coded LIMITs matter, since the physical LIMITs will both contain the same string as in the COMPU-CONST
                            compu_scale_output_object = {}
                            
                            # Both LIMITs should be CLOSED
                            if compu_scale['lower_limit_as_coded_value']['limit_type'] != 'eLIMIT_CLOSED' or compu_scale['upper_limit_as_coded_value']['limit_type'] != 'eLIMIT_CLOSED':
                                raise RuntimeError('Unexpected LOWER/UPPER-LIMIT types: {}, {}'.format(compu_scale['lower_limit_as_coded_value']['limit_type'], compu_scale['upper_limit_as_coded_value']['limit_type']))
                            
                            # Both LIMITs' data types must match the coded data type
                            if compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type'] or compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                raise RuntimeError('Data types of coded LOWER/UPPER-LIMIT {}, {} do not match coded data type {}'.format(compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'], compu_scale['upper_limit_as_coded_value']['mcd_value']['data_type'], compu_scale_output_object['coded_base_data_type']))
                            
                            # Get the LIMITs
                            compu_scale_output_object['lower_limit'] = compu_scale['lower_limit_as_coded_value']['mcd_value']['value']
                            compu_scale_output_object['upper_limit'] = compu_scale['upper_limit_as_coded_value']['mcd_value']['value']
                            
                            # If the internal data type is a string type, the definition of a range is not allowed
                            # If the element UPPER-LIMIT is explicitly specified, its content shall be equal to the content of LOWER-LIMIT
                            if output_object['coded_base_data_type'] in ['A_ASCIISTRING', 'A_UNICODE2STRING']:
                                if compu_scale_output_object['lower_limit'] != compu_scale_output_object['upper_limit']:
                                    raise RuntimeError('UPPER-LIMIT does not match LOWER-LIMIT for TEXTTABLE with string coded data type: {} vs {}'.format(compu_scale_output_object['lower_limit'], compu_scale_output_object['upper_limit']))
                            
                            # COMPU-CONST defines the resulting text for the appropriate interval
                            compu_scale_output_object['long_name'] = compu_scale['compu_const']['value']
                            
                            # The LONG-NAME-ID of the COMPU-SCALE belongs to the text
                            compu_scale_output_object['long_name_id'] = compu_scale['long_name_id']
                            
                            # The COMPU-CONST's data type must match the physical data type
                            if compu_scale['compu_const']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                raise RuntimeError('COMPU-CONST data type does not match physical type: {} vs {}'.format(compu_scale['compu_const']['data_type'], output_object['physical_base_data_type']))
                            
                            # Add the COMPU-SCALE to the list
                            output_object['compu_scales'].append(compu_scale_output_object)
                        
                        # The optional COMPU-DEFAULT-VALUE can be used to define the physical value if the internal value does not lie in any given interval
                        output_object['compu_default_value'] = None
                        if compu_method['compu_internal_to_phys']['compu_default_value'] is not None:
                            output_object['compu_default_value'] = compu_method['compu_internal_to_phys']['compu_default_value']['value']
                            
                            # The COMPU-DEFAULT-VALUE's data type must match the physical data type
                            if compu_method['compu_internal_to_phys']['compu_default_value']['data_type'] != 'e'+output_object['physical_base_data_type']:
                                raise RuntimeError('COMPU-DEFAULT-VALUE data type does not match physical type: {} vs {}'.format(compu_method['compu_internal_to_phys']['compu_default_value']['data_type'], output_object['physical_base_data_type']))
                        
                        # Check possible data types
                        if output_object['coded_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64', 'A_ASCIISTRING', 'A_UTF8STRING', 'A_BYTEFIELD', 'A_UNICODE2STRING']:
                            raise RuntimeError('Coded BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['coded_base_data_type']))
                        if output_object['physical_base_data_type'] not in ['A_UNICODE2STRING']:
                            raise RuntimeError('Physical BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['physical_base_data_type']))
                    
                    case 'eTAB_INTP':
                        # A COMPU-METHOD of CATEGORY TAB-INTP defines a set of points with linear interploaton between them
                        output_object['compu_category'] = 'TAB-INTP'
                        
                        # The category TAB-INTP must specify at least two COMPU-SCALEs
                        if len(compu_method['compu_internal_to_phys']['compu_scales']) < 2:
                            raise RuntimeError('TAB-INTP must specify at least 2 COMPU-SCALEs, not {}'.format(len(compu_method['compu_internal_to_phys']['compu_scales'])))
                        
                        # Get the COMPU-SCALEs
                        output_object['compu_scales'] = []
                        for compu_scale in compu_method['compu_internal_to_phys']['compu_scales']:
                            # Each COMPU-SCALE will define only a singular value, not an interval
                            # LOWER-LIMIT contains the singular value and UPPER-LIMIT shall not be present
                            # ... Actually, UPPER-LIMIT is present but we shall ignore it
                            compu_scale_output_object = {}
                            
                            # The (LOWER-)LIMIT's data type must match the coded BASE-DATA-TYPE
                            if compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type'] != 'e'+output_object['coded_base_data_type']:
                                raise RuntimeError('LOWER-LIMIT data type for COMPU-SCALE of TAB-INTP must be {}, not {}'.format(output_object['coded_base_data_type'], compu_scale['lower_limit_as_coded_value']['mcd_value']['data_type']))
                            
                            # The (LOWER-)LIMIT's type must be CLOSED
                            if compu_scale['lower_limit_as_coded_value']['limit_type'] != 'eLIMIT_CLOSED':
                                raise RuntimeError('LOWER-LIMIT type for COMPU-SCALE of TAB-INTP must be CLOSED, not {}'.format(compu_scale['lower_limit_as_coded_value']['limit_type']))
                            
                            # Get the (LOWER-)LIMIT
                            compu_scale_output_object['limit'] = compu_scale['lower_limit_as_coded_value']['mcd_value']['value']
                            
                            # Like with MUX, the data type seems to be Unicode string, even though it contains a number...
                            if compu_scale['compu_const']['data_type'] != 'eA_UNICODE2STRING':
                                raise RuntimeError('COMPU-CONST is not string: {}'.format(compu_scale['compu_const']['data_type']))
                            
                            # Calculation of the physical value is done by linear interpolation for the interval specified by the values inside COMPU-CONST
                            compu_scale_output_object['compu_const'] = compu_scale['compu_const']['value']
                            
                            # Add the COMPU-SCALE to the list
                            output_object['compu_scales'].append(compu_scale_output_object)
                        
                        # Check possible data types
                        if output_object['coded_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Coded BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['coded_base_data_type']))
                        if output_object['physical_base_data_type'] not in ['A_INT32', 'A_UINT32', 'A_FLOAT32', 'A_FLOAT64']:
                            raise RuntimeError('Physical BASE-DATA-TYPE {} not allowed for LINEAR'.format(output_object['physical_base_data_type']))
                    
                    case _:
                        object_printer.print_indented(0, '') 
                        object_printer.print_object(compu_method, 'compu_method', 0)
                        object_printer.print_indented(0, '')
                        raise RuntimeError('Unknown compu_category: {}'.format(compu_category))
        
        # Structure: MCD-2D V2.2 - 7.3.6.10.2
        case 'MCD_DB_PARAMETER_STRUCTURE':
            # A STRUCTURE is some kind of wrapper to enable recursion, that combines several PARAMs into a group of parameters belonging together
            # Each PARAM represents an item which is a member of the group built by this STRUCTURE
            output_object['type'] = 'STRUCTURE'
            
            # Get the STRUCTURE's LONG-NAME and DESCRIPTION
            output_object['long_name'] = dop['long_name']
            output_object['description'] = dop['description']
            
            # The optional attribute BYTE-SIZE gives the size of the whole structure in bytes
            # If the STRUCTURE has any dynamic components (e.g. MUX, or any FIELD with dynamic length), the BYTE-SIZE should not be given
            output_object['byte_size'] = dop['byte_size'] if dop['byte_size'] != 0 else None
            
            # Add each PARAM of the STRUCTURE to a list
            output_object['parameters'] = []
            for parameter in dop['parameters']:
                output_object['parameters'].append(parse_dop(object_loader, layer_data_objects, project_folder_path, parameter))
        
        # Static field: MCD-2D V2.2 - 7.3.6.10.3
        case 'MCD_DB_PARAMETER_STATIC_FIELD':
            # STATIC-FIELDs are used when the PDU contains a recurring structure and the number of repetitions is fixed and does not have to be determined dynamically
            # In other words, a STATIC-FIELD is used to describe a repetition of a BASIC-STRUCTURE or ENV-DATA-DESC with an "a priori" fixed number of repetitions
            output_object['type'] = 'STATIC-FIELD'
            
            # The number of repetitions is given via the attribute FIXED-NUMBER-OF-ITEMS
            output_object['fixed_number_of_items'] = dop['fixed_number_of_items']
            
            # The first item starts at the same byte position as the STATIC-FIELD
            # For each further item, the byte position is increased by ITEM-BYTE-SIZE, which determines the length of one item in the field
            output_object['item_byte_size'] = dop['item_byte_size']
            
            # The reference to the BASIC-STRUCTURE defines the complex DOP to be repeatedly applied
            struct_dop = object_loader.load_object_by_reference(project_folder_path, dop['structure_ref']) # MCD_DB_PARAMETER_STRUCTURE
            if struct_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
                raise RuntimeError('Object is not BASIC-STRUCTURE: {}'.format(struct_dop['#OBJECT_TYPE']))
            output_object['structure'] = parse_dop(object_loader, layer_data_objects, project_folder_path, struct_dop)
        
        # Dynamic length field: MCD-2D V2.2 - 7.3.6.10.4
        case 'MCD_DB_PARAMETER_DYNAMIC_LENGTH_FIELD':
            # DYNAMIC-LENGTH-FIELDs are fields of items (BASIC-STRUCTURE) with variable number of repetitions, which can be determined only at runtime
            output_object['type'] = 'DYNAMIC-LENGTH-FIELD'
            
            # The determination of the number of repetitions is described by DETERMINE-NUMBER-OF-ITEMS
            # The DATA-OBJECT-PROP referenced to is used to calculate the repetition number
            determine_number_of_items_dop = object_loader.load_object_by_reference(project_folder_path, dop['determine_number_of_items_dop_ref']) # DB_DOP_SIMPLE_BASE
            output_object['determine_number_of_items'] = parse_dop(object_loader, layer_data_objects, project_folder_path, determine_number_of_items_dop)
            
            # The repetition number is contained in its physical value of type A_UINT32
            if output_object['determine_number_of_items']['physical_base_data_type'] != 'A_UINT32':
                raise RuntimeError('Invalid data type for DETERMINE-NUMBER-OF-ITEMS DOP: {}'.format(output_object['determine_number_of_items']['physical_base_data_type']))
            
            # Its BYTE-POSITION is relative to that of the DYNAMIC-LENGTH-FIELD
            # The optional BIT-POSITION shall be between 0 and 7
            output_object['determine_number_of_items']['byte_position'] = dop['determine_number_of_items_byte_position']
            output_object['determine_number_of_items']['bit_position'] = dop['determine_number_of_items_bit_position']
            if output_object['determine_number_of_items']['bit_position'] not in range(0, 8):
                raise RuntimeError('BIT-POSITION {} not between 0-7'.format(output_object['determine_number_of_items']['bit_position']))
            
            # For the first item, the byte position is given by OFFSET relatively to the byte position of the DYNAMIC-LENGTH-FIELD
            output_object['offset'] = dop['first_item_offset']
            # Each further item starts at the byte edge following the item before
            
            # The reference to the BASIC-STRUCTURE defines the COMPLEX-DOP to be repeatedly applied
            struct_dop = object_loader.load_object_by_reference(project_folder_path, dop['structure_ref']) # MCD_DB_PARAMETER_STRUCTURE
            if struct_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
                raise RuntimeError('Object is not BASIC-STRUCTURE: {}'.format(struct_dop['#OBJECT_TYPE']))
            output_object['structure'] = parse_dop(object_loader, layer_data_objects, project_folder_path, struct_dop)
        
        # Dynamic Endmarker Field: MCD-2D V2.2 - 7.3.6.10.5
        case 'MCD_DB_PARAMETER_DYNAMIC_ENDMARKER_FIELD':
            # DYNAMIC-ENDMARKER-FIELDs are fields of items (BASIC-STRUCTUREs) which are repeated until an end-marker is found (the TERMINATION-VALUE)
            # They are also terminated by the end of the PDU
            output_object['type'] = 'DYNAMIC-ENDMARKER-FIELD'
            
            # Before each iteration step, the end of PDU condition is tested
            # If the end of PDU is reached, then the processing of the iteration stops immediately
            # Otherwise, the referenced DATA-OBJECT-PROP is used to calculate a physical value of the parameter at the current position in the PDU
            determine_termination_parameter_dop = object_loader.load_object_by_reference(project_folder_path, dop['dop_base_ref']) # DB_DOP_SIMPLE_BASE
            output_object['determine_termination_parameter'] = parse_dop(object_loader, layer_data_objects, project_folder_path, determine_termination_parameter_dop)
            
            # If the resulting physical value matches the TERMINATION-VALUE (inside DATA-OBJECT-PROP-REF), the field ends without any additional item
            # Therefore, the value inside the TERMINATION-VALUE shall be given in the physical type of this referenced DATA-OBJECT-PROP
            output_object['termination_value'] = dop['termination_value']
            
            # For the first item, the byte position is given by the byte position of the DYNAMIC-ENDMARKER-FIELD
            # Each further item starts at the byte edge following the item before
            
            # The bytes defined by the ENDMARKER are not considered to be consumed
            # A parameter without BYTE-POSITION defined after the ENDMARKER-FIELD starts directly after the last structure of the field
            # If the interpretation of the ENDMARKER bytes is not desired, they can be skipped with a RESERVED parameter
            
            # The reference to the BASIC-STRUCTURE defines the complex DOP to be repeatedly applied
            struct_dop = object_loader.load_object_by_reference(project_folder_path, dop['structure_ref']) # MCD_DB_PARAMETER_STRUCTURE
            if struct_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
                raise RuntimeError('Object is not BASIC-STRUCTURE: {}'.format(struct_dop['#OBJECT_TYPE']))
            output_object['structure'] = parse_dop(object_loader, layer_data_objects, project_folder_path, struct_dop)
        
        # End of PDU field: MCD-2D V2.2 - 7.3.6.10.6
        case 'MCD_DB_PARAMETER_END_OF_PDU_FIELD':
            # END-OF-PDU-FIELDs are similar to DYNAMIC-ENDMARKER-FIELDs, with the difference that the item is always repeated until the end of the PDU
            output_object['type'] = 'END-OF-PDU-FIELD'
            
            # For the first item, the byte position is given by the BYTE-POSITION of the END-OF-PDU-FIELD
            # Each further item starts at the byte edge following the item before
            
            # The reference to the BASIC-STRUCTURE defines the COMPLEX-DOP to be repeatedly applied
            struct_dop = object_loader.load_object_by_reference(project_folder_path, dop['structure_ref']) # MCD_DB_PARAMETER_STRUCTURE
            if struct_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
                raise RuntimeError('Object is not BASIC-STRUCTURE: {}'.format(struct_dop['#OBJECT_TYPE']))
            output_object['structure'] = parse_dop(object_loader, layer_data_objects, project_folder_path, struct_dop)
        
        # Multiplexer: MCD-2D V2.2 - 7.3.6.10.7
        case 'MCD_DB_PARAMETER_MULTIPLEXER':
            # MUXes are used to interpret data stream depending on the value of a switch-key (similar to match-case statements)
            output_object['type'] = 'MUX'
            
            # Get the MUX's BYTE-POSITION
            output_object['byte_position'] = dop['byte_position']
            
            # The determination of the actual switch-key is described inside SWITCH-KEY
            # The DATA-OBJECT-PROP referenced to is used to calculate the switch-key, which is contained in its physical value
            switch_key_dop = object_loader.load_object_by_reference(project_folder_path, dop['switch_key']['dop_base_ref']) # DB_DOP_SIMPLE_BASE
            output_object['switch_key'] = parse_dop(object_loader, layer_data_objects, project_folder_path, switch_key_dop)
            
            # Its BYTE-POSITION is relative to the that of the MUX
            output_object['switch_key']['byte_position'] = dop['switch_key']['byte_position']
            
            # The DIAG-CODED-TYPE of that DATA-OBJECT-PROP shall be of type STANDARD-LENGTH-TYPE
            if output_object['switch_key']['diag_coded_type'] != 'STANDARD-LENGTH-TYPE':
                raise RuntimeError('Invalid DIAG-CODED-TYPE for SWITCH-KEY DOP: {}'.format(output_object['switch_key']['diag_coded_type']))
            
            # The optional BIT-POSITION shall be between 0 and 7
            output_object['switch_key']['bit_position'] = dop['switch_key']['bit_position']
            if output_object['switch_key']['bit_position'] not in range(0, 8):
                raise RuntimeError('BIT-POSITION {} not between 0-7'.format(output_object['switch_key']['bit_position']))
            
            # Any number of CASEs can be specified
            output_object['cases'] = []
            for case in dop['cases']:
                # Get the CASE's LONG-NAME and DESCRIPTION (not many have one)
                case_output_object = {}
                case_output_object['long_name'] = case['long_name']
                case_output_object['description'] = case['description']
                
                # Each CASE defines a LOWER-LIMIT and an UPPER-LIMIT
                
                # The limit types should both be CLOSED
                if case['lower_limit']['limit_type'] != 'eLIMIT_CLOSED' or case['upper_limit']['limit_type'] != 'eLIMIT_CLOSED':
                    raise RuntimeError('SWITCH-CASE uknown limit types: {}, {}'.format(case['lower_limit']['limit_type'], case['upper_limit']['limit_type']))
                
                # Both limits should be Unicode strings, pretty strange...
                if case['lower_limit']['mcd_value']['data_type'] != 'eA_UNICODE2STRING' or case['upper_limit']['mcd_value']['data_type'] != 'eA_UNICODE2STRING':
                    raise RuntimeError('SWITCH-CASE limits are not strings: {}, {}'.format(case['lower_limit']['mcd_value']['data_type'], case['upper_limit']['mcd_value']['data_type']))
                
                # Get the LOWER-LIMIT and UPPER-LIMIT of the CASE
                case_output_object['lower_limit'] = case['lower_limit']['mcd_value']['value']
                case_output_object['upper_limit'] = case['upper_limit']['mcd_value']['value']
                
                # If a matching CASE is found, the referenced STRUCTURE is analyzed at the BYTE-POSITION (child element of MUX), relatively to the byte position of the MUX
                
                # Add the referenced STRUCTURE's fields to the CASE object
                struct_dop = object_loader.load_object_by_reference(project_folder_path, case['structure_dop_ref']) # MCD_DB_PARAMETER_STRUCTURE
                if struct_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
                    raise RuntimeError('Object is not BASIC-STRUCTURE: {}'.format(struct_dop['#OBJECT_TYPE']))
                case_output_object['structure'] = parse_dop(object_loader, layer_data_objects, project_folder_path, struct_dop)
                
                # Add the CASE to the list of CASES
                output_object['cases'].append(case_output_object)
            
            # If a MUX object has no CASES sub-object then it shall have a DEFAULT-CASE sub-object
            # If a matching CASE cannot be found and the optional DEFAULT-CASE is specified, then the STRUCTURE referenced by this DEFAULT-CASE is analyzed in the same way
            output_object['default_case'] = None
            if dop['default_case'] is not None and dop['default_case']['structure_dop_ref'] is not None:
                # Get the DEFAULT-CASE's LONG-NAME
                output_object['default_case'] = {}
                output_object['default_case']['long_name'] = dop['default_case']['long_name']
                
                # 
                if dop['default_case']['description'] is not None:
                    raise RuntimeError('DEFAULT-CASE has DESCRIPTION: {}'.format(dop['default_case']['description']))
                
                # Add the referenced STRUCTURE's fields to the DEFAULT-CASE object
                struct_dop = object_loader.load_object_by_reference(project_folder_path, dop['default_case']['structure_dop_ref']) # MCD_DB_PARAMETER_STRUCTURE
                if struct_dop['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
                    raise RuntimeError('Object is not BASIC-STRUCTURE: {}'.format(struct_dop['#OBJECT_TYPE']))
                output_object['default_case']['structure'] = parse_dop(object_loader, layer_data_objects, project_folder_path, struct_dop)
        
        # Some MWBs are able to include a DTC as one of the parameters in their structure
        case 'DB_DOP_DTC':
            output_object['type'] = 'DTC'
            
            # Sanity checks...
            diag_coded_type = dop['diag_coded_type']
            physical_type = dop['physical_type']
            compu_method = dop['compu_method']
            if diag_coded_type['type'] != 'eSTANDARD_LENGTH_TYPE':
                raise RuntimeError('DTC DIAG-CODED-TYPE must be STANDARD-LENGTH-TYPE, not {}').format(diag_coded_type['type'])
            if diag_coded_type['bit_length'] != 24:
                raise RuntimeError('DTC BIT-LENGTH must be 24, not {}'.format(diag_coded_type['bit_length']))
            if diag_coded_type['bit_mask'] != bytearray():
                raise RuntimeError('DTC must have no BIT-MASK, has {}'.format(diag_coded_type['bit_mask']))
            if diag_coded_type['encoding'] != 'eNONE':
                raise RuntimeError('DTC ENCODING must be NONE, not {}'.format(diag_coded_type['encoding']))
            if diag_coded_type['is_high_low_byte_order'] != True:
                raise RuntimeError('DTC IS-HIGH-LOW-BYTE-ORDER must be True')
            if diag_coded_type['base_data_type_as_mcd_data_type'] != 'eA_UINT32':
                raise RuntimeError('DTC coded BASE-DATA-TYPE must be A_UINT32, not {}'.format(diag_coded_type['base_data_type_as_mcd_data_type']))
            if physical_type['base_data_type_as_mcd_data_type'] != 'eA_UINT32':
                raise RuntimeError('DTC physical BASE-DATA-TYPE must be A_UINT32, not {}'.format(physical_type['base_data_type_as_mcd_data_type']))
            if compu_method['compu_category'] != 'eIDENTICAL':
                raise RuntimeError('DTC COMPU-METHOD CATEGORY must be IDENTICAL, not {}'.format(compu_method['compu_category']))
            
            # Get the SHORT-NAME and LONG-NAME
            output_object['short_name'] = dop['short_name']
            output_object['long_name'] = dop['long_name']
            
            # DTC-DOPs are very similar to simple DOPs, the following fields are copied to make parsing similar too
            output_object['coded_base_data_type'] = 'A_UINT32'
            output_object['diag_coded_type'] = 'STANDARD-LENGTH-TYPE'
            output_object['bit_length'] = 24
            output_object['bit_mask'] = None
            output_object['encoding'] = 'NONE'
            output_object['endianness'] = 'big'
            output_object['physical_base_data_type'] = 'A_UINT32'
            output_object['display_radix'] = 16
            output_object['precision'] = None
            output_object['units'] = None
            output_object['internal_constraint'] = None
            output_object['physical_constraint'] = None
            output_object['compu_category'] = 'IDENTICAL'
            
            # The object contains 'diag_trouble_codes_map', which correlates the received code with the actual DTC
            output_object['dtc_list'] = []
            for map_item in dop['diag_trouble_codes_ref_map']:
                dtc_output_object = {}
                
                # Load the reference to the DTC definition
                dtc = object_loader.load_object_by_reference(project_folder_path, map_item['reference']) # MCD_DB_DIAG_TROUBLE_CODE
                if dtc['#OBJECT_TYPE'] != 'MCD_DB_DIAG_TROUBLE_CODE':
                    raise RuntimeError('Object is not DTC: {}'.format(dtc['#OBJECT_TYPE']))
                
                # The 'trouble code' refers to the value returned by the ECU
                dtc_output_object['trouble_code'] = dtc['trouble_code']
                
                # The referenced DTC's trouble code must match the map key
                if dtc['trouble_code'] != map_item['map_key']:
                    raise 'Trouble code {:X} does not match map key {:X}'.format(dtc['trouble_code'], map_item['map_key'])
                
                dtc_output_object['label'] = dtc['label']
                dtc_output_object['short_name'] = dtc['short_name']
                
                dtc_output_object['dtc'] = dtc['trouble_code_text']
                
                dtc_output_object['description'] = dtc['description']
                dtc_output_object['level'] = dtc['level']
                
                output_object['dtc_list'].append(dtc_output_object)
        
        case _:
            object_printer.print_indented(0, '') 
            object_printer.print_object(dop, 'dop', 0)
            object_printer.print_indented(0, '')
            raise RuntimeError('Unknown DOP type: {}'.format(dop['#OBJECT_TYPE']))
    
    return output_object


def get_ecu_variant_map(base_variant_project_data):
    # Return None for BASE-VARIANTs which do not have ECU-VARIANTs defined
    if len(base_variant_project_data['ecu_variant_ref_collection']) == 0:
        return None
    
    ecu_variant_map = {}
    
    # Go through each ECU-VARIANT referenced by the BASE-VARIANT
    for ecu_variant_ref in base_variant_project_data['ecu_variant_ref_collection']:
        ecu_variant_map[ecu_variant_ref['name']] = ecu_variant_ref['reference']
    
    return ecu_variant_map


def get_ecu_variant_layer_data(object_loader, project_folder_path, ecu_variant_reference):
    (ecu_variant_PoolID, ecu_variant_ObjectID) = ObjectLoader.decode_object_reference(ecu_variant_reference)
    
    ecu_variant = object_loader.load_object_by_id(project_folder_path, ecu_variant_PoolID, ecu_variant_ObjectID)
    
    ecu_variant_layer_data_ObjectID = ecu_variant['ecu']['location_refs'][0]['reference']['access_key']['layer_data_object_id']
    
    return object_loader.load_object_by_id(project_folder_path, ecu_variant_PoolID, ecu_variant_layer_data_ObjectID)


def get_mwb_map(object_loader, project_folder_path, ecu_variant_layer_data):
    # Search for the DIAG-COMM reference with name 'DiagnServi_ReadDataByIdentMeasuValue' (might not exist)
    diag_com_ref_RDBI = None
    for diag_com_ref in ecu_variant_layer_data['diag_com_refs']:
        if diag_com_ref['map_key'] == 'DiagnServi_ReadDataByIdentMeasuValue':
            diag_com_ref_RDBI = diag_com_ref
            break
    
    # Return None for ECU-VARIANTs which do not have the MWB service defined
    if diag_com_ref_RDBI is None:
        return None
            
    # Load the DIAG-SERVICE object from its reference
    rdbi_service = object_loader.load_object_by_reference(project_folder_path, diag_com_ref_RDBI['reference']['attrib_obj_ref'])
    
    # The service should only have one positve response referenced
    if len(rdbi_service['data_primitive']['diag_com_primitive']['positive_response_ref_collection']) != 1:
        raise RuntimeError('RDBI service has multiple positive responses')
    
    # Load the positive response from its reference in the service
    response = object_loader.load_object_by_reference(project_folder_path, rdbi_service['data_primitive']['diag_com_primitive']['positive_response_ref_collection'][0]['reference'])
    
    # The response parameter with SHORT-NAME 'Param_DataRecor' must be loaded
    # It might be the third or fourth response parameter
    
    # Search for the response parameter with SHORT-NAME 'Param_DataRecor'
    data_record_response_parameter = None
    for response_parameter in response['response_parameters']:
        if response_parameter['short_name'] == 'Param_DataRecor':
            data_record_response_parameter = response_parameter
            break
    
    # The response parameter must have been found
    if data_record_response_parameter is None:
        raise RuntimeError('Could not find Param_DataRecor response parameter')
    
    # Load the table of the response parameter from its reference
    response_parameter_table = object_loader.load_object_by_reference(project_folder_path, data_record_response_parameter['table_ref'])
    
    # Load the DOP from its reference, whose COMPU-SCALEs contain the correlation between RDBI DIDs and measurement names
    did_table = object_loader.load_object_by_reference(project_folder_path, response_parameter_table['dop_simple_ref'])
    
    mwb_map = {}
    for compu_scale in did_table['compu_method']['compu_internal_to_phys']['compu_scales']:
        mwb_map[compu_scale['compu_const_as_coded_value']['value']] = {'long_name': compu_scale['compu_const']['value'], 'long_name_id': compu_scale['long_name_id']}
    
    return (mwb_map, response_parameter_table)


def get_mwb_table(response_parameter_table):
    # Return the map of the table's keys as a dictionary in which the MWB's LONG-NAME resolves to the table row's reference
    return {item['map_key']: item['reference'] for item in response_parameter_table['table_key_map']}


def get_mwb_table_parameter(object_loader, project_folder_path, mwb_table, mwb_table_key, mwb_long_name_to_did_map):
    # Normally, the key for the DID map is the measurement's long name directly
    # There seems to be a problem in the file for some BCM modules, where the key appears with spaces but it should have contained underscores (even MCD Kernel complains)
    mwb_long_name = mwb_table_key
    
    map_key = mwb_long_name
    try:
        # Try the normal key, then apply the workaround if it fails
        mwb_long_name_to_did_map[map_key]
    except KeyError:
        map_key = map_key.replace(' ', '_')
        
        # If that key doesn't work either, just return None
        try:
            mwb_long_name_to_did_map[map_key]
        except KeyError:
            return None
                    
    # Correlate the measurement's name with its DID and LONG-NAME-ID
    mwb_did = mwb_long_name_to_did_map[map_key]['did']
    mwb_long_name_id = mwb_long_name_to_did_map[map_key]['long_name_id']
    
    # Load the measurement's table row by its reference
    mwb_table_row = object_loader.load_object_by_reference(project_folder_path, mwb_table[mwb_table_key])
    
    # The table row must contain the same key it had in the map
    if mwb_table_row['key'] != mwb_long_name:
        raise RuntimeError('Wrong key in table row: {} vs {}'.format(mwb_table_row['key'], mwb_long_name))
    
    return (mwb_did, mwb_long_name, mwb_long_name_id, mwb_table_row['parameter'])


def parse_mwb_table_row_parameter(mwb_table_row_parameter):
    # Some sanity checks...
    if mwb_table_row_parameter['default_mcd_value'] is not None:
        raise RuntimeError('Table row parameter has default')
    if mwb_table_row_parameter['sys_param'] is not None:
        raise RuntimeError('Table row parameter has sys param')
    if mwb_table_row_parameter['mcd_parameter_type'] != 'eVALUE':
        raise RuntimeError('Wrong parameter type for table row parameter: {}'.format(mwb_table_row_parameter['mcd_parameter_type']))
    
    return (mwb_table_row_parameter['long_name'], mwb_table_row_parameter['description'], mwb_table_row_parameter['byte_position'], mwb_table_row_parameter['bit_position'])


def get_mwb_name_and_table_row_parameter_by_did(object_loader, project_folder_path, mwb_table, mwb_map, desired_did):
    # mwb_map: keyed by DID, resolves to {long_name, long_name_id}
    mwb_long_name_and_id = mwb_map[desired_did]
    mwb_long_name = mwb_long_name_and_id['long_name']
    mwb_long_name_id = mwb_long_name_and_id['long_name_id']
    
    # mwb_table: keyed by long_name, resolves to reference to row
    # Normally, the key for the DID map is the measurement's long name directly
    # There seems to be a problem in the file for some BCM modules, where the key appears with spaces but it should have contained underscores (even MCD Kernel complains)
    mwb_table_key = mwb_long_name
    try:
        # Try the normal key, then apply the workaround if it fails
        mwb_table[mwb_table_key]
    except KeyError:
        mwb_table_key = mwb_table_key.replace('_', ' ')
        
        # If that key doesn't work either, just return None
        try:
            mwb_table[mwb_table_key]
        except KeyError:
            return None
    
    mwb_table_row_reference = mwb_table[mwb_table_key]
    
    # Load the measurement's table row by its reference
    mwb_table_row = object_loader.load_object_by_reference(project_folder_path, mwb_table_row_reference)
    
    # The table row must contain the same key it had in the map
    if mwb_table_row['key'] != mwb_table_key:
        raise RuntimeError('Wrong key in table row: {} vs {}'.format(mwb_table_row['key'], mwb_table_key))
    
    return (mwb_long_name, mwb_long_name_id, mwb_table_row['parameter'])


def get_mwb_structure(object_loader, project_folder_path, mwb_table_row_parameter):
    # Load the parameter's associated DOP by its reference (which should be a structure, type MCD_DB_PARAMETER_STRUCTURE)
    mwb_structure = object_loader.load_object_by_reference(project_folder_path, mwb_table_row_parameter['db_object_ref'])
    if mwb_structure['#OBJECT_TYPE'] != 'MCD_DB_PARAMETER_STRUCTURE':
        raise RuntimeError('Wrong data type for parameter structure: {}'.format(mwb_structure['#OBJECT_TYPE']))
    return mwb_structure


def dump_mwbs_for_base_variant(object_loader, protocol_layer_data_list, project_folder_path, base_variant_filename, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
        
        # The MWBs will be dumped into a file named like the ECU-VARIANT
        # The .c extension is only used for highlighting and block folding in a code editor
        ecu_variant_output_file_path = os.path.join(base_variant_output_folder_path, 'MWB_' + ecu_variant_name + '.c')
        
        # Only dump the MWBs if the file doesn't already exist (or if overwriting is allowed)
        if not overwrite and (os.path.exists(ecu_variant_output_file_path) and os.path.isfile(ecu_variant_output_file_path)):
            object_printer.print_indented(debug_info_indentation_level + 1, 'Already done, skipping')
        else:
            # The layer data will be needed for getting a list of all MWBs and also for solving some references
            
            # If parsing the BASE-VARIANT, its layer data was retrieved previously
            if ecu_variant_name == base_variant_name:
                ecu_variant_layer_data = base_variant_layer_data
            # Otherwise, retrieve the ECU-VARIANT's layer data
            else:
                ecu_variant_layer_data = get_ecu_variant_layer_data(object_loader, project_folder_path, ecu_variant_map[ecu_variant_name])
            
            # Get a map of all available MWBs = Measuring Value(s / Blocks)
            mwb_map_result = get_mwb_map(object_loader, project_folder_path, ecu_variant_layer_data)
            
            # Skip ECU-VARIANTs which do not have the MWB service defined (no file will be created)
            if mwb_map_result is None:
                object_printer.print_indented(debug_info_indentation_level + 1, 'Has no MWBs')
                continue
            
            # In the response parameter table, the methods for decoding responses are keyed by the measurement's name
            (mwb_map, response_parameter_table) = mwb_map_result
            
            # Create the BASE-VARIANT's output folder if it doesn't exist
            if not os.path.isdir(base_variant_output_folder_path):
                os.makedirs(base_variant_output_folder_path)
            
            # Open the output file and dump the MWBs
            with open(ecu_variant_output_file_path, 'w', encoding='utf-8') as ecu_variant_output_file:
                # Back to the 'Param_DataRecor' response parameter's table, go through the entries in the key map
                # Each one has a reference to the table row with the specified LONG-NAME
                mwb_table = get_mwb_table(response_parameter_table)
                for mwb_did in mwb_map:
                    # Get the definition for the current DID
                    result = get_mwb_name_and_table_row_parameter_by_did(object_loader, project_folder_path, mwb_table, mwb_map, mwb_did)
                    if result is None:
                        raise RuntimeError('Failed to find MWB table row')
                    
                    # Decode the table row
                    mwb_long_name, mwb_long_name_id, mwb_table_row_parameter = result
                    
                    # Parse the parameter
                    mwb_table_row_parameter_long_name, mwb_description, mwb_byte_position, mwb_bit_position = parse_mwb_table_row_parameter(mwb_table_row_parameter)
                    
                    # Get the object of type 'STRUCTURE'
                    mwb_structure = get_mwb_structure(object_loader, project_folder_path, mwb_table_row_parameter)
                    
                    # These objects will be used (in this order) for solving references which don't specify a PoolID
                    layer_data_objects = [ecu_variant_layer_data, base_variant_layer_data] + protocol_layer_data_list
                    
                    # Parse the structure
                    parsed_mwb_structure = parse_dop(object_loader, layer_data_objects, project_folder_path, mwb_structure)
                    if parsed_mwb_structure['type'] != 'STRUCTURE':
                        raise RuntimeError('MWB base DOP shoud be STRUCTURE, not {}'.format(parsed_mwb_structure['type']))
                    
                    # Create an object (dictionary) with the fields retrieved from the table row and the parameter structure
                    obj = {
                        'did': mwb_did,
                        'long_name': mwb_long_name,
                        'long_name_id': mwb_long_name_id,
                        'description': mwb_description,
                        'byte_position': mwb_byte_position,
                        'bit_position': mwb_bit_position,
                        'structure': parsed_mwb_structure
                    }
                    
                    # Dump to the output file
                    object_printer.print_object(obj, '0x{:04X}: {} - {}'.format(mwb_did, mwb_long_name_id, mwb_long_name), 0, ecu_variant_output_file, False)
                    object_printer.print_indented(0, '', ecu_variant_output_file)


def dump_mwbs_for_all_base_variants_in_project(object_loader, protocol_layer_data, project_folder_path, output_folder_path, overwrite = False, debug_info_indentation_level = 0):
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
        
        # Dump the MWBs with the other function
        dump_mwbs_for_base_variant(object_loader, protocol_layer_data, project_folder_path, PoolID, output_folder_path, overwrite, debug_info_indentation_level + 1)


def dump_mwbs_for_all_base_variants_in_all_projects(project_folder_path, output_folder_path, debug_info_indentation_level = 0):
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
        
        # Dump the MWBs for each ECU-VARIANT in each BASE-VARIANT with the other function
        dump_mwbs_for_all_base_variants_in_project(object_loader, protocol_layer_data_list, project_path, project_output_folder_path, False, debug_info_indentation_level + 1)


def dumpMWB_basevariant(project_folder_path, base_variant_filename, output_folder_path):
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
    dump_mwbs_for_base_variant(object_loader, protocol_layer_data_list, project_folder_path, base_variant_filename, project_output_folder_path, True)


def dumpMWB_project(project_folder_path, output_folder_path):
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
        dump_mwbs_for_all_base_variants_in_project(object_loader, protocol_layer_data_list, project_folder_path, project_output_folder_path)
    except:
        print('Error:\n{}'.format(traceback.format_exc()))
    
    # Get the elapsed time and split it into hours, minutes, seconds
    elapsed_seconds = time.time() - start_time
    (hours, remainder) = divmod(elapsed_seconds, 3600)
    (minutes, seconds) = divmod(remainder, 60)
    
    # Display the time taken by the script to run
    print('\nElapsed: {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


def dumpMWB_projects(projects_folder_path, output_folder_path):
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
        dump_mwbs_for_all_base_variants_in_all_projects(projects_folder_path, output_folder_path)
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
    parser = argparse.ArgumentParser(description='Dump MWB (measured value blocks) definitions')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # All MWBs from all ECU-VARIANTs in a BASE-VARIANT of a project
    parser_basevariant = subparsers.add_parser('basevariant', help='Dump MWBs for all ECU-VARIANTs in a BASE-VARIANT')
    parser_basevariant.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_basevariant.add_argument('base_variant_filename', help='Filename of BASE-VARIANT (.bv.db file)')
    parser_basevariant.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and BASE-VARIANT')
    parser_basevariant.set_defaults(func=dumpMWB_basevariant)
    
    # All MWBs from all ECU-VARIANTs in all BASE-VARIANTs of a project
    parser_project = subparsers.add_parser('project', help='Dump MWBs for all ECU-VARIANTs in all BASE-VARIANTs of a project')
    parser_project.add_argument('project_folder_path', help='MCD project (folder containing .db and .key files)')
    parser_project.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for the project and each BASE-VARIANT')
    parser_project.set_defaults(func=dumpMWB_project)
    
    # All MWBs from all ECU-VARIANTs in all BASE-VARIANTs of all projects
    parser_all_projects = subparsers.add_parser('projects', help='Dump MWBs for all ECU-VARIANTs in all BASE-VARIANTs of all projects')
    parser_all_projects.add_argument('projects_folder_path', help='MCD projects (folder containing folders containing .db and .key files)')
    parser_all_projects.add_argument('output_folder_path', help='Path of folder where to write the dump files, in a separate folder for each project')
    parser_all_projects.set_defaults(func=dumpMWB_projects)
    
    # Parse the provided arguments and call the appropriate function based on the command
    args = parser.parse_args()
    filtered_args = {k: v for k, v in vars(args).items() if k not in ('func', 'command')}
    args.func(**filtered_args)
