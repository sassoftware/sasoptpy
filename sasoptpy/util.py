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


from collections import Iterable
import random
import string
import warnings
from contextlib import contextmanager

import sasoptpy
from sasoptpy._libs import (pd, np)


def load_package_globals():

    # Constant values
    sasoptpy.MIN = 'MIN'
    sasoptpy.MAX = 'MAX'
    sasoptpy.CONT = 'CONT'
    sasoptpy.INT = 'INT'
    sasoptpy.BIN = 'BIN'
    sasoptpy.STR = 'str'
    sasoptpy.NUM = 'num'

    sasoptpy.LSO = 'lso'
    sasoptpy.MIP = 'mip'
    sasoptpy.LP = 'lp'
    sasoptpy.QP = 'qp'

    sasoptpy.N = '_N_'

    # Container for wrapped statements
    sasoptpy._transfer = {}
    sasoptpy.transfer_allowed = False

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
        'min': sasoptpy.MIN,
        'string': sasoptpy.STR,
        'str': sasoptpy.STR,
        'number': sasoptpy.NUM,
        'num': sasoptpy.NUM
    }

    sasoptpy.itemid = 0


def get_creation_id():
    sasoptpy.itemid += 1
    return sasoptpy.itemid

def get_next_name():
    return 'o' + str(get_creation_id())


def is_existing_object(obj):
    if obj.get_name() is None:
        return False
    elif get_obj_by_name(obj.get_name()):
        return True
    else:
        return False

def need_name_assignment(obj, name):
    if obj.get_name() is None:
        return True
    elif obj.get_name() == name:
        return False
    else:
        return True

def set_creation_order_if_empty(obj):
    if hasattr(obj, '_objorder') and not obj._objorder:
        obj._objorder = get_creation_id()


def load_function_containers():
    sasoptpy.container = None

    def read_statement_dictionary():
        d = dict()
        d[sasoptpy.core.Model.set_objective] = sasoptpy.abstract.statement.ObjectiveStatement.set_objective_of_model
        d[sasoptpy.core.Model.solve] = sasoptpy.abstract.statement.SolveStatement.solve
        d[sasoptpy.core.Variable.set_bounds] = sasoptpy.abstract.statement.Assignment.set_bounds
        d[sasoptpy.abstract.ParameterValue.set_value] = sasoptpy.abstract.statement.Assignment.set_value
        d[sasoptpy.core.Model.drop_constraint] = sasoptpy.abstract.statement.DropStatement.drop_constraint
        d[sasoptpy.core.util.read_data] = sasoptpy.abstract.statement.ReadDataStatement.read_data
        return d

    sasoptpy.statement_dictionary = read_statement_dictionary()


def load_default_mediators():
    sasoptpy.mediators['CAS'] = sasoptpy.interface.CASMediator
    sasoptpy.mediators['SAS'] = sasoptpy.interface.SASMediator


def submit(caller, *args, **kwargs):
    session = caller.get_session()
    session_type = get_session_type(session)
    if session is None or session_type is None:
        raise RuntimeError('No session is available')

    mediator_class = sasoptpy.mediators[session_type]
    mediator = mediator_class(caller, session)
    return mediator.submit(*args, **kwargs)


def submit_for_solve(caller, *args, **kwargs):
    session = caller.get_session()
    session_type = get_session_type(session)
    if session is None or session_type is None:
        raise RuntimeError('No session is available')

    mediator_class = sasoptpy.mediators[session_type]
    mediator = mediator_class(caller, session)
    return mediator.solve(*args, **kwargs)


def register_to_function_container(func1, func2):
    sasoptpy.statement_dictionary[func1] = func2


