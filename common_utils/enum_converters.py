object_types = {
  0x0000: 'DB_UNKNOWN',
  0x0002: 'DB_KEY_VECTOR',
  0x0003: 'DB_CASE',
  0x0004: 'DB_CASES',
  0x0005: 'DB_COMPU_BASE',
  0x0006: 'DB_COMPU_INTERNAL_TO_PHYS',
  0x0007: 'DB_PROT_PARAM_DATA',
  0x000A: 'DB_COMPU_METHOD',
  0x000F: 'DB_COMPU_PHYS_TO_INTERNAL',
  0x0014: 'DB_COMPU_RATIONAL_COEFFS',
  0x0019: 'DB_COMPU_SCALE',
  0x001E: 'DB_COMPU_SCALES',
  0x0020: 'DB_DEFAULT_CASE',
  0x0021: 'DB_ECU_CONFIG_INFO',
  0x0023: 'DB_DIAG_CODED_TYPE',
  0x0027: 'DB_DOP_BASE',
  0x0028: 'DB_DOP_DTC',
  0x0029: 'DB_DOP_STRUCT',
  0x002C: 'DB_DOP_SIMPLE_BASE',
  0x002D: 'DB_ECU_VARIANT_PATTERN',
  0x002E: 'DB_ECU_VARIANT_PATTERNS',
  0x002F: 'DB_ENV_DATA',
  0x0030: 'DB_ENV_DATA_REF_SET',
  0x0031: 'DB_LAYER_DATA',
  0x0032: 'DB_INTERNAL_CONSTRAINT',
  0x0033: 'DB_PROJECT_DATA',
  0x0034: 'DB_VEHICLE_INFO_DATA',
  0x0037: 'DB_LIMIT',
  0x0038: 'DB_MATCHING_PARAMETER',
  0x0039: 'DB_MATCHING_PARAMETERS',
  0x003C: 'DB_PHYSICAL_TYPE',
  0x0041: 'MCD_DB_CODE_INFORMATION',
  0x0042: 'MCD_DB_CODE_INFORMATIONS',
  0x0046: 'DB_RELATED_SERVICES',
  0x0048: 'DB_SCALE_CONSTRAINT',
  0x0049: 'DB_SCALE_CONSTRAINTS',
  0x004A: 'DB_SERVICE_PROTOCOL_PARAMETER',
  0x004B: 'DB_SERVICE_PROTOCOL_PARAMETERS',
  0x004C: 'DB_SWITCH_KEY',
  0x004D: 'MCD_ACCESS_KEY',
  0x004E: 'MCD_DB_ACCESS_LEVEL',
  0x004F: 'MCD_DB_CONTROL_PRIMITIVES',
  0x0050: 'MCD_DB_CONTROL_PRIMITIVE_REFERENCES',
  0x0051: 'MCD_DB_DATA_PRIMITIVES',
  0x0052: 'MCD_DB_DATA_PRIMITIVE_REFERENCES',
  0x0053: 'MCD_DB_DIAG_COM_PRIMITIVES',
  0x0054: 'MCD_DB_DIAG_COM_PRIMITIVE_REFERENCES',
  0x0055: 'MCD_DB_DIAG_SERVICES',
  0x0056: 'MCD_DB_DIAG_SERVICE_REFERENCES',
  0x0057: 'MCD_DB_DIAG_TROUBLE_CODE',
  0x0058: 'MCD_DB_DIAG_TROUBLE_CODES',
  0x0059: 'MCD_DB_DIAG_TROUBLE_CODE_REFERENCES',
  0x005A: 'MCD_DB_ECU_BASE_VARIANT',
  0x005B: 'MCD_DB_ECU_BASE_VARIANTS',
  0x005C: 'MCD_DB_ECU_VARIANT',
  0x005D: 'MCD_DB_ECU_VARIANTS',
  0x005E: 'MCD_DB_FUNCTIONAL_CLASS',
  0x005F: 'MCD_DB_FUNCTIONAL_CLASSES',
  0x0060: 'MCD_DB_FUNCTIONAL_CLASS_REFERENCES',
  0x0061: 'MCD_DB_FUNCTIONAL_GROUPS',
  0x0062: 'MCD_DB_HELP_SERVICE_REFERENCES',
  0x0063: 'MCD_DB_INPUT_PARAM',
  0x0064: 'MCD_DB_JOB',
  0x0065: 'MCD_DB_JOB_REFERENCES',
  0x0066: 'MCD_DB_JOBS',
  0x0067: 'MCD_DB_LOCATION',
  0x0068: 'MCD_DB_LOCATION_REFERENCES',
  0x0069: 'MCD_DB_LOCATIONS',
  0x006A: 'MCD_DB_LOGICAL_LINK',
  0x006B: 'MCD_DB_LOGICAL_LINKS',
  0x006C: 'MCD_DB_LOGICAL_LINK_REFERENCES',
  0x006D: 'MCD_DB_PARAMETERS',
  0x006E: 'MCD_DB_PHYSICAL_VEHICLE_LINK_OR_INTERFACE',
  0x006F: 'MCD_DB_PHYSICAL_VEHICLE_LINK_OR_INTERFACES',
  0x0071: 'MCD_DB_PROJECT',
  0x0072: 'MCD_DB_PROTOCOL_PARAMETER',
  0x0073: 'MCD_DB_PROTOCOL_PARAMETER_SET',
  0x0078: 'MCD_DB_REQUEST',
  0x0079: 'MCD_DB_REQUEST_PARAMETERS',
  0x0091: 'MCD_DB_RESPONSE',
  0x0092: 'MCD_DB_RESPONSE_PARAMETERS',
  0x0093: 'MCD_DB_PARAMETER_DYNAMIC_ENDMARKER_FIELD',
  0x0094: 'MCD_DB_PARAMETER_DYNAMIC_LENGTH_FIELD',
  0x0095: 'MCD_DB_PARAMETER_END_OF_PDU_FIELD',
  0x0096: 'MCD_DB_PARAMETER_ENV_DATA_DESC',
  0x0097: 'MCD_DB_PARAMETER_ENV_DATA',
  0x00A0: 'MCD_DB_PARAMETER_MULTIPLEXER',
  0x00A1: 'MCD_DB_PARAMETER_REFERENCES',
  0x00A4: 'MCD_DB_PARAMETER',
  0x00A5: 'MCD_DB_PARAMETER_SIMPLE',
  0x00A6: 'MCD_DB_PARAMETER_STATIC_FIELD',
  0x00A7: 'MCD_DB_MATCHING_REQUEST_PARAMETER',
  0x00A8: 'MCD_DB_PARAMETER_STRUCT_FIELD',
  0x00AA: 'MCD_DB_PARAMETER_STRUCTURE',
  0x00AB: 'MCD_DB_TABLE',
  0x00AC: 'MCD_DB_TABLE_PARAMETER',
  0x00AD: 'MCD_DB_TABLE_PARAMETERS',
  0x00B0: 'MCD_DB_PARAMETER_TABLESTRUCT',
  0x00B1: 'MCD_DB_PARAMETER_TABLE_ENTRY',
  0x00B2: 'MCD_DB_PARAMETER_TABLE_KEY',
  0x00B9: 'MCD_DB_RESPONSES',
  0x00BE: 'MCD_DB_SERVICE',
  0x00BF: 'MCD_DB_SINGLE_ECU_JOB',
  0x00C3: 'MCD_DB_SERVICES',
  0x00C8: 'MCD_DB_SERVICE_REFERENCES',
  0x00C9: 'MCD_DB_VEHICLE_CONNECTOR',
  0x00D0: 'MCD_DB_VEHICLE_CONNECTORS',
  0x00D1: 'MCD_DB_VEHICLE_CONNECTOR_PIN',
  0x00D2: 'MCD_DB_VEHICLE_CONNECTOR_PINS',
  0x00D3: 'MCD_DB_VEHICLE_CONNECTOR_PIN_REFERENCES',
  0x00D4: 'MCD_DB_VEHICLE_INFORMATION',
  0x00D5: 'MCD_DB_VEHICLE_INFORMATIONS',
  0x00D6: 'MCD_DB_ECU_VARIANT_REFERENCES',
  0x00D7: 'MCD_DB_ECU_BASE_VARIANT_REFERENCES',
  0x00D8: 'MCD_DB_VEHICLE_INFORMATION_REFERENCES',
  0x00E0: 'MCD_DB_ECU_MEM',
  0x00E1: 'MCD_DB_ECU_MEMS',
  0x00E2: 'MCD_DB_FLASH_CHECKSUM',
  0x00E3: 'MCD_DB_FLASH_CHECKSUMS',
  0x00E4: 'MCD_DB_FLASH_DATA_BLOCK',
  0x00E5: 'MCD_DB_FLASH_DATA_BLOCKS',
  0x00E6: 'MCD_DB_FLASH_DATA',
  0x00E7: 'MCD_DB_FLASH_FILTER',
  0x00E8: 'MCD_DB_FLASH_FILTERS',
  0x00E9: 'MCD_DB_FLASH_IDENT',
  0x00EA: 'MCD_DB_FLASH_IDENTS',
  0x00EB: 'MCD_DB_FLASH_SECURITY',
  0x00EC: 'MCD_DB_FLASH_SECURITIES',
  0x00ED: 'MCD_DB_FLASH_SEGMENT',
  0x00EE: 'MCD_DB_FLASH_SEGMENTS',
  0x00EF: 'MCD_DB_FLASH_SESSION_CLASS',
  0x00F0: 'MCD_DB_FLASH_SESSION_CLASSES',
  0x00F1: 'MCD_DB_FLASH_SESSION',
  0x00F2: 'MCD_DB_FLASH_SESSIONS',
  0x00F3: 'MCD_DB_PHYSICAL_SEGMENT',
  0x00F4: 'MCD_DB_PHYSICAL_SEGMENTS',
  0x00F5: 'MCD_DB_PHYSICAL_MEMORY',
  0x00F6: 'MCD_DB_PHYSICAL_MEMORIES',
  0x00F8: 'MCD_DB_FLASH_JOB',
  0x00F9: 'MCD_DB_IDENT_DESCRIPTION',
  0x00FA: 'MCD_VALUES',
  0x00FB: 'MCD_INTERVAL',
  0x00FC: 'MCD_ACCESS_KEYS',
  0x00FD: 'MCD_DB_FUNCTIONAL_GROUP',
  0x00FE: 'MCD_TEXT_TABLE_ELEMENT',
  0x00FF: 'MCD_TEXT_TABLE_ELEMENTS',
  0x0100: 'MCD_DB_DIAG_VARIABLE',
  0x0101: 'MCD_DB_DIAG_VARIABLES',
  0x0102: 'MCD_DB_UNIT',
  0x0103: 'MCD_DB_UNITS',
  0x0104: 'MCD_DB_UNIT_GROUP',
  0x0105: 'MCD_DB_UNIT_GROUPS',
  0x0106: 'MCD_DB_DATA_PRIMITIVE',
  0x0107: 'MCD_DB_STARTCOMMUNICATION',
  0x0108: 'MCD_DB_STOPCOMMUNICATION',
  0x0109: 'MCD_DB_VARIANTIDENTIFICATION',
  0x010A: 'MCD_DB_VARIANTIDENTIFICATIONANDSELECTION',
  0x010B: 'MCD_DB_PROTOCOLPARAMETERSET',
  0x010C: 'MCD_DB_PHYSICAL_DIMENSION',
  0x010D: 'MCD_DB_ECU',
  0x010E: 'MCD_DB_FUNCTIONAL_GROUP_REFERENCES',
  0x010F: 'MCD_DB_SPECIAL_DATA_GROUPS',
  0x0110: 'MCD_DB_SPECIAL_DATA_GROUP',
  0x0111: 'MCD_DB_SPECIAL_DATA_ELEMENT',
  0x0112: 'MCD_DB_DYN_ID_DEFINE_COM_PRIMITIVE',
  0x0113: 'MCD_DB_DYN_ID_READ_COM_PRIMITIVE',
  0x0114: 'MCD_DB_DYN_ID_CLEAR_COM_PRIMITIVE',
  0x0115: 'MCD_AUDIENCE',
  0x0116: 'MCD_DB_MULTIPLE_ECU_JOB',
  0x0119: 'MCD_DB_TABLES',
  0x011D: 'MCD_DB_TABLE_REFERENCES',
  0x0120: 'MCD_DB_ECU_MEM_REFERENCES',
  0x0121: 'MCD_DB_UNIT_REFERENCES',
  0x0122: 'MCD_DB_FLASH_SESSION_CLASS_REFERENCES',
  0x0123: 'MCD_DB_FLASH_SESSION_REFERENCES',
  0x0124: 'MCD_DB_HEX_SERVICE',
  0x0126: 'MCD_DB_TABLE_PARAMETER_REFERENCES',
  0x0127: 'MCD_DB_PHYSICAL_MEMORY_REFERENCES',
  0x0128: 'MCD_DB_UNIT_GROUP_REFERENCES',
  0x0180: 'MCD_DB_CONFIGURATION_DATA',
  0x0181: 'MCD_DB_CONFIGURATION_DATAS',
  0x0182: 'MCD_DB_CONFIGURATION_DATA_REFERENCES',
  0x0183: 'MCD_DB_CONFIGURATION_ID_ITEM',
  0x0184: 'MCD_DB_CONFIGURATION_RECORD',
  0x0185: 'MCD_DB_CONFIGURATION_RECORDS',
  0x0186: 'MCD_DB_CONFIGURATION_RECORD_REFERENCES',
  0x0187: 'MCD_DB_CODING_DATA',
  0x0188: 'MCD_DB_CONFIGURATION_ITEM',
  0x0189: 'MCD_DB_DATA_ID_ITEM',
  0x018A: 'MCD_DB_DATA_RECORD',
  0x018B: 'MCD_DB_DATA_RECORDS',
  0x018C: 'MCD_DB_DATA_RECORD_REFERENCES',
  0x018D: 'MCD_DB_ITEM_VALUE',
  0x018E: 'MCD_DB_ITEM_VALUES',
  0x018F: 'MCD_DB_OPTION_ITEM',
  0x0190: 'MCD_DB_OPTION_ITEMS',
  0x0191: 'MCD_DB_SYSTEM_ITEM',
  0x0192: 'MCD_DB_SYSTEM_ITEMS',
  0x0193: 'DB_DIAG_COM_DATA_CONNECTOR',
  0x0194: 'DB_DIAG_COM_DATA_CONNECTORS',
  0x0195: 'MCD_DB_MATCHING_PARAMETER',
  0x0196: 'MCD_DB_MATCHING_PARAMETERS',
  0x0197: 'MCD_DB_SUB_COMPONENT',
  0x0198: 'MCD_DB_SUB_COMPONENTS',
  0x0199: 'MCD_DB_SUB_COMPONENT_REFERENCES',
  0x019A: 'MCD_DB_MATCHING_PATTERN',
  0x019B: 'MCD_DB_MATCHING_PATTERNS',
  0x019C: 'MCD_DB_SUB_COMPONENT_PARAM_CONNECTOR',
  0x019D: 'MCD_DB_SUB_COMPONENT_PARAM_CONNECTORS',
  0x01A0: 'MCD_DB_ECU_STATE',
  0x01A3: 'MCD_DB_ECU_STATE_CHART',
  0x01A6: 'MCD_DB_ECU_STATE_CHARTS',
  0x01A9: 'MCD_DB_ECU_STATES',
  0x01AC: 'MCD_DB_ECU_STATE_TRANSITION',
  0x01AF: 'MCD_DB_ECU_STATE_TRANSITIONS',
  0x01B2: 'MCD_DB_EXTERNAL_ACCESS_METHOD',
  0x01B5: 'MCD_DB_PRECONDITION_DEFINITION',
  0x01B8: 'MCD_DB_PRECONDITION_DEFINITIONS',
  0x01BB: 'MCD_DB_STATE_TRANSITION_ACTION',
  0x01BE: 'MCD_DB_STATE_TRANSITION_ACTIONS',
  0x01C1: 'MCD_DB_ECU_STATE_REFERENCES',
  0x01C4: 'MCD_DB_ECU_STATE_CHART_REFERENCES',
  0x01C7: 'MCD_DB_ECU_STATE_TRANSITION_REFERENCES',
  0x01CA: 'MCD_DB_STATE_TRANSITION_ACTION_REFERENCES',
  0x01CD: 'MCD_DB_PRE_CONDITION_DEFINITION_REFERENCES',
  0x0200: 'MCD_INTERNAL_CONSTRAINT',
  0x0201: 'MCD_SCALE_CONSTRAINTS',
  0x0202: 'MCD_SCALE_CONSTRAINT',
  0x0203: 'MCD_CONSTRAINT',
  0x0204: 'MCD_INTERVALS',
  0x0210: 'MCD_DB_SPECIAL_DATA_GROUP_CAPTION',
  0x0211: 'MCD_DB_SPECIAL_DATA_GROUP_REFERENCES',
  0x0220: 'MCD_DB_RESPONSE_REFERENCES',
  0x0230: 'MCD_DB_PARAMETER_REFERENCE',
  0x0240: 'MCD_DB_ADDITIONAL_AUDIENCES',
  0x0241: 'MCD_DB_ADDITIONAL_AUDIENCE',
  0x0250: 'DB_ODX_LINK',
  0x0251: 'DB_ODX_LINKS',
  0x0255: 'DB_LIBRARY',
  0x0300: 'MCD_DB_BASE_FUNCTION_NODE',
  0x0301: 'MCD_DB_COMPONENT_CONNECTOR',
  0x0302: 'MCD_DB_COMPONENT_CONNECTORS',
  0x0303: 'MCD_DB_DIAG_OBJECT_CONNECTOR',
  0x0304: 'MCD_DB_DIAG_TROUBLE_CODE_CONNECTOR',
  0x0305: 'MCD_DB_DIAG_TROUBLE_CODE_CONNECTORS',
  0x0306: 'MCD_DB_FAULT_MEMORY',
  0x0307: 'MCD_DB_ENV_DATA_CONNECTOR',
  0x0308: 'MCD_DB_ENV_DATA_CONNECTORS',
  0x0309: 'MCD_DB_ENV_DATA_DESC',
  0x030A: 'MCD_DB_FUNCTION_DIAG_COM_CONNECTOR',
  0x030B: 'MCD_DB_FUNCTION_DIAG_COM_CONNECTORS',
  0x030C: 'MCD_DB_FUNCTION_DICTIONARY',
  0x030D: 'MCD_DB_FUNCTION_DICTIONARIES',
  0x030E: 'MCD_DB_FUNCTION_IN_PARAMETER',
  0x030F: 'MCD_DB_FUNCTION_IN_PARAMETERS',
  0x0310: 'MCD_DB_FUNCTION_OUT_PARAMETER',
  0x0311: 'MCD_DB_FUNCTION_OUT_PARAMETERS',
  0x0312: 'MCD_DB_FUNCTION_NODE',
  0x0313: 'MCD_DB_FUNCTION_NODES',
  0x0314: 'MCD_DB_FUNCTION_NODE_GROUP',
  0x0315: 'MCD_DB_FUNCTION_NODE_GROUPS',
  0x0316: 'MCD_DB_TABLE_ROW_CONNECTOR',
  0x0317: 'MCD_DB_TABLE_ROW_CONNECTORS',
  0x0318: 'DB_FUNCTION_DICTIONARY_DATA',
  0x0319: 'DB_COM_PARAM_SPEC',
  0x031A: 'DB_COM_PARAM_SUB_SET',
  0x031B: 'DB_FLASH_DATA',
  0x031C: 'MCD_DB_ENV_DATA_DESCS',
  0x031D: 'MCD_DB_FAULT_MEMORIES',
  0x031E: 'DB_STATE_CHART_DATA',
  0x031F: 'DB_INLINE_FLASH_DATA'
}

