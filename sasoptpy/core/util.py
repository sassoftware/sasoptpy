
import warnings

import sasoptpy
from sasoptpy._libs import np


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


def expression_to_constraint(left, relation, right):

    if isinstance(right, list) and relation == 'E':
        e = left.copy()
        e._add_coef_value(None, 'CONST', -1 * min(right[0], right[1]))
        ranged_constraint = sasoptpy.core.Constraint(exp=e, direction='E',
                                                crange=abs(right[1] - right[0]))
        return ranged_constraint
    elif not is_variable(left):
        if left._temp and is_expression(left):
            r = left
        else:
            if left._operator is None:
                r = left.copy()
            else:
                r = Expression(0)
                r += left
        #  TODO r=self could be used whenever expression has no name
        if np.isinstance(type(right), np.number):
            r._linCoef['CONST']['val'] -= right
        elif is_expression(right):
            r -= right
        generated_constraint = sasoptpy.core.Constraint(exp=r, direction=relation, crange=0)
        return generated_constraint
    else:
        r = sasoptpy.core.Expression()
        for v in left._linCoef:
            r._add_coef_value(left._linCoef[v]['ref'], v,
                              left._linCoef[v]['val'])
        if np.isinstance(type(right), np.number):
            r._linCoef['CONST']['val'] -= right
        else:
            for v in right._linCoef:
                r._add_coef_value(right._linCoef[v]['ref'],
                                  v, -right._linCoef[v]['val'])
        generated_constraint = sasoptpy.core.Constraint(exp=r, direction=relation, crange=0)
        return generated_constraint

