
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


def _to_safe_iterator_expression(itlist):
    strlist = []
    for i in itlist:
        if isinstance(i, sasoptpy.core.Expression):
            strlist.append(i._expr())
        elif isinstance(i, str):
            safe_i = "".join(c if c.isalnum() else '_' for c in i)
            strlist.append("'{}'".format(safe_i))
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


def get_key_for_expr(key):
    if isinstance(key, sasoptpy.abstract.SetIterator):
        return key._get_for_expr()
    else:
        return 'for {} in {}'.format(key._name, key._set._name)


def multiply_coefficients(left, right, target):

    left = left.copy()
    left['CONST'] = left.pop('CONST')
    right = right.copy()
    right['CONST'] = right.pop('CONST')

    for i, x in left.items():
        for j, y in right.items():
            if x['ref'] is None and y['ref'] is None:
                append_coef_value(
                    target, ref=None, key='CONST', value=x['val'] * y['val'])
            elif x['ref'] is None:
                if x['val'] * y['val'] != 0:
                    append_coef_value(
                        target, ref=y['ref'], key=j, value=x['val'] * y['val'])
            elif y['ref'] is None:
                if x['val'] * y['val'] != 0:
                    append_coef_value(
                        target, ref=x['ref'], key=i, value=x['val'] * y['val'])
            else:
                if x['val'] * y['val'] != 0:
                    if x.get('op') is None and y.get('op') is None:
                        new_key = sasoptpy.util.pack_to_tuple(i) + \
                                  sasoptpy.util.pack_to_tuple(j)
                        alt_key = sasoptpy.util.pack_to_tuple(j) + \
                                  sasoptpy.util.pack_to_tuple(i)
                        new_ref = list(x['ref']) + list(y['ref'])
                        if alt_key in target:
                            append_coef_value(
                                target, ref=new_ref, key=alt_key,
                                value=x['val'] * y['val'])
                        else:
                            append_coef_value(
                                target, ref=new_ref, key=new_key,
                                value=x['val'] * y['val'])
                    else:
                        new_key = (i, j)
                        x_actual = x['ref']
                        if 'op' in x and x['op'] is not None:
                            x_actual = sasoptpy.util.wrap_expression(x)
                        y_actual = y['ref']
                        if 'op' in y and y['op'] is not None:
                            y_actual = sasoptpy.util.wrap_expression(y)

                        append_coef_value(
                            target, ref=[x_actual, y_actual], key=new_key,
                            value=x['val'] * y['val'])


def append_coef_value(original_dict, ref, key, value):
    if key in original_dict:
        original_dict[key]['val'] +=  value
    else:
        original_dict[key] = {'ref': ref, 'val': value}


def get_name_from_keys(name, keys):
    return '{}['.format(name) + ','.join(format(k) for k in keys) + ']'


