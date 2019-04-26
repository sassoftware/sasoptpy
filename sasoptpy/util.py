#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import warnings

import sasoptpy
from sasoptpy._libs import (pd, np)


def load_package_globals():

    # Constant values
    sasoptpy.MIN = 'MIN'
    sasoptpy.MAX = 'MAX'
    sasoptpy.CONT = 'CONT'
    sasoptpy.INT = 'INT'
    sasoptpy.BIN = 'BIN'

    # Global dictionary
    sasoptpy.__namedict = {}

    # Container for wrapped statements
    sasoptpy._transfer = {}
    sasoptpy.transfer_allowed = False

    # Counters
    sasoptpy.__ctr = {'obj': [0], 'var': [0], 'con': [0], 'expr': [0], 'model': [0],
                      'i': [0], 'set': [0], 'param': [0], 'impvar': [0], 'table': [0]}

    sasoptpy.__objcnt = 0

    # Transformation dictionary
    sasoptpy._transform = {
        'binary': sasoptpy.BIN,
        'bin': sasoptpy.BIN,
        'integer': sasoptpy.INT,
        'int': sasoptpy.INT,
        'continuous': sasoptpy.CONT,
        'cont': sasoptpy.CONT,
        'maximize': sasoptpy.MAX,
        'max': sasoptpy.MAX,
        'minimize': sasoptpy.MIN,
        'min': sasoptpy.MIN
    }

    # Load default configuration
    # sasoptpy.config = Config()
    # sasoptpy.default_config_keys = sasoptpy.config.keys


def assign_name(name, ctype=None):
    """
    Checks if a name is valid and returns a random string if not

    Parameters
    ----------
    name : str or None
        Name to be checked if unique
    ctype : str, optional
        Type of the object

    Returns
    -------
    str : The given name if valid, a random string otherwise
    """
    if name and type(name) != str:
        name = ctype + '_' + str(name) if ctype else str(name)
    if name is None or name == '':
        if ctype is None:
            name = 'TMP_' + ''.join(random.choice(string.ascii_uppercase) for
                                    _ in range(5))
        else:
            name = '{}_{}'.format(ctype, get_and_increment_counter(ctype))
    else:
        if name in sasoptpy.__namedict:
            if ctype is None:
                name = ''.join(random.choice(string.ascii_lowercase) for
                               _ in range(5))
            else:
                name = '{}_{}'.format(ctype, get_and_increment_counter(ctype))
        else:
            name = name.replace(" ", "_")
    while name in sasoptpy.__namedict:
        if ctype is None:
            name = ''.join(random.choice(string.ascii_lowercase) for
                           _ in range(5))
        else:
            name = '{}_{}'.format(ctype, get_and_increment_counter(ctype))
    return name


def register_globally(name, obj):
    """
    Adds the name and order of a component into the global reference list

    Parameters
    ----------
    name : string
        Name of the object
    obj : object
        Object to be registered to the global name dictionary

    Returns
    -------
    objcnt : int
        Unique object number to represent creation order
    """
    sasoptpy.__objcnt += 1
    sasoptpy.__namedict[name] = {'ref': obj, 'order': sasoptpy.__objcnt}
    return sasoptpy.__objcnt


def delete_name(name):
    nd = get_namedict()
    if name is not None and name in nd:
        del nd[name]


def set_creation_order_if_empty(obj, order):
    if hasattr(obj, '_objorder') and not obj._objorder:
        obj._objorder = order


def get_in_digit_format(val):
    """
    Returns the default formatted string of the given numerical variable

    Parameters
    ----------
    val : float or integer
        Variable to be formatted into string

    Returns
    -------
    for : str
        Formatted string

    """
    digits = sasoptpy.config['max_digits']
    if digits and digits > 0:
        return str(round(val, digits))
    return str(val)


def _extract_argument_as_list(inp):

    if isinstance(inp, int):
        thelist = list(range(0, inp))
    elif isinstance(inp, range):
        thelist = list(inp)
    elif isinstance(inp, tuple):
        thelist = inp[0]
    elif isinstance(inp, list):
        thelist = inp
    elif sasoptpy.abstract.is_abstract_set(inp):
        thelist = [inp]
    else:
        thelist = list(inp)
    return thelist


def extract_list_value(tuplist, listname):
    """
    Extracts values inside various object types

    Parameters
    ----------
    tuplist : tuple
        Key combination to be extracted
    listname : dict or list or int or float or DataFrame or Series object
        List where the value will be extracted

    """
    if listname is None:
        v = None
    elif isinstance(listname, dict):
        v = listname[tuple_unpack(tuplist)]
    elif np.isinstance(type(listname), np.number):
        v = listname
    elif isinstance(listname, pd.DataFrame):
        if isinstance(listname.index, pd.MultiIndex):
            v = listname.loc[tuplist[:-1]][tuplist[-1]]
        else:
            v = listname.loc[tuplist]
    elif isinstance(listname, pd.Series):
        v = listname.loc[tuplist]
    else:
        v = listname
        for k in tuplist:
            v = v[k]
    return v


