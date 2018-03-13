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
import inspect
import random
import string

import numpy as np
import pandas as pd

import sasoptpy.model
import sasoptpy.components


# Constant values
MIN = 'MIN'
MAX = 'MAX'
CONT = 'CONT'
INT = 'INT'
BIN = 'BIN'

# Global dictionary
__namedict = {}

# Counters
__ctr = {'obj': [0], 'var': [0], 'con': [0], 'expr': [0], 'model': [0],
         'i':[0], 'param': [0]}


def check_name(name, ctype=None):
    '''
    Checks if a name is in valid and returns a random string if not

    Parameters
    ----------
    name : str
        Name to be checked if unique

    Returns
    -------
    str : The given name if valid, a random string otherwise
    '''
    if name is None:
        if ctype is None:
            name = ''.join(random.choice(string.ascii_lowercase) for
                           _ in range(5))
        else:
            name = '{}_{}'.format(ctype, get_counter(ctype))
    else:
        if name in __namedict:
            if ctype is None:
                name = ''.join(random.choice(string.ascii_lowercase) for
                               _ in range(5))
            else:
                name = '{}_{}'.format(ctype, get_counter(ctype))
        else:
            name = name.replace(" ", "_")
    while name in __namedict:
        if ctype is None:
            name = ''.join(random.choice(string.ascii_lowercase) for
                           _ in range(5))
        else:
            name = '{}_{}'.format(ctype, get_counter(ctype))
    return name


def _is_generated(expr):
    if isinstance(expr, sasoptpy.components.Variable):
        return
    caller = inspect.stack()[2][3]
    if caller == '<genexpr>':
        return True


def register_name(name, obj):
    '''
    Adds the name of a component into the global reference list
    '''
    __namedict[name] = obj


def quick_sum(argv):
    '''
    Quick summation function for :class:`Expression` objects

    Returns
    -------
    :class:`Expression` object
        Sum of given arguments

    Examples
    --------

    >>> x = so.VariableGroup(10000, name='x')
    >>> y = so.quick_sum(2*x[i] for i in range(10000))

    Notes
    -----

    This function is faster for expressions compared to Python's native sum()
    function.

    '''
    clocals = argv.gi_frame.f_locals.copy()
    exp = sasoptpy.components.Expression(temp=True)
    for i in argv:
        exp = exp + i
        if isinstance(i, sasoptpy.components.Expression):
            if i._abstract:
                newlocals = argv.gi_frame.f_locals
                iterators = []
                for nl in newlocals.keys():
                    if nl not in clocals:
                        iterators.append(newlocals[nl])
                exp = _check_iterator(exp, 'sum', iterators)
    exp._temp = False
    return exp


def _check_iterator(exp, operand, iterators):
    if isinstance(exp, sasoptpy.components.Variable):
        r = exp.copy()
    else:
        r = exp
    if r._name is None:
        r._name = check_name(None, 'expr')
    if r._operand is None:
        r._operand = operand
    for i in iterators:
        if isinstance(i, sasoptpy.data.SetIterator):
            r._iterkey.append(i)
    return r


def get_obj_by_name(name):
    '''
    Returns the reference to an object by using the unique name

    Returns
    -------
    object
        Reference to the object that has the name

    Notes
    -----

    If there is a conflict in the namespace, you might not get the object
    you request. Clear the namespace using
    :func:`reset_globals` when needed.

    See Also
    --------
    :func:`reset_globals`

    Examples
    --------

    >>> m.add_variable(name='var_x', lb=0)
    >>> m.add_variables(2, name='var_y', vartype=so.INT)
    >>> x = so.get_obj_by_name('var_x')
    >>> y = so.get_obj_by_name('var_y')
    >>> print(x)
    >>> print(y)
    >>> m.add_constraint(x + y[0] <= 3, name='con_1')
    >>> c1 = so.get_obj_by_name('con_1')
    >>> print(c1)
    var_x
    Variable Group var_y
    [(0,): Variable [ var_y_0 | INT ]]
    [(1,): Variable [ var_y_1 | INT ]]
    var_x  +  var_y_0  <=  3

    '''
    if name in __namedict:
        return __namedict[name]
    else:
        return None


def dict_to_frame(dictobj, cols=None):
    '''
    Converts dictionaries to DataFrame objects for pretty printing

    Parameters
    ----------
    dictobj : dict
        Dictionary to be converted
    cols : list, optional
        Column names

    Returns
    -------
    :class:`DataFrame` object
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

    '''
    frobj = pd.DataFrame.from_dict(dictobj, orient='index')
    if isinstance(cols, list):
        frobj.columns = cols
    if isinstance(frobj.index[0], tuple):
        frobj.index = pd.MultiIndex.from_tuples(frobj.index)
    return frobj


