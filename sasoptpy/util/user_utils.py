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

"""
User accessible utility functions
"""

from collections import Iterable
import random
import string
import warnings
from contextlib import contextmanager

import sasoptpy
from sasoptpy._libs import (pd, np)
from .package_utils import (
    wrap_expression, _wrap_expression_with_iterators, list_length,
    get_first_member, pack_to_tuple, _sort_tuple)


def concat(exp1, exp2):
    return wrap_expression(exp1).concat(wrap_expression(exp2))


@contextmanager
def iterate(set, name):
    if isinstance(name, list):
        yield sasoptpy.abstract.SetIteratorGroup(set, names=name)
    else:
        yield sasoptpy.abstract.SetIterator(set, name=name)


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


def submit(caller, *args, **kwargs):
    session = caller.get_session()
    session_type = sasoptpy.util.package_utils.get_session_type(session)
    if session is None or session_type is None:
        raise RuntimeError('No session is available')

    mediator_class = sasoptpy.mediators[session_type]
    mediator = mediator_class(caller, session)
    return mediator.submit(*args, **kwargs)


def submit_for_solve(caller, *args, **kwargs):
    session = caller.get_session()
    session_type = sasoptpy.util.package_utils.get_session_type(session)
    if session is None or session_type is None:
        raise RuntimeError('No session is available')

    mediator_class = sasoptpy.mediators[session_type]
    mediator = mediator_class(caller, session)
    return mediator.solve(*args, **kwargs)


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


def reset():
    """
    Resets package configs and internal counters
    """
    sasoptpy.config.reset()
    sasoptpy.itemid = 0


def reset_globals():
    warnings.warn('Use sasoptpy.reset()', DeprecationWarning)
    reset()


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


def is_linear(item):
    return item._is_linear()