def _to_quoted_string(item):
    if isinstance(item, int):
        return str(item)
    elif isinstance(item, str):
        return "'{}'".format(item)
    elif isinstance(item, tuple):
        return '<' + ','.join(_to_quoted_string(j) for j in item) + '>'
    else:
        return str(item)


def is_key_abstract(key):
    import sasoptpy.abstract
    return sasoptpy.abstract.util.is_key_abstract(key)


def pack_to_tuple(obj):
    """
    Converts a given object to a tuple object

    If the object is a tuple, the function returns the input,
    otherwise creates a single dimensional tuple

    Parameters
    ----------
    obj : Object
        Object that is converted to a tuple

    Returns
    -------
    t : tuple
        Tuple that includes the original object
    """
    if isinstance(obj, tuple):
        return obj
    elif isinstance(obj, str):
        return (obj,)
    return (obj,)


def get_first_member(tp):
    """
    Grabs the first element in a tuple, if a tuple is given as argument

    Parameters
    ----------
    tp : tuple

    """
    if isinstance(tp, tuple):
        if len(tp) == 1:
            return tp[0]
    return tp


def tuple_pack(obj):
    warnings.warn('Use sasoptpy.util.pack_to_tuple', DeprecationWarning)
    return pack_to_tuple(obj)


def quick_sum(argv):
    return sasoptpy.util.expr_sum(argv)


def expr_sum(argv):
    """
    Summation function for :class:`Expression` objects

    Returns
    -------
    exp : Expression
        Sum of given arguments

    Examples
    --------

    >>> x = so.VariableGroup(10000, name='x')
    >>> y = so.quick_sum(2*x[i] for i in range(10000))

    Notes
    -----

    This function is faster for expressions compared to Python's native sum()
    function.

    """
    clocals = argv.gi_frame.f_locals.copy()

    if sasoptpy.transfer_allowed:
        argv.gi_frame.f_globals.update(sasoptpy._transfer)

    exp = sasoptpy.core.Expression(temp=True)
    iterators = []
    for i in argv:
        exp = exp + i
        if sasoptpy.core.util.is_expression(i):
            if i._abstract:
                newlocals = argv.gi_frame.f_locals
                for nl in newlocals.keys():
                    if nl not in clocals and\
                       type(newlocals[nl]) == sasoptpy.data.SetIterator:
                        iterators.append((nl, newlocals[nl]))  # Tuple: nm ref
    if iterators:
        # First pass: make set iterators uniform
        for i in iterators:
            for j in iterators:
                if isinstance(i, sasoptpy.data.SetIterator) and\
                   isinstance(j, sasoptpy.data.SetIterator):
                    if i[0] == j[0]:
                        j[1]._name = i[1]._name
        it_names = []
        for i in iterators:
            unique = True
            for j in it_names:
                if i[0] == j[0]:
                    unique = False
                    break
            if unique:
                it_names.append(i)
        # Second pass: check for iterators
        iterators = [p[1] for p in it_names]
        exp = _check_iterator(exp, 'sum', iterators)
    exp._temp = False
    return exp


def load_function_containers():
    sasoptpy.container = None

    def read_statement_dictionary():
        d = dict()
        d[sasoptpy.core.Model.set_objective] = sasoptpy.abstract.statement.ObjectiveStatement.set_objective
        d[sasoptpy.core.Model.solve] = sasoptpy.abstract.statement.SolveStatement.solve
        d[sasoptpy.core.Variable.set_bounds] = sasoptpy.abstract.statement.Assignment.set_bounds
        d[sasoptpy.abstract.ParameterValue.set_value] = sasoptpy.abstract.statement.Assignment.set_value
        d[sasoptpy.core.Model.drop_constraint] = sasoptpy.abstract.statement.DropStatement.drop_constraint
        return d

    sasoptpy.statement_dictionary = read_statement_dictionary()


def _to_optmodel_loop(keys):
    s = ''
    subindex = []
    for key in keys:
        if isinstance(key, tuple):
            for i in flatten_tuple(key):
                subindex.append(str(i))
        elif not is_key_abstract(key):
            subindex.append(str(key))
    if subindex:
        s += '_' + '_'.join(subindex)
    iters = get_iterators(keys)
    conds = get_conditions(keys)
    if len(iters) > 0:
        s += ' {'
        s += ', '.join(iters)
        if len(conds) > 0:
            s += ': '
            s += ' and '.join(conds)
        s += '}'
    return s


def _recursive_walk(obj, func, attr=None, alt=None):
    """
    Calls a given method recursively for given objects


    Parameters
    ----------
    func : string
        Name of the method / function be called
    attr : string, optional
        An attribute which triggers an alternative method to be called if\
        exists
    alt : string, optional
        Name of the alternative method / function to be called if passed attr\
        exists for given objects

    Notes
    -----
    - This function is for internal consumption.

    """
    result = []
    for i in list(obj):
        if isinstance(i, list):
            result.append(recursive_walk(i, func))
        else:
            if attr is None:
                m_call = getattr(i, func)
                result.append(m_call())
            else:
                m_attr = getattr(i, attr)
                if m_attr:
                    m_call = getattr(i, alt)
                else:
                    m_call = getattr(i, func)
                result.append(m_call())
    return result