def extract_argument_as_list(inp):

    if isinstance(inp, int):
        thelist = list(range(0, inp))
    elif isinstance(inp, range):
        thelist = list(inp)
    elif isinstance(inp, tuple):
        thelist = inp[0]
    elif isinstance(inp, list):
        thelist = inp
    elif isinstance(inp, sasoptpy.data.Set):
        thelist = [inp]
    else:
        thelist = list(inp)
    return thelist


def extract_list_value(tuplist, listname):
    '''
    Extracts values inside various object types

    Parameters
    ----------
    tuplist : tuple
        Key combination to be extracted
    listname : dict or list or int or float or DataFrame or Series object
        List where the value will be extracted

    Returns
    -------
    object
        Corresponding value inside listname
    '''
    if listname is None:
        v = None
    elif isinstance(listname, dict):
        v = listname[tuple_unpack(tuplist)]
    elif np.issubdtype(type(listname), np.number):
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


def list_length(listobj):
    '''
    Returns the length of an object if it is a list, tuple or dict

    Parameters
    ----------
    listobj : Python object

    Returns
    -------
    int
        Length of the list, tuple or dict, otherwise 1
    '''
    if (isinstance(listobj, list) or isinstance(listobj, tuple) or
            isinstance(listobj, dict)):
        return len(listobj)
    else:
        return 1


def get_counter(ctrtype):
    '''
    Returns and increments the list counter for naming

    Parameters
    ----------
    ctrtype : string
        Type of the counter, 'obj', 'var', 'con' or 'expr'

    Returns
    -------
    int
        Current value of the counter
    '''
    ctr = __ctr[ctrtype]
    ctr[0] = ctr[0] + 1
    return ctr[0]


def tuple_unpack(tp):
    '''
    Grabs the first element in a tuple, if a tuple is given as argument

    Parameters
    ----------
    tp : tuple

    Returns
    -------
    object
        The first object inside the tuple.
    '''
    if isinstance(tp, tuple):
        if len(tp) == 1:
            return tp[0]
    return tp


def tuple_pack(obj):
    '''
    Converts a given object to a tuple object

    If the object is a tuple, the function returns itself, otherwise creates
    a single dimensional tuple.

    Parameters
    ----------
    obj : Object
        Object that is converted to tuple

    Returns
    -------
    tuple
        Corresponding tuple to the object.
    '''
    if isinstance(obj, tuple):
        return obj
    elif isinstance(obj, str):
        return (obj,)
    return (obj,)


def reset_globals():
    '''
    Deletes the references inside the global dictionary and restarts counters

    Examples
    --------

    >>> import sasoptpy as so
    >>> m = so.Model(name='my_model')
    >>> print(so.get_namespace())
    Global namespace:
        Model
               0 my_model <class 'sasoptpy.model.Model'>, sasoptpy.Model(name='my_model', session=None)
        VariableGroup
        ConstraintGroup
        Expression
        Variable
        Constraint
    >>> so.reset_globals()
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

    '''
    __namedict.clear()
    for i in __ctr:
        __ctr[i] = [0]


def read_frame(df, cols=None):
    '''
    Reads each column in :class:`pandas.DataFrame` into a list of :class:`pandas.Series` objects

    Parameters
    ----------
    df : :class:`pandas.DataFrame` object
        DataFrame to be read
    cols : list of strings, optional
        Column names to be read. By default, it reads all columns

    Returns
    -------
    list
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

    '''
    series = []
    if cols is None:
        cols = df.columns
    for col in cols:
        if col in df.columns:
            series.append(df[col])
        else:
            print('WARNING: Column name {} does not exist.'.format(col))
    return series


def flatten_frame(df):
    '''
    Converts a :class:`pandas.DataFrame` object into a :class:`pandas.Series`
    object where indices are tuples of row and column indices

    Parameters
    ----------
    df : :class:`pandas.DataFrame` object

    Returns
    -------
    :class:`pandas.DataFrame` object
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

    '''
    new_frame = df.stack()
    new_frame.index = new_frame.index.to_series()
    return new_frame


