

import sasoptpy


def set_group_abstract(group):
    for elem in group:
        elem.set_abstract(True)


def is_expression(obj):
    return isinstance(obj, sasoptpy.core.Expression)


def is_variable(obj):
    return isinstance(obj, sasoptpy.core.Variable)


def is_constraint(obj):
    return isinstance(obj, sasoptpy.core.Constraint)


def _to_iterator_expression(itlist):
    strlist = []
    for i in itlist:
        if isinstance(i, sasoptpy.core.Expression):
            strlist.append(i._expr())
        elif isinstance(i, str):
            strlist.append("'{}'".format(i))
        else:
            strlist.append(str(i))
    return strlist

