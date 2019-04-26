
import warnings

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


def _evaluate(comp):
    """
    Evaluates the value of a given expression component.

    Parameters
    ----------
    comp : dict
        Dictionary of references, coefficient and operator

    Returns
    -------
    v : float
        Current value of the expression.
    """

    ref = comp['ref']
    val = comp['val']
    op = comp.get('op')
    v = 0

    if op is None:
        op = '*'

    if op == '*':
        v = val
        for i in ref:
            v = v * i.get_value()
    elif op == '/':
        try:
            v = val * ref[0].get_value() / ref[1].get_value()
        except ZeroDivisionError:
            print('ERROR: Float division by zero')
            return None
    elif op == '^':
        v = val * ref[0].get_value() ** ref[1].get_value()
    else:
        # Hacky way of doing this
        warnings.warn('Operator {} is not supported, running with Python\'s exec function.'.format(op), SyntaxWarning)
        exec("v = val * (ref[0].get_value() {} ref[1].get_value())".format(op), globals(), locals())

    return v