def print_model_mps(model):
    '''
    Prints the MPS representation of the model

    Parameters
    ----------
    model : :class:`Model` object

    Examples
    --------
    >>> m = so.Model(name='print_example', session=s)
    >>> x = m.add_variable(lb=1, name='x')
    >>> y = m.add_variables(2, name='y', ub=3, vartype=so.INT)
    >>> m.add_constraint(x + y.sum('*') <= 9, name='c1')
    >>> m.add_constraints((x + y[i] >= 2 for i in [0, 1]), name='c2')
    >>> m.set_objective(x+3*y[0], sense=so.MAX, name='obj')
    >>> so.print_model_mps(m)
    NOTE: Initialized model print_example
         Field1    Field2         Field3 Field4    Field5 Field6 _id_
    0      NAME            print_example      0                0    1
    1      ROWS                                                     2
    2       MAX       obj                                           3
    3         L        c1                                           4
    4         G      c2_0                                           5
    5         G      c2_1                                           6
    6   COLUMNS                                                     7
    7                   x            obj      1                     8
    8                   x             c1      1                     9
    9                   x           c2_0      1                    10
    10                  x           c2_1      1                    11
    11           MARK0000       'MARKER'         'INTORG'          12
    12                y_0            obj      3                    13
    13                y_0             c1      1                    14
    14                y_0           c2_0      1                    15
    15                y_1             c1      1                    16
    16                y_1           c2_1      1                    17
    17           MARK0001       'MARKER'         'INTEND'          18
    18      RHS                                                    19
    19                RHS             c1      9                    20
    20                RHS           c2_0      2                    21
    21                RHS           c2_1      2                    22
    22   RANGES                                                    23
    23   BOUNDS                                                    24
    24       LO       BND              x      1                    25
    25       UP       BND            y_0      3                    26
    26       LO       BND            y_0      0                    27
    27       UP       BND            y_1      3                    28
    28       LO       BND            y_1      0                    29
    29   ENDATA                               0                0   30

    See also
    --------
    :func:`sasoptpy.Model.to_frame`

    '''
    with pd.option_context('display.max_rows', None):
        print(model.to_frame())


def get_namespace():
    '''
    Prints details of components registered to the global name dictionary

    The list includes models, variables, constraints and expressions
    '''
    s = 'Global namespace:'
    for c in [sasoptpy.model.Model, sasoptpy.components.VariableGroup,
              sasoptpy.components.ConstraintGroup,
              sasoptpy.components.Expression, sasoptpy.components.Variable,
              sasoptpy.components.Constraint]:
        s += '\n\t{}'.format(c.__name__)
        for i, k in enumerate(__namedict):
            if type(__namedict[k]) is c:
                s += '\n\t\t{:4d} {:{width}} {}, {}'.format(
                    i, k, type(__namedict[k]), repr(__namedict[k]),
                    width=len(max(__namedict, key=len)))
    return s


def get_namedict():
    return __namedict


def set_namedict(ss):
    __namedict = ss


def get_len(i):
    try:
        return len(i)
    except TypeError:
        return 1


def _list_item(i):
    it = type(i)
    if it == list:
        return i
    else:
        return [i]


def _to_bracket(prefix, keys):
    if keys is None:
        return prefix
    else:
        s = prefix + '['
        k = tuple_pack(keys)
        s += ','.join([str(i) for i in k])
        s += ']'
        return s


def _sort_tuple(i):
    i = sasoptpy.utils.tuple_pack(i)
    key = (len(i),)
    for s in i:
        if isinstance(s, str):
            key += (0,)
        elif np.issubdtype(type(s), np.number):
            key += (1,)
        elif isinstance(s, tuple):
            key += (2,)
    key += i
    return(key)