def is_set_abstract(arg):
    return sasoptpy.abstract.is_abstract_set(arg)


def get_iterators(keys):
    """
    Returns a list of definition strings for a given list of SetIterators
    """
    iterators = []
    groups = {}
    for key in keys:
        if is_key_abstract(key):
            iterators.append(key._defn())
        elif isinstance(key, tuple):
            for subkey in key:
                if hasattr(subkey, '_group'):
                    g = groups.setdefault(subkey._group, [])
                    g.append(subkey)
    if groups:
        for kg in groups.values():
            s = '<' + ','.join([i._name for i in kg]) + '> in ' +\
                kg[0]._set._name
            iterators.append(s)
    return iterators


def get_conditions(keys):
    conditions = []
    for key in keys:
        if is_key_abstract(key):
            if len(key._conditions) > 0:
                conditions.append(key._to_conditions())
    return conditions


def reset():
    """
    Deletes the references inside the global dictionary and restarts counters

    Examples
    --------

    >>> import sasoptpy as so
    >>> m = so.Model(name='my_model')
    >>> print(so.get_namespace())
    Global namespace:
        Model
               0 my_model <class 'sasoptpy.model.Model'>,\
               sasoptpy.Model(name='my_model', session=None)
        VariableGroup
        ConstraintGroup
        Expression
        Variable
        Constraint
    >>> so.reset()
    >>> print(so.get_namespace())
    Global namespace:
        Model
        VariableGroup
        ConstraintGroup
        Expression
        Variable
        Constraint

    See also
    --------
    :func:`get_namespace`

    """
    sasoptpy.__namedict.clear()
    for i in sasoptpy.__ctr:
        sasoptpy.__ctr[i] = [0]
    sasoptpy.config.reset()


def reset_globals():
    reset()


def get_mutable(exp):
    """
    Returns a mutable copy of the given expression if it is immutable

    Parameters
    ----------
    exp : Variable or Expression
        Object to be wrapped

    Returns
    -------
    r : Expression
        Mutable copy of the expression, if the original is immutable
    """
    if isinstance(exp, sasoptpy.Variable):
        r = sasoptpy.Expression(exp)
        r._abstract = exp._abstract
    elif isinstance(exp, sasoptpy.Expression):
        r = exp
    else:
        r = sasoptpy.components.Expression(exp)
    return r


def wrap_expression(e, abstract=False):
    """
    Wraps expression inside another expression
    """
    wrapper = sasoptpy.Expression()
    if hasattr(e, '_name') and e._name is not None:
        name = e._name
    else:
        name = assign_name(None, 'expr')
    if sasoptpy.core.util.is_expression(e):
        wrapper._linCoef[name] = {'ref': e, 'val': 1.0}
        wrapper._abstract = e._abstract or abstract
    elif isinstance(e, dict):
        wrapper._linCoef[name] = {**e}
    return wrapper


def get_and_increment_counter(ctrtype):
    """
    Returns and increments the list counter for naming

    Parameters
    ----------
    ctrtype : string
        Type of the counter, 'obj', 'var', 'con' or 'expr'

    Returns
    -------
    ctr : int
        Current value of the counter
    """
    ctr = sasoptpy.__ctr[ctrtype]
    ctr[0] = ctr[0] + 1
    return ctr[0]


def dict_to_frame(dictobj, cols=None):
    """
    Converts dictionaries to DataFrame objects for pretty printing

    Parameters
    ----------
    dictobj : dict
        Dictionary to be converted
    cols : list, optional
        Column names

    Returns
    -------
    frobj : DataFrame
        DataFrame representation of the dictionary

    Examples
    --------

    >>> d = {'coal': {'period1': 1, 'period2': 5, 'period3': 7},
    >>>      'steel': {'period1': 8, 'period2': 4, 'period3': 3},
    >>>      'copper': {'period1': 5, 'period2': 7, 'period3': 9}}
    >>> df = so.dict_to_frame(d)
    >>> print(df)
            period1  period2  period3
    coal          1        5        7
    copper        5        7        9
    steel         8        4        3

    """
    frobj = pd.convert_dict_to_frame(dictobj, cols)
    return frobj


def flatten_tuple(tp):
    """
    Flattens nested tuples

    Parameters
    ----------

    tp : tuple
        Nested tuple to be flattened

    Returns
    -------
    elem : Generator-type
        A generator-type object representing the flat tuple

    Examples
    --------
    >>> tp = (3, 4, (5, (1, 0), 2))
    >>> print(list(so.flatten_tuple(tp)))
    [3, 4, 5, 1, 0, 2]

    """
    for elem in tp:
        if isinstance(elem, tuple):
            yield from flatten_tuple(elem)
        else:
            yield elem




