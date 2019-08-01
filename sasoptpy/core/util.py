
from math import inf
import warnings

import sasoptpy
from sasoptpy._libs import np, pd


def is_expression(obj):
    return isinstance(obj, sasoptpy.core.Expression)


def is_variable(obj):
    return isinstance(obj, sasoptpy.core.Variable)


def is_constraint(obj):
    return isinstance(obj, sasoptpy.core.Constraint)


def is_abstract(obj):
    if hasattr(obj, '_abstract') and obj._abstract:
        return True
    return False


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
    v = None

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
            raise ZeroDivisionError('Division error in evaluation')
    elif op == '^':
        v = val * ref[0].get_value() ** ref[1].get_value()

    return v


def expression_to_constraint(left, relation, right):

    if isinstance(right, list) and relation == 'E':
        e = left.copy()
        e._add_coef_value(None, 'CONST', -1 * min(right[0], right[1]))
        ranged_constraint = sasoptpy.core.Constraint(
            exp=e, direction='E', crange=abs(right[1] - right[0]))
        return ranged_constraint
    elif not is_variable(left):
        if left._operator is None:
            r = left.copy()
        else:
            r = Expression(0)
            r += left
        if np.isinstance(type(right), np.number):
            r._linCoef['CONST']['val'] -= right
        elif is_expression(right):
            r -= right
        generated_constraint = sasoptpy.core.Constraint(
            exp=r, direction=relation, crange=0)
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
        generated_constraint = sasoptpy.core.Constraint(
            exp=r, direction=relation, crange=0)
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
        original_dict[key]['val'] += value
    else:
        original_dict[key] = {'ref': ref, 'val': value}


def get_name_from_keys(name, keys):
    return '{}['.format(name) + ','.join(format(k) for k in keys) + ']'


def check_transfer_mode(argv):
    if sasoptpy.transfer_allowed and hasattr(argv, 'gi_frame'):
        argv.gi_frame.f_globals.update(sasoptpy._transfer)


def get_generator_names(argv):
    keys = tuple()
    if argv.gi_code.co_nlocals == 1:
        vnames = argv.gi_code.co_cellvars
    else:
        vnames = argv.gi_code.co_varnames
    vdict = argv.gi_frame.f_locals
    for ky in vnames:
        if ky != '.0':
            keys = keys + (vdict[ky],)
    return keys


def get_default_value(vartype, key):
    return sasoptpy.config['default_bounds'].get(vartype).get(key)


def get_default_bounds_if_none(vartype, lb, ub):
    lb = get_default_value(vartype, 'lb') if lb is None else lb
    ub = get_default_value(vartype, 'ub') if ub is None else ub
    return lb, ub


def is_regular_component(cm):
    return (cm._objorder > 0 and
            not (hasattr(cm, '_shadow') and cm._shadow) and
            not (hasattr(cm, '_parent') and cm._parent))


def has_parent(cm):
    return hasattr(cm, '_parent') and cm._parent is not None


def get_group_bound(bound):
    group_types = [pd.DataFrame, pd.Series, list, dict, tuple]
    if any(isinstance(bound, g) for g in group_types):
        return None
    else:
        return bound

@sasoptpy.containable
def read_data(table, index, columns):
    pass

