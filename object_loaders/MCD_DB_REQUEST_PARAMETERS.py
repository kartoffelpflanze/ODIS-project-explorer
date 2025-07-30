from object_loaders import MCD_DB_PARAMETERS


def load(stream):
    return MCD_DB_PARAMETERS.load(stream) # super = MCDDbParameters
