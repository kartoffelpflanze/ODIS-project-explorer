from object_loaders import DB_CASE_BASE


def load(stream):
    return DB_CASE_BASE.load(stream) # super = DbCaseBase