location_types = {
    0x0101: 'ECU_BASE_VARIANT',
    0x0102: 'ECU_VARIANT',
    0x0103: 'FUNCTIONAL_GROUP',
    0x0104: 'MULTIPLE_ECU_JOB',
    0x0105: 'PROTOCOL'
}


def get_object_type_enum(value):
    return object_types[int(value)]


def get_location_type_enum(value):
    return location_types[int(value)]


def get_mcd_value_data_type_enum(value):
    # Types above 18 are considered to have no type
    if value > 18:
        return 'eNO_TYPE'
    
    # Types A_INT8 and A_UINT8 are excluded for some reason
    # Also, the rest of excluded types until 18 are considered invalid
    if value in [9, 13, 15, 16, 17, 18]:
        raise RuntimeError('Invalid MCDValue data type: {}'.format(value))
    
    # The other types correspond to the MCDDatType enum
    return get_MCDDataType(value)


def get_db_file_type(pool_id):
    db_file_type = pool_id.rsplit('.', 1)[1]
    match db_file_type:
        case 'vi':
            return 'Vehicle Information Table'
        case 'ec':
            return 'ECU Configuration'
        case 'fl':
            return 'Flash'
        case 'fd':
            return 'Function Dictionary'
        case 'sd':
            return 'ECU Shared Data'
        case 'pr':
            return 'Protocol'
        case 'fg':
            return 'Functional Group'
        case 'bv':
            return 'Base Variant'
        case 'ev':
            return 'ECU Variant'
        case 'mj':
            return 'Multiple ECU Job'
        case 'cp':
            return 'Communication Parameters'
        case _:
            return 'Unknown ({})'.format(db_file_type)


