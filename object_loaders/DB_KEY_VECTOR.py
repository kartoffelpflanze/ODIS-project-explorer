from common_utils import common_loaders


def load(stream):
    obj = {}
    obj['keys'] = common_loaders.loadAsciiStringVectorFromObjectStream(stream)
    return obj
