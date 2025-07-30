from object_loaders import MCD_DB_PROTOCOL_PARAMETER


def load(stream):
    return MCD_DB_PROTOCOL_PARAMETER.load(stream) # super = MCDDbProtocolParameterImpl