def get_MCDLocationType(value):
    match value:
        case 0x0101:
            return 'eECU_BASE_VARIANT'
        case 0x0102:
            return 'eECU_VARIANT'
        case 0x0103:
            return 'eFUNCTIONAL_GROUP'
        case 0x0104:
            return 'eMULTIPLE_ECU_JOB'
        case 0x0105:
            return 'ePROTOCOL'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDGatewayMode(value):
    match value:
        case 0x6E03:
            return 'eNO_GATEWAY'
        case 0x6E01:
            return 'eTRANSPARENT_GATEWAY'
        case 0x6E02:
            return 'eVISIBLE_GATEWAY'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDParameterType(value):
    match value:
        case 0x7001:
            return 'eVALUE'
        case 0x7002:
            return 'eRESERVED'
        case 0x7003:
            return 'eCODED_CONST'
        case 0x7004:
            return 'ePHYS_CONST'
        case 0x7005:
            return 'eLENGTH_KEY'
        case 0x7006:
            return 'eMATCHING_REQUEST_PARAM'
        case 0x7007:
            return 'eSYSTEM'
        case 0x7008:
            return 'eDYNAMIC'
        case 0x7009:
            return 'eTABLE_KEY'
        case 0x7010:
            return 'eTABLE_STRUCT'
        case 0x7011:
            return 'eTABLE_ENTRY'
        case 0x7012:
            return 'eGENERATED'
        case 0x7013:
            return 'eNRC_CONST'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDConnectorPinType(value):
    match value:
        case 0x7400:
            pin_type = 'eHI'
        case 0x7401:
            pin_type = 'eLOW'
        case 0x7402:
            pin_type = 'eK'
        case 0x7403:
            pin_type = 'eL'
        case 0x7404:
            pin_type = 'eTX'
        case 0x7405:
            pin_type = 'eRX'
        case 0x7406:
            pin_type = 'ePLUS'
        case 0x7407:
            pin_type = 'eMINUS'
        case 0x7408:
            pin_type = 'eSINGLEWIRE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDObjectType(value):
    match value:
        case 0x04CA:
            return 'eMCDACCESSKEY'
        case 0x04CB:
            return 'eMCDACCESSKEYS'
        case 0x0DAC:
            return 'eMCDAUDIENCE'
        case 0x0403:
            return 'eMCDCOLLECTION'
        case 0x0404:
            return 'eMCDCOMMUNICATIONEXCEPTION'
        case 0x0DA4:
            return 'eMCDCONFIGURATIONIDITEM'
        case 0x0DA2:
            return 'eMCDCONFIGURATIONITEM'
        case 0x0DA1:
            return 'eMCDCONFIGURATIONRECORD'
        case 0x0DA0:
            return 'eMCDCONFIGURATIONRECORDS'
        case 0x0D8D:
            return 'eMCDCONSTRAINT'
        case 0x0C84:
            return 'eMCDCONTROLPRIMITIVE'
        case 0x0405:
            return 'eMCDDATABASEEXCEPTION'
        case 0x0DA5:
            return 'eMCDDATAIDITEM'
        case 0x0C80:
            return 'eMCDDATAPRIMITIVE'
        case 0x0C8D:
            return 'eMCDDBACCESSLEVEL'
        case 0x0DAD:
            return 'eMCDDBADDITIONALAUDIENCE'
        case 0x0DAE:
            return 'eMCDDBADDITIONALAUDIENCES'
        case 0x0E02:
            return 'eMCDDBBASEFUNCTIONNODE'
        case 0x0DF5:
            return 'eMCDDBCODEINFORMATION'
        case 0x0DFA:
            return 'eMCDDBCODEINFORMATIONS'
        case 0x0D96:
            return 'eMCDDBCODINGDATA'
        case 0x0DD4:
            return 'eMCDDBCOMPONENTCONNECTOR'
        case 0x0DD3:
            return 'eMCDDBCOMPONENTCONNECTORS'
        case 0x0DF0:
            return 'eMCDDBCONFIGURATIONDATA'
        case 0x0DF1:
            return 'eMCDDBCONFIGURATIONDATAS'
        case 0x0D99:
            return 'eMCDDBCONFIGURATIONIDITEM'
        case 0x0D97:
            return 'eMCDDBCONFIGURATIONITEM'
        case 0x0D92:
            return 'eMCDDBCONFIGURATIONRECORD'
        case 0x0DF2:
            return 'eMCDDBCONFIGURATIONRECORDS'
        case 0x0C85:
            return 'eMCDDBCONTROLPRIMITIVE'
        case 0x0C95:
            return 'eMCDDBCONTROLPRIMITIVES'
        case 0x0D9A:
            return 'eMCDDBDATAIDITEM'
        case 0x0C82:
            return 'eMCDDBDATAPRIMITIVE'
        case 0x0CA2:
            return 'eMCDDBDATAPRIMITIVES'
        case 0x0D95:
            return 'eMCDDBDATARECORD'
        case 0x0D94:
            return 'eMCDDBDATARECORDS'
        case 0x0CAD:
            return 'eMCDDBDIAGCOMPRIMITIVE'
        case 0x0482:
            return 'eMCDDBDIAGCOMPRIMITIVES'
        case 0x0DC7:
            return 'eMCDDBDIAGOBJECTCONNECTOR'
        case 0x0C83:
            return 'eMCDDBDIAGSERVICE'
        case 0x0C94:
            return 'eMCDDBDIAGSERVICES'
        case 0x04CC:
            return 'eMCDDBDIAGTROUBLECODE'
        case 0x0DC9:
            return 'eMCDDBDIAGTROUBLECODECONNECTOR'
        case 0x0DC8:
            return 'eMCDDBDIAGTROUBLECODECONNECTORS'
        case 0x04CD:
            return 'eMCDDBDIAGTROUBLECODES'
        case 0x0CA5:
            return 'eMCDDBDYNIDCLEARCOMPRIMITIVE'
        case 0x0C8F:
            return 'eMCDDBDYNIDDEFINECOMPRIMITIVE'
        case 0x0C90:
            return 'eMCDDBDYNIDREADCOMPRIMITIVE'
        case 0x0CA3:
            return 'eMCDDBECU'
        case 0x0484:
            return 'eMCDDBECUBASEVARIANT'
        case 0x0485:
            return 'eMCDDBECUBASEVARIANTS'
        case 0x0C8B:
            return 'eMCDDBECUMEM'
        case 0x0C8C:
            return 'eMCDDBECUMEMS'
        case 0x0DF3:
            return 'eMCDDBECUSTATE'
        case 0x0DFF:
            return 'eMCDDBECUSTATECHART'
        case 0x0DFE:
            return 'eMCDDBECUSTATECHARTS'
        case 0x0E00:
            return 'eMCDDBECUSTATES'
        case 0x0DFD:
            return 'eMCDDBECUSTATETRANSITION'
        case 0x0DFB:
            return 'eMCDDBECUSTATETRANSITIONACTION'
        case 0x0DF8:
            return 'eMCDDBECUSTATETRANSITIONACTIONS'
        case 0x0DF7:
            return 'eMCDDBECUSTATETRANSITIONS'
        case 0x0486:
            return 'eMCDDBECUVARIANT'
        case 0x0487:
            return 'eMCDDBECUVARIANTS'
        case 0x0DCB:
            return 'eMCDDBENVDATACONNECTOR'
        case 0x0DCA:
            return 'eMCDDBENVDATACONNECTORS'
        case 0x048D:
            return 'eMCDDBENVDATADESC'
        case 0x048E:
            return 'eMCDDBENVDATADESCS'
        case 0x0DF4:
            return 'eMCDDBEXTERNALACCESSMETHOD'
        case 0x0CB6:
            return 'eMCDDBFAULTMEMORIES'
        case 0x0CB4:
            return 'eMCDDBFAULTMEMORY'
        case 0x04B7:
            return 'eMCDDBFLASHCHECKSUM'
        case 0x04B8:
            return 'eMCDDBFLASHCHECKSUMS'
        case 0x04B9:
            return 'eMCDDBFLASHDATA'
        case 0x04BA:
            return 'eMCDDBFLASHDATABLOCK'
        case 0x04BB:
            return 'eMCDDBFLASHDATABLOCKS'
        case 0x04BC:
            return 'eMCDDBFLASHFILTER'
        case 0x04BD:
            return 'eMCDDBFLASHFILTERS'
        case 0x04BE:
            return 'eMCDDBFLASHIDENT'
        case 0x04BF:
            return 'eMCDDBFLASHIDENTS'
        case 0x04C0:
            return 'eMCDDBFLASHJOB'
        case 0x04C1:
            return 'eMCDDBFLASHSECURITIES'
        case 0x04C2:
            return 'eMCDDBFLASHSECURITY'
        case 0x04C3:
            return 'eMCDDBFLASHSEGMENT'
        case 0x04C4:
            return 'eMCDDBFLASHSEGMENTS'
        case 0x04C5:
            return 'eMCDDBFLASHSESSION'
        case 0x04C6:
            return 'eMCDDBFLASHSESSIONCLASS'
        case 0x04C7:
            return 'eMCDDBFLASHSESSIONCLASSES'
        case 0x04C8:
            return 'eMCDDBFLASHSESSIONS'
        case 0x0488:
            return 'eMCDDBFUNCTIONALCLASS'
        case 0x0489:
            return 'eMCDDBFUNCTIONALCLASSES'
        case 0x048A:
            return 'eMCDDBFUNCTIONALGROUP'
        case 0x048B:
            return 'eMCDDBFUNCTIONALGROUPS'
        case 0x0DCF:
            return 'eMCDDBFUNCTIONDIAGCOMCONNECTOR'
        case 0x0DCE:
            return 'eMCDDBFUNCTIONDIAGCOMCONNECTORS'
        case 0x0DBC:
            return 'eMCDDBFUNCTIONDICTIONARIES'
        case 0x0DBD:
            return 'eMCDDBFUNCTIONDICTIONARY'
        case 0x0DC3:
            return 'eMCDDBFUNCTIONINPARAMETER'
        case 0x0DC2:
            return 'eMCDDBFUNCTIONINPARAMETERS'
        case 0x0DD1:
            return 'eMCDDBFUNCTIONNODE'
        case 0x0DD2:
            return 'eMCDDBFUNCTIONNODEGROUP'
        case 0x0DD8:
            return 'eMCDDBFUNCTIONNODEGROUPS'
        case 0x0DD7:
            return 'eMCDDBFUNCTIONNODES'
        case 0x0DC5:
            return 'eMCDDBFUNCTIONOUTPARAMETER'
        case 0x0DC4:
            return 'eMCDDBFUNCTIONOUTPARAMETERS'
        case 0x048F:
            return 'eMCDDBHEXSERVICE'
        case 0x0C98:
            return 'eMCDDBIDENTDESCRIPTION'
        case 0x0DE7:
            return 'eMCDDBINTERFACECABLE'
        case 0x0DE8:
            return 'eMCDDBINTERFACECABLES'
        case 0x0DE9:
            return 'eMCDDBINTERFACECONNECTORPIN'
        case 0x0DEA:
            return 'eMCDDBINTERFACECONNECTORPINS'
        case 0x0D9E:
            return 'eMCDDBITEMVALUE'
        case 0x0D9F:
            return 'eMCDDBITEMVALUES'
        case 0x0C9E:
            return 'eMCDDBJOB'
        case 0x0C9D:
            return 'eMCDDBJOBS'
        case 0x0406:
            return 'eMCDDBLOCATION'
        case 0x0407:
            return 'eMCDDBLOCATIONS'
        case 0x0408:
            return 'eMCDDBLOGICALLINK'
        case 0x0409:
            return 'eMCDDBLOGICALLINKS'
        case 0x0D8C:
            return 'eMCDDBMATCHINGPARAMETER'
        case 0x0D8B:
            return 'eMCDDBMATCHINGPARAMETERS'
        case 0x0D8A:
            return 'eMCDDBMATCHINGPATTERN'
        case 0x0D89:
            return 'eMCDDBMATCHINGPATTERNS'
        case 0x0490:
            return 'eMCDDBMULTIPLEECUJOB'
        case 0x042D:
            return 'eMCDDBOBJECT'
        case 0x0D9B:
            return 'eMCDDBOPTIONITEM'
        case 0x0D9D:
            return 'eMCDDBOPTIONITEMS'
        case 0x0CAE:
            return 'eMCDDBPARAMETER'
        case 0x0480:
            return 'eMCDDBPARAMETERS'
        case 0x0DAB:
            return 'eMCDDBPHYSICALDIMENSION'
        case 0x0C9A:
            return 'eMCDDBPHYSICALMEMORIES'
        case 0x0C99:
            return 'eMCDDBPHYSICALMEMORY'
        case 0x0C9B:
            return 'eMCDDBPHYSICALSEGMENT'
        case 0x0C9C:
            return 'eMCDDBPHYSICALSEGMENTS'
        case 0x0DEB:
            return 'eMCDDBPHYSICALVEHICLELINK'
        case 0x040A:
            return 'eMCDDBPHYSICALVEHICLELINKORINTERFACE'
        case 0x040B:
            return 'eMCDDBPHYSICALVEHICLELINKORINTERFACES'
        case 0x0DFC:
            return 'eMCDDBPRECONDITIONDEFINITION'
        case 0x0DF6:
            return 'eMCDDBPRECONDITIONDEFINITIONS'
        case 0x040C:
            return 'eMCDDBPROJECT'
        case 0x042B:
            return 'eMCDDBPROJECTCONFIGURATION'
        case 0x040D:
            return 'eMCDDBPROJECTDESCRIPTION'
        case 0x040E:
            return 'eMCDDBPROJECTDESCRIPTIONS'
        case 0x0493:
            return 'eMCDDBPROTOCOLPARAMETERSET'
        case 0x0C89:
            return 'eMCDDBREQUEST'
        case 0x0494:
            return 'eMCDDBREQUESTPARAMETER'
        case 0x0C8E:
            return 'eMCDDBREQUESTPARAMETERS'
        case 0x0495:
            return 'eMCDDBRESPONSE'
        case 0x0496:
            return 'eMCDDBRESPONSEPARAMETER'
        case 0x0497:
            return 'eMCDDBRESPONSEPARAMETERS'
        case 0x0498:
            return 'eMCDDBRESPONSES'
        case 0x0499:
            return 'eMCDDBSERVICE'
        case 0x049A:
            return 'eMCDDBSERVICES'
        case 0x049B:
            return 'eMCDDBSINGLEECUJOB'
        case 0x0CA9:
            return 'eMCDDBSPECIALDATA'
        case 0x0CAA:
            return 'eMCDDBSPECIALDATAELEMENT'
        case 0x0CA8:
            return 'eMCDDBSPECIALDATAGROUP'
        case 0x0CAB:
            return 'eMCDDBSPECIALDATAGROUPCAPTION'
        case 0x0CA7:
            return 'eMCDDBSPECIALDATAGROUPS'
        case 0x049C:
            return 'eMCDDBSTARTCOMMUNICATION'
        case 0x049D:
            return 'eMCDDBSTOPCOMMUNICATION'
        case 0x0DE3:
            return 'eMCDDBSUBCOMPONENT'
        case 0x0DD6:
            return 'eMCDDBSUBCOMPONENTPARAMCONNECTOR'
        case 0x0DD9:
            return 'eMCDDBSUBCOMPONENTPARAMCONNECTORS'
        case 0x0DD5:
            return 'eMCDDBSUBCOMPONENTS'
        case 0x0D98:
            return 'eMCDDBSYSTEMITEM'
        case 0x0D9C:
            return 'eMCDDBSYSTEMITEMS'
        case 0x0CB0:
            return 'eMCDDBTABLE'
        case 0x0CB5:
            return 'eMCDDBTABLEPARAMETER'
        case 0x0CB3:
            return 'eMCDDBTABLEPARAMETERS'
        case 0x0CB1:
            return 'eMCDDBTABLEROWCONNECTOR'
        case 0x0CB2:
            return 'eMCDDBTABLEROWCONNECTORS'
        case 0x0CAF:
            return 'eMCDDBTABLES'
        case 0x04CF:
            return 'eMCDDBUNIT'
        case 0x0CA0:
            return 'eMCDDBUNITGROUP'
        case 0x0C9F:
            return 'eMCDDBUNITGROUPS'
        case 0x042F:
            return 'eMCDDBUNITS'
        case 0x049E:
            return 'eMCDDBVARIANTIDENTIFICATION'
        case 0x049F:
            return 'eMCDDBVARIANTIDENTIFICATIONANDSELECTION'
        case 0x04A0:
            return 'eMCDDBVEHICLECONNECTOR'
        case 0x04A1:
            return 'eMCDDBVEHICLECONNECTORPIN'
        case 0x04A2:
            return 'eMCDDBVEHICLECONNECTORPINS'
        case 0x04C9:
            return 'eMCDDBVEHICLECONNECTORS'
        case 0x0410:
            return 'eMCDDBVEHICLEINFORMATION'
        case 0x0411:
            return 'eMCDDBVEHICLEINFORMATIONS'
        case 0x0CAC:
            return 'eMCDDIAGCOMPRIMITIVE'
        case 0x0C96:
            return 'eMCDDIAGCOMPRIMITIVES'
        case 0x0C81:
            return 'eMCDDIAGSERVICE'
        case 0x0CA6:
            return 'eMCDDYNIDCLEARCOMPRIMITIVE'
        case 0x0C91:
            return 'eMCDDYNIDDEFINECOMPRIMITIVE'
        case 0x0C92:
            return 'eMCDDYNIDREADCOMPRIMITIVE'
        case 0x0412:
            return 'eMCDERROR'
        case 0x04CE:
            return 'eMCDERRORS'
        case 0x0413:
            return 'eMCDEXCEPTION'
        case 0x04AD:
            return 'eMCDFLASHJOB'
        case 0x0E01:
            return 'eMCDFLASHSEGMENTITERATOR'
        case 0x04A6:
            return 'eMCDHEXSERVICE'
        case 0x0DE5:
            return 'eMCDINTERFACE'
        case 0x0DE2:
            return 'eMCDINTERFACERESOURCE'
        case 0x0DE4:
            return 'eMCDINTERFACERESOURCES'
        case 0x0DE6:
            return 'eMCDINTERFACES'
        case 0x0C97:
            return 'eMCDINTERVAL'
        case 0x0DAF:
            return 'eMCDINTERVALS'
        case 0x0CA1:
            return 'eMCDJOB'
        case 0x04A7:
            return 'eMCDJOBAPI'
        case 0x0414:
            return 'eMCDLOGICALLINK'
        case 0x0DEC:
            return 'eMCDMESSAGEFILTER'
        case 0x0DED:
            return 'eMCDMESSAGEFILTERS'
        case 0x0DEF:
            return 'eMCDMESSAGEFILTERVALUES'
        case 0x0DE1:
            return 'eMCDMONITORINGLINK'
        case 0x04A8:
            return 'eMCDMULTIPLEECUJOB'
        case 0x0417:
            return 'eMCDNAMEDCOLLECTION'
        case 0x0418:
            return 'eMCDNAMEDOBJECT'
        case 0x042C:
            return 'eMCDOBJECT'
        case 0x0DA3:
            return 'eMCDOPTIONITEM'
        case 0x0DF9:
            return 'eMCDOPTIONITEMS'
        case 0x042E:
            return 'eMCDPARAMETER'
        case 0x041B:
            return 'eMCDPARAMETERIZATIONEXCEPTION'
        case 0x041C:
            return 'eMCDPROGRAMVIOLATIONEXCEPTION'
        case 0x041D:
            return 'eMCDPROJECT'
        case 0x04A9:
            return 'eMCDPROTOCOLPARAMETERSET'
        case 0x0DA8:
            return 'eMCDREADDIAGCOMPRIMITIVES'
        case 0x0C8A:
            return 'eMCDREQUEST'
        case 0x04AA:
            return 'eMCDREQUESTPARAMETER'
        case 0x04AB:
            return 'eMCDREQUESTPARAMETERS'
        case 0x041E:
            return 'eMCDRESPONSE'
        case 0x041F:
            return 'eMCDRESPONSEPARAMETER'
        case 0x0420:
            return 'eMCDRESPONSEPARAMETERS'
        case 0x0421:
            return 'eMCDRESPONSES'
        case 0x0422:
            return 'eMCDRESULT'
        case 0x0423:
            return 'eMCDRESULTS'
        case 0x04AC:
            return 'eMCDRESULTSTATE'
        case 0x0D8E:
            return 'eMCDSCALECONSTRAINT'
        case 0x0D8F:
            return 'eMCDSCALECONSTRAINTS'
        case 0x04AE:
            return 'eMCDSERVICE'
        case 0x0424:
            return 'eMCDSHAREEXCEPTION'
        case 0x04B0:
            return 'eMCDSINGLEECUJOB'
        case 0x04B1:
            return 'eMCDSTARTCOMMUNICATION'
        case 0x04B2:
            return 'eMCDSTOPCOMMUNICATION'
        case 0x0425:
            return 'eMCDSYSTEM'
        case 0x0427:
            return 'eMCDSYSTEMEXCEPTION'
        case 0x0DA6:
            return 'eMCDSYSTEMITEM'
        case 0x0DAA:
            return 'eMCDSYSTEMITEMS'
        case 0x04B3:
            return 'eMCDTEXTTABLEELEMENT'
        case 0x04B4:
            return 'eMCDTEXTTABLEELEMENTS'
        case 0x0428:
            return 'eMCDVALUE'
        case 0x0429:
            return 'eMCDVALUES'
        case 0x04B5:
            return 'eMCDVARIANTIDENTIFICATION'
        case 0x04B6:
            return 'eMCDVARIANTIDENTIFICATIONANDSELECTION'
        case 0x042A:
            return 'eMCDVERSION'
        case 0x0DA7:
            return 'eMCDWRITEDIAGCOMPRIMITIVES'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDLimitType(value):
    match value:
        case 0x6D02:
            return 'eLIMIT_CLOSED'
        case 0x6D03:
            return 'eLIMIT_INFINITE'
        case 0x6D01:
            return 'eLIMIT_OPEN'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDLimitType(value):
    match value:
        case 0x6D02:
            return 'eLIMIT_CLOSED'
        case 0x6D03:
            return 'eLIMIT_INFINITE'
        case 0x6D01:
            return 'eLIMIT_OPEN'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDRangeInfo(value):
    match value:
        case 0x0607:
            return 'eVALUE_CODED_TO_PHYSICAL_FAILED'
        case 0x0604:
            return 'eVALUE_NOT_AVAILABLE'
        case 0x0603:
            return 'eVALUE_NOT_DEFINED'
        case 0x0606:
            return 'eVALUE_NOT_INITIALIZED'
        case 0x0605:
            return 'eVALUE_NOT_VALID'
        case 0x0602:
            return 'eVALUE_VALID'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDRepetitionMode(value):
    match value:
        case 0x6602:
            return 'eREPEATED'
        case 0x6601:
            return 'eSINGLE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDAddressingMode(value):
    match value:
        case 0x6003:
            return 'eFUNCTIONAL'
        case 0x6004:
            return 'eFUNCTIONAL_OR_PHYSICAL'
        case 0x6002:
            return 'ePHYSICAL'
        case 0x6001:
            return 'eUNDEFINED'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDRuntimeMode(value):
    match value:
        case 0x6902:
            return 'eCYCLIC'
        case 0x6901:
            return 'eNONCYCLIC'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDTransmissionMode(value):
    match value:
        case 0x6A01:
            return 'eNO_TRANSMISSION'
        case 0x6A02:
            return 'eRECEIVE'
        case 0x6A03:
            return 'eSEND'
        case 0x6A04:
            return 'eSEND_AND_RECEIVE'
        case 0x6A05:
            return 'eSEND_OR_RECEIVE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDUnitGroupCategory(value):
    match value:
        case 0x0F00:
            return 'eCOUNTRY'
        case 0x0F01:
            return 'eEQUIVALENT_UNITS'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDResponseType(value):
    match value:
        case 0x6F03:
            return 'eGLOBAL_NEG_RESPONSE'
        case 0x6F02:
            return 'eLOCAL_NEG_RESPONSE'
        case 0x6F01:
            return 'ePOSITIVE_RESPONSE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_EDbCompuCategory(value):
    match value:
        case 0:
            return 'eIDENTICAL'
        case 1:
            return 'eLINEAR'
        case 2:
            return 'eSCALE_LINEAR'
        case 3:
            return 'eTEXTTAB'
        case 4:
            return 'eCOMPUCODE'
        case 5:
            return 'eTAB_INTP'
        case 6:
            return 'eRAT_FUNC'
        case 7:
            return 'eSCALE_RAT_FUNC'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_EDbDiagCodedType(value):
    match value:
        case 0:
            return 'eLEADING_LENGTH_INFO_TYPE'
        case 1:
            return 'eMIN_MAX_LENGTH_TYPE'
        case 2:
            return 'eSTANDARD_LENGTH_TYPE'
        case 3:
            return 'ePARAM_LENGTH_INFO_TYPE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_EDbTermination(value):
    match value:
        case 0:
            return 'eENDOFPDU'
        case 1:
            return 'eZERO'
        case 2:
            return 'eHEX_FF'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_EDbEncoding(value):
    match value:
        case 0:
            return 'eBCD_P'
        case 1:
            return 'eBCD_UP'
        case 2:
            return 'e1C'
        case 3:
            return 'e2C'
        case 4:
            return 'eSM'
        case 5:
            return 'eUTF_8'
        case 6:
            return 'eUCS_2'
        case 7:
            return 'eIEEE754'
        case 8:
            return 'eISO_8859_1'
        case 9:
            return 'eISO_8859_2'
        case 10:
            return 'eWINDOWS_1252'
        case 11:
            return 'eNONE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_MCDDataType(value):
    match value:
        case 0x0001:
            return 'eA_ASCIISTRING'
        case 0x0002:
            return 'eA_BITFIELD'
        case 0x0003:
            return 'eA_BYTEFIELD'
        case 0x0004:
            return 'eA_FLOAT32'
        case 0x0005:
            return 'eA_FLOAT64'
        case 0x0006:
            return 'eA_INT16'
        case 0x0007:
            return 'eA_INT32'
        case 0x0008:
            return 'eA_INT64'
        case 0x0009:
            return 'eA_INT8'
        case 0x000A:
            return 'eA_UINT16'
        case 0x000B:
            return 'eA_UINT32'
        case 0x000C:
            return 'eA_UINT64'
        case 0x000D:
            return 'eA_UINT8'
        case 0x000E:
            return 'eA_UNICODE2STRING'
        case 0x000F:
            return 'eFIELD'
        case 0x0010:
            return 'eMULTIPLEXER'
        case 0x0011:
            return 'eSTRUCTURE'
        case 0x0012:
            return 'eTEXTTABLE'
        case 0x0013:
            return 'eA_BOOLEAN'
        case 0x0014:
            return 'eDTC'
        case 0x0015:
            return 'eENVDATA'
        case 0x0016:
            return 'eEND_OF_PDU'
        case 0x0017:
            return 'eTABLE'
        case 0x0018:
            return 'eENVDATADESC'
        case 0x0019:
            return 'eKEY'
        case 0x001A:
            return 'eLENGTHKEY'
        case 0x001B:
            return 'eTABLE_ROW'
        case 0x001C:
            return 'eSTRUCT_FIELD'
        case 0x00FF:
            return 'eNO_TYPE'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def get_EDbDataType(value):
    match value:
        case 0:
            return 'eDB_INT32'
        case 1:
            return 'eDB_UINT32'
        case 2:
            return 'eDB_FLOAT32'
        case 3:
            return 'eDB_FLOAT64'
        case 4:
            return 'eDB_ASCIISTRING'
        case 5:
            return 'eDB_UTF8STRING'
        case 6:
            return 'eDB_UNICODE2STRING'
        case 7:
            return 'eDB_BYTEFIELD'
        case 8:
            return 'eDB_BITFIELD'
        case _:
            raise RuntimeError('Invalid enum value ({:04X})'.format(value))


