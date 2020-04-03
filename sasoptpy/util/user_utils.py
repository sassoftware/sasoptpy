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
from sasoptpy.libs import (pd, np)
from .package_utils import (
    wrap_expression, _wrap_expression_with_iterators,
    get_first_member, pack_to_tuple)


def concat(exp1, exp2):
    return wrap_expression(exp1).concat(wrap_expression(exp2))


@contextmanager
def iterate(set, name):
    if not sasoptpy.abstract.is_abstract_set(set):
        set = sasoptpy.Set.from_object(set)
    if isinstance(name, list):
        yield sasoptpy.abstract.SetIteratorGroup(set, names=name)
    else:
        yield sasoptpy.abstract.SetIterator(set, name=name)


def exp_range(start, stop, step=1):
    """
    Creates a set within specified range

    Parameters
    ----------
    start : :class:`Expression`
        First value of the range
    stop : :class:`Expression`
        Last value of the range
    step : :class:`Expression`, optional
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


def get_solution_table(*argv, key=None, rhs=False):
    return get_value_table(*argv, key=key, rhs=rhs)


def get_value_table(*args, **kwargs):
    """
    Returns values of the given arguments as a merged pandas DataFrame

    Parameters
    ----------
    key : list, optional
        Keys for objects
    rhs : bool, optional
        Option for including constant values

    Returns
    -------
    table : :class:`pandas.DataFrame`
        DataFrame object that holds object values
    """

    if len(args) == 0:
        return None

    series = []
    for arg in args:
        s = get_values(arg, **kwargs)
        series.append(s)
    return pd.concat(series, axis=1, sort=False)


def get_values(arg, **kwargs):
    """
    Returns values of given set of arguments as a pandas Series
    """
    if isinstance(arg, pd.Series):
        arg_values = arg.apply(
            lambda row: row.get_value() if hasattr(row, 'get_value')
            else str(row))
        return arg_values
    elif isinstance(arg, pd.DataFrame):
        arg_values = arg.apply(
            lambda col: col.apply(
                lambda row: row.get_value() if hasattr(row, 'get_value')
                else str(row)))
        return arg_values
    elif isinstance(arg, sasoptpy.VariableGroup):
        keys = []
        values = []
        members = arg.get_members() if arg._abstract is False else arg.get_shadow_members()
        for i in members:
            if any([sasoptpy.abstract.is_abstract(j) for j in i]):
            #if sasoptpy.abstract.is_abstract(get_first_member(i)):
                continue
            keys.append(get_first_member(i))
            values.append(members[i].get_value())
        return pd.Series(values, index=keys, name=arg.get_name())
    elif isinstance(arg, sasoptpy.ConstraintGroup):
        keys = []
        values = []
        members = arg.get_all_keys()
        rhs = kwargs.get('rhs', False)
        for i in members:
            if sasoptpy.abstract.is_abstract(get_first_member(i)):
                continue
            keys.append(get_first_member(i))
            values.append(arg[i].get_value(rhs=rhs))
        return pd.Series(values, index=keys, name=arg.get_name())
    elif isinstance(arg, sasoptpy.ImplicitVar):
        keys = []
        values = []
        members = arg.get_dict()
        for i in members:
            keys.append(get_first_member(i))
            values.append(members[i].get_value())
        return pd.Series(values, index=keys, name=arg.get_name())
    elif isinstance(arg, sasoptpy.Expression):
        return pd.Series([arg.get_value()], index=['-'], name=arg.get_name())
    else:
        return pd.Series([arg], index=['-'], name=str(arg))


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


def submit_for_tune(caller, **kwargs):
    session = caller.get_session()
    session_type = sasoptpy.util.package_utils.get_session_type(session)
    if session_type != 'CAS':
        raise TypeError('Tune action is only available on CAS (SAS Viya) servers.')

    mediator_class= sasoptpy.mediators[session_type]
    mediator = mediator_class(caller, session)
    return mediator.tune(**kwargs)


def quick_sum(argv):
    """
    Summation function for :class:`Expression` objects

    Notes
    -----

    This method will deprecate in future versions.
    Use :func:`expr_sum` instead.

    """
    return sasoptpy.util.expr_sum(argv)


def expr_sum(argv):
    """
    Summation function for :class:`Expression` objects

    Returns
    -------
    exp : :class:`Expression`
        Sum of given arguments

    Examples
    --------

    >>> x = so.VariableGroup(10000, name='x')
    >>> y = so.expr_sum(2*x[i] for i in range(10000))

    Notes
    -----

    This function is faster for expressions compared to Python's native sum()
    function.

    """
    clocals = argv.gi_frame.f_locals.copy()

    exp = sasoptpy.core.Expression()
    exp.set_temporary()
    iterators = []
    for i in argv:
        exp = exp + i
        if sasoptpy.core.util.is_expression(i):
            #if i._abstract:
            newlocals = argv.gi_frame.f_locals
            for nl in newlocals.keys():
                if nl not in clocals and\
                        (type(newlocals[nl]) == sasoptpy.abstract.SetIterator or
                         type(newlocals[nl]) == sasoptpy.abstract.SetIteratorGroup):
                    iterators.append(newlocals[nl])
                    newlocals[nl].set_name(nl)
    if iterators:
        iterators = sorted(iterators, key=lambda i: i._objorder)
        exp = _wrap_expression_with_iterators(exp, 'sum', iterators)
    exp.set_permanent()
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


def has_integer_variables(item):
    return item._has_integer_vars()
