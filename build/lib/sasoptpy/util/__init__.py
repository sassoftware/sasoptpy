from .package_utils import load_package_globals
from .package_utils import *
from .user_utils import *
import sasoptpy


def to_expression(item):
    if hasattr(item, '_expr'):
        return item._expr()
    else:
        return sasoptpy.util.package_utils._to_sas_string(item)


def to_definition(item):
    return item._defn()


def to_optmodel(item, **kwargs):
    return sasoptpy.interface.to_optmodel(item, **kwargs)