def get_solution_table(*argv, sort=True, rhs=False):
    '''
    Returns the requested variable names as a DataFrame table

    Parameters
    ----------
    sort : bool, optional
        Sort option for the indices

    Returns
    -------
    :class:`pandas.DataFrame`
        DataFrame object that holds keys and values
    '''
    soltable = []
    listofkeys = []
    keylengths = []
    # Get dimension from first argv
    if(len(argv) == 0):
        return None

    for i, _ in enumerate(argv):
        if isinstance(argv[i], Iterable):
            if isinstance(argv[i], sasoptpy.components.VariableGroup):
                currentkeylist = list(argv[i]._vardict.keys())
                for m in argv[i]._vardict:
                    m = sasoptpy.utils.tuple_unpack(m)
                    if m not in listofkeys:
                        listofkeys.append(m)
                keylengths.append(sasoptpy.utils.list_length(
                    currentkeylist[0]))
            elif isinstance(argv[i], sasoptpy.components.ConstraintGroup):
                currentkeylist = list(argv[i]._condict.keys())
                for m in argv[i]._condict:
                    m = sasoptpy.utils.tuple_unpack(m)
                    if m not in listofkeys:
                        listofkeys.append(m)
                keylengths.append(sasoptpy.utils.list_length(
                    currentkeylist[0]))
            elif (isinstance(argv[i], pd.Series) or
                  (isinstance(argv[i], pd.DataFrame) and
                  len(argv[i].columns) == 1)):
                # optinal method: converting to series, argv[i].iloc[0]
                currentkeylist = argv[i].index.values
                for m in currentkeylist:
                    m = sasoptpy.utils.tuple_unpack(m)
                    if m not in listofkeys:
                        listofkeys.append(m)
                keylengths.append(sasoptpy.utils.list_length(
                    currentkeylist[0]))
            elif isinstance(argv[i], pd.DataFrame):
                index_list = argv[i].index.tolist()
                col_list = argv[i].columns.tolist()
                for m in index_list:
                    for n in col_list:
                        current_key = sasoptpy.utils.tuple_pack(m)
                        + sasoptpy.utils.tuple_pack(n)
                        if current_key not in listofkeys:
                            listofkeys.append(current_key)
                keylengths.append(sasoptpy.utils.list_length(
                    current_key))
            elif isinstance(argv[i], dict):
                currentkeylist = list(argv[i].keys())
                for m in currentkeylist:
                    m = sasoptpy.utils.tuple_unpack(m)
                    if m not in listofkeys:
                        listofkeys.append(m)
                keylengths.append(sasoptpy.utils.list_length(
                    currentkeylist[0]))
        else:
            if ('',) not in listofkeys:
                listofkeys.append(('',))
                keylengths.append(1)

    if(sort):
        try:
            listofkeys = sorted(listofkeys,
                                key=_sort_tuple)
        except TypeError:
            listofkeys = listofkeys

    maxk = max(keylengths)
    for k in listofkeys:
        if isinstance(k, tuple):
            row = list(k)
        else:
            row = [k]
        if sasoptpy.utils.list_length(k) < maxk:
            row.extend(['-']*(maxk-sasoptpy.utils.list_length(k)))
        for i, _ in enumerate(argv):
            if type(argv[i]) == sasoptpy.components.VariableGroup:
                tk = sasoptpy.utils.tuple_pack(k)
                val = argv[i][tk].get_value()\
                    if tk in argv[i]._vardict else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.components.Variable:
                val = argv[i].get_value() if k == ('',) else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.components.Constraint:
                val = argv[i].get_value(rhs=rhs) if k == ('',) else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.components.ConstraintGroup:
                tk = sasoptpy.utils.tuple_pack(k)
                val = argv[i][tk].get_value()\
                    if tk in argv[i]._condict else '-'
                row.append(val)
            elif type(argv[i]) == sasoptpy.components.Expression:
                val = argv[i].get_value() if k == ('',) else '-'
                row.append(val)
            elif type(argv[i]) == pd.Series:
                if k in argv[i].index.values:
                    if type(argv[i][k]) == sasoptpy.components.Expression:
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
                        cellv = argv[i].ix[k, j]
                        if type(cellv) == pd.Series:
                            cellv = cellv.iloc[0]
                        if type(cellv) == sasoptpy.components.Expression:
                            row.append(cellv.get_value())
                        else:
                            row.append(argv[i].ix[k, j])
                    elif sasoptpy.tuple_pack(k) in argv[i].index.tolist():
                        tk = sasoptpy.tuple_pack(k)
                        cellv = argv[i].ix[tk, j]
                        if type(cellv) == pd.Series:
                            cellv = cellv.iloc[0]
                        if type(cellv) == sasoptpy.components.Expression:
                            row.append(cellv.get_value())
                        else:
                            row.append(argv[i].ix[tk, j])
                    else:
                        row.append('-')
            elif type(argv[i]) == pd.DataFrame:
                arg_series = argv[i].stack()
                arg_series.index = arg_series.index.to_series()
                if k in arg_series.index.values.tolist():
                    if type(arg_series[k]) == sasoptpy.components.Expression:
                        val = arg_series[k].get_value()
                    else:
                        val = arg_series[k]
                else:
                    val = '-'
                row.append(val)
            elif isinstance(argv[i], dict):
                if k in argv[i]:
                    tk = sasoptpy.utils.tuple_pack(k)
                    if type(argv[i][tk]) == sasoptpy.components.Expression:
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
    pd.set_option('display.multi_sparse', False)
    return soltablep2
