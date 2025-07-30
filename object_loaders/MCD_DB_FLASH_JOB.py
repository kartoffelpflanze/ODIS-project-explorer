from object_loaders import MCD_DB_JOB


def load(stream):
    return MCD_DB_JOB.load(stream) # super = MCDDbJobImpl