def get_in_digit_format(val):
    """
    Returns a value by rounding it to config digits

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
        return round(val, digits)
    return val


def round_digits(val):
    digits = sasoptpy.config['print_digits']
    if digits and digits > 0:
        return round(val, digits)
    return val


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


def tuple_unpack(tp):
    warnings.warn('Use sasoptpy.util.get_first_member', DeprecationWarning)
    return get_first_member(tp)


def tuple_pack(obj):
    warnings.warn('Use sasoptpy.util.pack_to_tuple', DeprecationWarning)
    return pack_to_tuple(obj)


def pack_to_list(obj):
    it = type(obj)
    if it == list:
        return obj
    else:
        return [obj]


def list_pack(obj):
    warnings.warn('Use sasoptpy.util.pack_to_list', DeprecationWarning)
    return pack_to_list(obj)


def _list_item(obj):
    warnings.warn('Use sasoptpy.util.pack_to_list', DeprecationWarning)
    return pack_to_list(obj)


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

    exp = sasoptpy.core.Expression()
    exp.set_temporary()
    iterators = []
    for i in argv:
        exp = exp + i
        if sasoptpy.core.util.is_expression(i):
            if i._abstract:
                newlocals = argv.gi_frame.f_locals
                for nl in newlocals.keys():
                    if nl not in clocals and\
                       type(newlocals[nl]) == sasoptpy.abstract.SetIterator:
                        iterators.append((nl, newlocals[nl]))  # Tuple: nm ref
                        try:
                            newlocals[nl].set_name(nl)
                        except:
                            pass
    if iterators:
        # First pass: make set iterators uniform
        for i in iterators:
            for j in iterators:
                if isinstance(i, sasoptpy.abstract.SetIterator) and\
                   isinstance(j, sasoptpy.abstract.SetIterator):
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
        # Reorder iterators
        iterators = sorted(iterators, key=lambda i: i._objorder)
        exp = _wrap_expression_with_iterators(exp, 'sum', iterators)
    exp._temp = False
    return exp


def _wrap_expression_with_iterators(exp, operator, iterators):
    if isinstance(exp, sasoptpy.core.Variable):
        r = exp.copy()
    else:
        r = exp
    if r._name is None:
        r._name = get_next_name()
    if r._operator is None:
        r._operator = operator
    for i in iterators:
        if isinstance(i, sasoptpy.abstract.SetIterator):
            r._iterkey.append(i)
    wrapper = sasoptpy.core.Expression()
    wrapper._linCoef[r._name] = {'ref': r, 'val': 1.0}
    wrapper._abstract = True
    return wrapper





def _to_optmodel_loop(keys):
    s = ''
    subindex = []
    for key in keys:
        if isinstance(key, tuple):
            for i in flatten_tuple(key):
                subindex.append(str(i))
        elif not is_key_abstract(key):
            subindex.append(safe_string(str(key)))
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

def is_abstract(arg):
    return hasattr(arg, '_abstract') and arg._abstract

def is_comparable(arg):
    forbidden_types = [pd.Series, pd.DataFrame, dict, tuple]
    if any(isinstance(arg, f) for f in forbidden_types):
        return False
    else:
        return True

def is_model(arg):
    return isinstance(arg, sasoptpy.core.Model)

def is_workspace(arg):
    return isinstance(arg, sasoptpy.session.Workspace)

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
    #reset_globals()
    sasoptpy.config.reset()
    sasoptpy.itemid = 0


def reset_globals():
    reset()
    #print('RESET GLOBALS IS CALLED')
    # sasoptpy.__namedict.clear()
    # for i in sasoptpy.__ctr:
    #     sasoptpy.__ctr[i] = [0]


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
        r = sasoptpy.core.Expression(exp)
    return r


def wrap_expression(e, abstract=False):
    """
    Wraps expression inside another expression
    """
    wrapper = sasoptpy.Expression()

    if hasattr(e, '_name') and e._name is not None:
        name = e._name
    else:
        name = get_next_name()

    if sasoptpy.core.util.is_expression(e):
        wrapper.set_member(key=name, ref=e, val=1)
        wrapper._abstract = e._abstract or abstract
    elif isinstance(e, dict):
        wrapper._linCoef[name] = {**e}
    elif isinstance(e, str):
        wrapper = sasoptpy.abstract.Auxiliary(base=e)
    elif np.isinstance(type(e), np.number):
        wrapper += e

    return wrapper


def wrap(e, abstract=False):
    warnings.warn('Use sasoptpy.util.wrap_expression', DeprecationWarning)
    return wrap_expression(e, abstract)


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


def flatten_frame(df, swap=False):
    """
    Converts a :class:`pandas.DataFrame` object into :class:`pandas.Series`

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        DataFrame to be flattened
    swap : boolean, optional
        Option to use columns as first index

    Returns
    -------
    new_frame : :class:`pandas.DataFrame`
        A new DataFrame where indices consist of index and columns names as
        tuples

    Examples
    --------

    >>> price = pd.DataFrame([
    >>>     [1, 5, 7],
    >>>     [8, 4, 3],
    >>>     [5, 7, 9]], columns=[\'period1\', \'period2\', \'period3\']).\\
    >>>     set_index([[\'coal\', \'steel\', \'copper\']])
    >>> print(\'Price data: \\n{}\'.format(price))
    >>> price_f = so.flatten_frame(price)
    >>> print(\'Price data: \\n{}\'.format(price_f))
    Price data:
            period1  period2  period3
    coal          1        5        7
    steel         8        4        3
    copper        5        7        9
    Price data:
    (coal, period1)      1
    (coal, period2)      5
    (coal, period3)      7
    (steel, period1)     8
    (steel, period2)     4
    (steel, period3)     3
    (copper, period1)    5
    (copper, period2)    7
    (copper, period3)    9
    dtype: int64

    """
    new_frame = df.stack()
    if swap:
        new_frame = new_frame.swaplevel()
    new_frame.index = new_frame.index.to_series()
    return new_frame


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


def _to_optmodel_expr(item):
    expr_func = getattr(item, "_expr", None)
    if callable(expr_func):
        return item._expr()
    else:
        return str(item)


def _to_optmodel_quoted_string(item):
    if isinstance(item, int):
        return str(item)
    elif isinstance(item, str):
        return "'{}'".format(item)
    elif isinstance(item, tuple):
        return '<' + ','.join(_to_optmodel_quoted_string(j) for j in item) + '>'
    else:
        return str(item)


def _to_quoted_string(item):
    warnings.warn('Use _to_optmodel_quoted_string', DeprecationWarning)
    return _to_optmodel_quoted_string(item)


def read_frame(df, cols=None):
    """
    Reads each column in :class:`pandas.DataFrame` into a list of\
    :class:`pandas.Series` objects

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        DataFrame to be read
    cols : list of strings, optional
        Column names to be read. By default, it reads all columns

    Returns
    -------
    series : list
        List of :class:`pandas.Series` objects

    Examples
    --------

    >>> price = pd.DataFrame([
    >>>     [1, 5, 7],
    >>>     [8, 4, 3],
    >>>     [5, 7, 9]], columns=['period1', 'period2', 'period3']).\\
    >>>     set_index([['coal', 'steel', 'copper']])
    >>> [period2, period3] = so.read_frame(price, ['period2', 'period3'])
    >>> print(period2)
    coal      5
    steel     4
    copper    7
    Name: period2, dtype: int64

    """
    series = []
    if cols is None:
        cols = df.columns
    for col in cols:
        if col in df.columns:
            series.append(df[col])
        else:
            raise IndexError('Column name {} does not exist'.format(col))
    return series


# TODO this function is too long, needs to be split
def get_solution_table(*argv, key=None, sort=False, rhs=False):
    """
    Returns the requested variable names as a DataFrame table

    Parameters
    ----------
    key : list, optional
        Keys for objects
    sort : bool, optional
        Option for sorting the keys
    rhs : bool, optional
        Option for including constant values

    Returns
    -------
    soltable : :class:`pandas.DataFrame`
        DataFrame object that holds keys and values
    """
    soltable = []
    listofkeys = []
    keylengths = []
    # Get dimension from first argv
    if len(argv) == 0:
        return None

    if key is None:
        for i, _ in enumerate(argv):
            if isinstance(argv[i], Iterable):
                if isinstance(argv[i], sasoptpy.core.VariableGroup):
                    currentkeylist = list(argv[i]._vardict.keys())
                    for m in argv[i]._vardict:
                        if argv[i]._vardict[m]._abstract:
                            continue
                        m = get_first_member(m)
                        if m not in listofkeys:
                            listofkeys.append(m)
                    keylengths.append(list_length(
                        currentkeylist[0]))
                elif isinstance(argv[i], sasoptpy.core.ConstraintGroup):
                    currentkeylist = list(argv[i]._condict.keys())
                    for m in argv[i]._condict:
                        m = get_first_member(m)
                        if m not in listofkeys:
                            listofkeys.append(m)
                    keylengths.append(list_length(
                        currentkeylist[0]))
                elif (isinstance(argv[i], pd.Series) or
                      (isinstance(argv[i], pd.DataFrame) and
                      len(argv[i].columns) == 1)):
                    # optinal method: converting to series, argv[i].iloc[0]
                    currentkeylist = argv[i].index.values
                    for m in currentkeylist:
                        m = get_first_member(m)
                        if m not in listofkeys:
                            listofkeys.append(m)
                    keylengths.append(list_length(
                        currentkeylist[0]))
                elif isinstance(argv[i], pd.DataFrame):
                    index_list = argv[i].index.tolist()
                    col_list = argv[i].columns.tolist()
                    for m in index_list:
                        for n in col_list:
                            current_key = pack_to_tuple(m) + pack_to_tuple(n)
                            if current_key not in listofkeys:
                                listofkeys.append(current_key)
                    keylengths.append(list_length(
                        current_key))
                elif isinstance(argv[i], dict):
                    currentkeylist = list(argv[i].keys())
                    for m in currentkeylist:
                        m = get_first_member(m)
                        if m not in listofkeys:
                            listofkeys.append(m)
                    keylengths.append(list_length(
                        currentkeylist[0]))
                elif isinstance(argv[i], sasoptpy.core.Expression):
                    if ('',) not in listofkeys:
                        listofkeys.append(('',))
                        keylengths.append(1)
                else:
                    print('Unknown type: {} {}'.format(type(argv[i]), argv[i]))
            else:
                if ('',) not in listofkeys:
                    listofkeys.append(('',))
                    keylengths.append(1)

        if sort:
            try:
                listofkeys = sorted(listofkeys,
                                    key=_sort_tuple)
            except TypeError:
                listofkeys = listofkeys

        maxk = max(keylengths)
    else:
        maxk = max(len(i) if isinstance(i, tuple) else 1 for i in key)
        listofkeys = key

    for k in listofkeys:
        if isinstance(k, tuple):
            row = list(k)
        else:
            row = [k]
        if list_length(k) < maxk:
            row.extend(['-']*(maxk-list_length(k)))
        for i, _ in enumerate(argv):
            if type(argv[i]) == sasoptpy.core.VariableGroup:
                tk = pack_to_tuple(k)
                if tk not in argv[i]._vardict or argv[i][tk]._abstract:
                    val = '-'
                else:
                    val = argv[i][tk].get_value()
                row.append(val)
            elif type(argv[i]) == sasoptpy.core.Variable:
                val = argv[i].get_value() if k == ('',) else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.core.Constraint:
                val = argv[i].get_value(rhs=rhs) if k == ('',) else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.core.ConstraintGroup:
                tk = pack_to_tuple(k)
                val = argv[i][tk].get_value()\
                    if tk in argv[i]._condict else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.core.Expression:
                val = argv[i].get_value() if k == ('',) else '-'
                row.append(val)
            elif type(argv[i]) == pd.Series:
                if k in argv[i].index.tolist():
                    if type(argv[i][k]) == sasoptpy.core.Expression:
                        val = argv[i][k].get_value()
                    else:
                        val = argv[i][k]
                else:
                    val = '-'
                row.append(val)
            elif (type(argv[i]) == pd.DataFrame and
                  len(argv[i].columns) == 1):
                for j in argv[i]:
                    if k in argv[i].index.tolist():
                        cellv = argv[i].loc[k, j]
                        if type(cellv) == pd.Series:
                            cellv = cellv.iloc[0]
                        if type(cellv) == sasoptpy.core.Expression:
                            row.append(cellv.get_value())
                        else:
                            row.append(argv[i].loc[k, j])
                    elif pack_to_tuple(k) in argv[i].index.tolist():
                        tk = pack_to_tuple(k)
                        cellv = argv[i].loc[tk, j]
                        if type(cellv) == pd.Series:
                            cellv = cellv.iloc[0]
                        if type(cellv) == sasoptpy.core.Expression:
                            row.append(cellv.get_value())
                        else:
                            row.append(argv[i].loc[tk, j])
                    else:
                        row.append('-')
            elif type(argv[i]) == pd.DataFrame:
                arg_series = argv[i].stack()
                arg_series.index = arg_series.index.to_series()
                if k in arg_series.index.values.tolist():
                    if type(arg_series[k]) == sasoptpy.core.Expression:
                        val = arg_series[k].get_value()
                    else:
                        val = arg_series[k]
                else:
                    val = '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.abstract.ImplicitVar:
                tk = pack_to_tuple(k)
                if tk in argv[i]._dict:
                    row.append(argv[i][tk].get_value())
                else:
                    row.append('-')
            elif isinstance(argv[i], dict):
                if k in argv[i]:
                    tk = pack_to_tuple(k)
                    if type(argv[i][tk]) == sasoptpy.core.Expression:
                        row.append(argv[i][tk].get_value())
                    elif np.issubdtype(type(argv[i][tk]), np.number):
                        row.append(argv[i][tk])
                    else:
                        row.append('-')
                else:
                    row.append('-')
            else:
                try:
                    row.append(str(argv[i][k]))
                except TypeError:
                    row.append('-')
        soltable.append(row)
    indexlen = len(soltable[0])-len(argv)
    indexcols = [i+1 for i in range(indexlen)]
    inputcols = []
    for a in argv:
        if isinstance(a, pd.DataFrame) and len(a.columns.tolist()) == 1:
            inputcols.extend(a.columns.values.tolist())
        else:
            try:
                inputcols.append(a._name)
            except AttributeError:
                if isinstance(a, pd.DataFrame):
                    inputcols.append('DataFrame')
                elif isinstance(a, dict):
                    inputcols.append('dict')
                else:
                    inputcols.append('arg: {}'.format(a))
    colnames = indexcols + inputcols
    soltablep = pd.DataFrame(soltable, columns=colnames)
    soltablep2 = soltablep.set_index(indexcols)
    pd.display_dense()
    pd.display_all()
    return soltablep2


def list_length(listobj):
    """
    Returns the length of an object if it is a list, tuple or dict

    Parameters
    ----------
    listobj : list, tuple or dict
        Object whose length will be returned

    Returns
    -------
    ln : int
        Length of the list, tuple or dict
    """
    if (isinstance(listobj, list) or isinstance(listobj, tuple) or
            isinstance(listobj, dict)):
        return len(listobj)
    else:
        return 1


def _sort_tuple(i):
    i = pack_to_tuple(i)
    key = (len(i),)
    for s in i:
        if isinstance(s, str):
            key += (0,)
        elif np.isinstance(type(s), np.number):
            key += (1,)
        elif isinstance(s, tuple):
            key += (2,)
    key += i
    return key


#TODO Both read_table and read_data functions are too long and out of place
def read_table(table, session=None, key=None, key_type=None, key_name=None,
               columns=None, col_types=None, col_names=None,
               upload=False, casout=None, ref=True):
    """
    Reads a CAS Table or pandas DataFrame

    Parameters
    ----------
    table : :class:`swat.cas.table.CASTable`, :class:`pandas.DataFrame`\
            object or string
        Pointer to CAS Table (server data, CASTable),\
        DataFrame (local data) or\
        the name of the table at execution (server data, string)
    session : :class:`swat.CAS` or :class:`saspy.SASsession`
        Session object if the table will be uploaded
    key : list, optional
        List of key columns (for CASTable) or index columns (for DataFrame)
    key_type : list or string, optional
        A list of column types consists of 'num' or 'str' values
    key_name : string, optional
        Name of the key set
    columns : list, optional
        List of columns to read into parameters
    col_types : dict, optional
        Dictionary of column types
    col_names : dict, optional
        Dictionary of column names
    upload : boolean, optional
        Option for uploading a local data to CAS server first
    casout : string or dict, optional
        Casout options if data is uploaded
    ref : boolean, optional
        Switch for returning the read data statement generated by the function

    Returns
    -------
    t : tuple
        A tuple where first element is the key (index), second element\
        is a list of requested columns and the last element is reference to\
        the original

    See also
    --------
    :func:`Model.read_table`
    :func:`Model.read_data`

    """

    if key is None:
        key = ['_N_']
    if key_type is None:
        key_type = ['num']
    if col_types is None:
        col_types = dict()
    if col_names is None:
        col_names = dict()

    # Type of the given table and the session
    t_type = type(table).__name__
    s_type = type(session).__name__

    if upload and t_type == 'DataFrame' and s_type == 'CAS':
        table = session.upload_frame(table, casout=casout)
    elif upload and t_type == 'Series' and s_type == 'CAS':
        table = pd.DataFrame(table)
        table = session.upload_frame(table, casout=casout)
    elif upload and t_type == 'DataFrame' and s_type == 'SAS':
        req_name = casout if isinstance(casout, str) else None
        upname = sasoptpy.util.assign_name(req_name, 'table')
        sasoptpy.util.register_globally(upname, table)
        table = session.df2sd(table, table=upname)

    t_type = type(table).__name__

    if type(table).__name__ == 'CASTable':
        tname = table.name
    elif type(table).__name__ == 'SASdata':
        tname = table.table
    elif type(table) == str:
        tname = table
    else:
        tname = str(table)

    pars = []
    dat = None

    if t_type == 'CASTable' or t_type == 'SASdata' or t_type == 'str':
        if not key or key == [None]:
            key = ['_N_']
        if key_name is None:
            key_name = 'set_' + ('_'.join([str(i) for i in key]) if key != ['_N_'] else tname + '_N')
        keyset = sasoptpy.abstract.Set(
            name=key_name,
            settype=key_type)
        pars = []
        if columns is None:
            columns = table.columns.tolist()

        for col in columns:
            if isinstance(col, str):
                coltype = col_types.get(col, 'num')
                colname = col_names.get(col, col)
                #current_param = sasoptpy.abstract.Parameter(name=colname, keys=[keyset],
                #                                        p_type=coltype)
                current_param = sasoptpy.abstract.ParameterGroup(
                    keyset, name=colname, ptype=coltype)
                pars.append({'param': current_param, 'column': col})
            elif isinstance(col, dict):
                coltype = col_types.get(col['name'], 'num')
                colname = col_names.get(col['name'], col['name'])
                current_param = sasoptpy.abstract.Parameter(name=colname, keys=[keyset],
                                                        p_type=coltype)
                col['param'] = current_param
                pars.append(col)

        dat = read_data(table, key_set=keyset, key_cols=key, params=pars)
    elif t_type == 'DataFrame':
        if key and key != [None] and key != ['_N_']:
            table = table.set_index(key)
        keyset = table.index.tolist()
        pars = []
        if columns is None:
            columns = list(table)
        for col in columns:
            pars.append({'param': table[col]})
    elif t_type == 'Series':
        keyset = table.index.tolist()
        pars = [{'param': table}]
    else:
        print('ERROR: Data type is not recognized in read_table: {} ({})'
              .format(table, type(table)))
        return None

    par_refs = [p['param'] for p in pars]

    if ref:
        return (keyset, par_refs, dat)
    elif not pars:
        return (keyset, par_refs)
    else:
        return keyset


def read_data(table, key_set, key_cols=None, option='', params=None):
    """
    (Experimental) Reads a CASTable into PROC OPTMODEL sets

    Parameters
    ----------
    table : :class:`swat.cas.table.CASTable`
        The CAS table to be read to sets and parameters
    key_set : Set
        Set object to be read as the key (index)
    key_cols : list or string, optional
        Column names of the key columns
    option : string, optional
        Additional options for read data command
    params : list, optional
        A list of dictionaries where each dictionary represent parameters

    Notes
    -----
    - `key_set` and `key_cols` parameters should be a list. When passing
      a single item, string type can be used instead.
    """

    if key_cols is None:
        key_cols = []
    if params is None:
        params = []

    # Reading key
    if key_set is not None and key_cols:
        key_set._colname = key_cols

    # Reading parameters
    for p in params:
        p.setdefault('column', None)
        p.setdefault('index', None)
        p['param']._set_loop(table, key_set, p['column'], p['index'])

    # Beginning
    if type(table).__name__ == 'CASTable':
        s = 'read data {}'.format(table.name)
    elif type(table).__name__ == 'SASdata':
        s = 'read data {}'.format(table.table)
    else:
        s = 'read data {}'.format(table)
    if option:
        s += ' {}'.format(option)
    s += ' into '
    # Key part
    if key_set is not None:
        s += '{}=[{}] '.format(key_set._name, ' '.join(key_set._colname))
    else:
        s += '[{}] '.format(' '.join(key_set._colname))
    # Parameter list
    parlist = []
    for p in params:
        parlist.append(p['param']._to_read_data())
    s += ' '.join(parlist)
    s += ';'
    return sasoptpy.abstract.OldStatement(s)


def _to_sas_string(obj):
    if hasattr(obj, '_expr'):
        return obj._expr()
    elif isinstance(obj, str):
        return "'{}'".format(obj)
    elif isinstance(obj, tuple):
        return ', '.join(_to_sas_string(i) for i in obj)
    elif isinstance(obj, list):
        return '{{{}}}'.format(','.join([_to_sas_string(i) for i in obj]))
    elif isinstance(obj, range):
        if obj.step == 1:
            return '{}..{}'.format(_to_sas_string(obj.start), _to_sas_string(obj.stop))
        else:
            return '{}..{} by {}'.format(_to_sas_string(obj.start), _to_sas_string(obj.stop), _to_sas_string(obj.step))
    elif np.isinstance(type(obj), np.number):
        return str(obj)
    else:
        print('WARNING: Unknown type to transform {}'.format(type(obj)))
        return '{}'.format(str(obj))


def _insert_brackets(prefix, keys):
    if keys is None:
        return prefix
    else:
        s = prefix + '['
        k = pack_to_tuple(keys)
        s += ', '.join(_to_iterator_expression(k))
        s += ']'
        return s


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


def _to_bracket(prefix, keys):
    warnings.warn('Use sasoptpy.util._insert_brackets', DeprecationWarning)
    return _insert_brackets(prefix, keys)


def exp_range(start, stop, step=1):
    """
    Creates a set within given range

    Parameters
    ----------
    start : Expression
        First value of the range
    stop : Expression
        Last value of the range
    step : Expression, optional
        Step size of the range

    Returns
    -------
    exset : Set
        Set that represents the range

    Examples
    --------

    >>> N = so.Parameter(name='N')
    >>> p = so.exp_range(1, N)
    >>> print(p._defn())
    set 1..N;

    """
    regular = isinstance(start, int) and isinstance(stop, int) and\
        isinstance(step, int)
    if regular:
        return range(start, stop, step)
    s = sasoptpy.abstract.AbstractRange(start, stop, step)
    return s


def get_python_symbol(symbol):
    if symbol == '^':
        return '**'
    else:
        return symbol


def safe_string(st):
    return "".join(c if c.isalnum() else '_' for c in st)


def to_expression(item):
    if hasattr(item, '_expr'):
        return item._expr()
    else:
        return _to_sas_string(item)


def to_definition(item):
    return item._defn()


def to_optmodel(item, **kwargs):
    return sasoptpy.interface.to_optmodel(item, **kwargs)


def is_linear(item):
    return item._is_linear()


def get_object_order(obj):
    return getattr(obj, '_objorder', None)

def get_attribute_definitions(members):
    definitions = [_attribute_to_defn(i) for i in members]
    defn = '\n'.join(definitions)
    return defn

def _attribute_to_defn(d):
    expr = to_expression
    if d['key'] == 'init':
        return '{} = {};'.format(expr(d['ref']), d['value'])
    if d['key'] == 'lb' or d['key'] == 'ub':
        return '{}.{} = {};'.format(expr(d['ref']), d['key'], d['value'])
    raise NotImplementedError('Attribute {} definition is not implemented'.format(
        d['key']
    ))

def addSpaces(s, space):
    white = ' '*space
    return white + white.join(s.splitlines(1))

def get_session_type(sess):
    if sess is None:
        return None
    else:
        sess_type = type(sess).__name__
        if sess_type == 'CAS':
            return 'CAS'
        elif sess_type == 'SASsession':
            return 'SAS'
        else:
            return None

def safe_variable_name(name):
    return name.replace(' ', '_').replace('\'', '')

def get_group_name(name):
    return name.split('[')[0]

@contextmanager
def iterate(set, name):
    yield sasoptpy.abstract.SetIterator(set, name=name)

def concat(exp1, exp2):
    return wrap_expression(exp1).concat(wrap_expression(exp2))

def has_expr(e):
    return hasattr(e, '_expr')