def map_enum_EDbDataType_to_MCDDataType(EDbDataType_enum):
    match EDbDataType_enum & 0xFF:
        case 0: # eDB_INT32
            return 7 # eA_INT32
        case 1: # eDB_UINT32
            return 11 # eA_UINT32
        case 2: # eDB_FLOAT32
            return 4 # eA_FLOAT32
        case 3: # eDB_FLOAT64
            return 5 # eA_FLOAT64
        case 4: # eDB_ASCIISTRING
            return 1 # eA_ASCIISTRING
        case 5 | 6: # eDB_UTF8STRING, eDB_UNICODE2STRING
            return 14 # eA_UNICODE2STRING
        case 7: # eDB_BYTEFIELD
            return 3 # c
        case 8: # eDB_BITFIELD
            return 2 # eA_BITFIELD
        case _:
            #return 0xFF
            raise RuntimeError('Invalid enum value ({:04X})'.format(EDbDataType_enum))


def map_enum_EDbPhysicalDataType_to_EDbDataType(EDbPhysicalDataType_enum):
    match EDbPhysicalDataType_enum & 0xFF:
        case 0:
            return 0
        case 1:
            return 1
        case 2:
            return 2
        case 3:
            return 3
        case 4:
            return 6
        case 5:
            return 7
        case _:
            #return 0
            raise RuntimeError('Invalid enum value ({:04X})'.format(EDbPhysicalDataType_enum))


def map_enum_EDbPhysicalDataType_to_MCDDataType(EDbPhysicalDataType_enum):
    match EDbPhysicalDataType_enum & 0xFF:
        case 0:
            return 7 # eA_INT32
        case 1:
            return 11 # eA_UINT32
        case 2:
            return 4 # eA_FLOAT32
        case 3:
            return 5 # eA_FLOAT64
        case 4:
            return 14 # eA_UNICODE2STRING
        case 5:
            return 3 # eA_BYTEFIELD
        case _:
            #return 0xFF
            raise RuntimeError('Invalid enum value ({:04X})'.format(EDbPhysicalDataType_enum))

