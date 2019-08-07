
import sasoptpy

def is_abstract(arg):
    from sasoptpy.abstract import (Set, SetIterator, Parameter, ParameterValue,
                                   ImplicitVar)
    abstract_classes = [Set, SetIterator, Parameter, ParameterValue, ImplicitVar]
    return any(isinstance(arg, i) for i in abstract_classes)

def is_abstract_set(arg):
    return isinstance(arg, sasoptpy.abstract.Set)


def is_key_abstract(arg):
    return isinstance(arg, sasoptpy.abstract.SetIterator)


def is_parameter(arg):
    return isinstance(arg, sasoptpy.abstract.Parameter)

