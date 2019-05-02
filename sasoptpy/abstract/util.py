
import sasoptpy


def is_abstract_set(arg):
    return isinstance(arg, sasoptpy.abstract.Set)


def is_key_abstract(arg):
    return isinstance(arg, sasoptpy.abstract.SetIterator)


def is_parameter(arg):
    return isinstance(arg, sasoptpy.abstract.Parameter)
