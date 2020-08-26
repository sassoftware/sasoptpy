
from math import inf
import warnings

import numpy as np
import pandas as pd

import sasoptpy

def to_mps(model, **kwargs):
    """
    Converts the Python model into a DataFrame object in MPS format

    Parameters
    ----------
    constant : boolean, optional
        Switching for using objConstant argument for solveMilp, solveLp. \
        Adds the constant as an auxiliary variable if value is True.

    Returns
    -------
    mpsdata : :class:`pandas.DataFrame`
        Problem representation in strict MPS format

    Examples
    --------

    >>> df = m.to_frame()
    >>> print(df)
         Field1 Field2  Field3 Field4 Field5 Field6 _id_
    0      NAME         model1      0             0    1
    1      ROWS                                        2
    2       MAX    obj                                 3
    3         L     c1                                 4
    4   COLUMNS                                        5
    5                x     obj      4                  6
    6                x      c1      3                  7
    7                y     obj     -5                  8
    8                y      c1      1                  9
    9       RHS                                       10
    10             RHS      c1      6                 11
    11   RANGES                                       12
    12   BOUNDS                                       13
    13   ENDATA                     0             0   14

    Notes
    -----
    * This method is called inside :meth:`Model.solve`.
    """

    constant = kwargs.get('constant', False)

    datarows = []

    def append_row(row):
        datarows.append(row + [len(datarows) + 1])
        return len(datarows)

    # Check if objective has a constant field
    if constant and model._objective._linCoef['CONST']['val'] != 0:
        obj_constant = model.add_variable('obj_constant')
        constant_value = model.get_objective().get_constant()
        obj_constant.set_bounds(lb=constant_value, ub=constant_value)
        obj_constant.set_value(constant_value)
        obj_name = model._objective.get_name() + '_constant'
        model.set_objective(model._objective - constant_value + obj_constant,
                           name=obj_name, sense=model._objective.get_sense())
        warnings.warn('WARNING: The objective function contains a'
                      ' constant term, an auxiliary variable is added.',
                      UserWarning)

    all_vars = model._get_all_variables()
    all_cons = model._get_all_constraints()

    # Create a dictionary of variables with constraint names
    var_con = {}
    for c in all_cons.values():
        for v in c._linCoef:
            var_con.setdefault(v, []).append(c.get_name())

    append_row(['NAME', '', model.get_name(), 0, '', 0])

    append_row(['ROWS', '', '', '', '', ''])
    if model._objective.get_name() is not None:
        append_row([model._objective._sense, model._objective.get_name(),
                          '', '', '', ''])
    for c in all_cons.values():
        append_row([c._direction, c.get_name(), '', '', '', ''])

    append_row(['COLUMNS', '', '', '', '', ''])
    curtype = sasoptpy.CONT
    for v in all_vars.values():
        f5 = 0
        if v._type is sasoptpy.INT and \
                curtype is sasoptpy.CONT:
            append_row(['', 'MARK0000', '\'MARKER\'', '',
                              '\'INTORG\'', ''])
            curtype = sasoptpy.INT
        if v._type is not sasoptpy.INT \
                and curtype is sasoptpy.INT:
            append_row(['', 'MARK0001', '\'MARKER\'', '',
                              '\'INTEND\'', ''])
            curtype = sasoptpy.CONT
        if v.get_name() in model._objective._linCoef:
            cv = model._objective._linCoef[v.get_name()]
            current_row = ['', v.get_name(), model._objective.get_name(), cv['val']]
            f5 = 1
        elif v.get_name() not in var_con:
            current_row = ['', v.get_name(), model._objective.get_name(), 0.0]
            f5 = 1
            var_con[v.get_name()] = []
        for cn in var_con.get(v.get_name(), []):
            if cn in all_cons:
                c = all_cons[cn]
                if v.get_name() in c._linCoef:
                    if f5 == 0:
                        current_row = ['', v.get_name(), c.get_name(),
                                       c._linCoef[v.get_name()]['val']]
                        f5 = 1
                    else:
                        current_row.append(c.get_name())
                        current_row.append(c._linCoef[v.get_name()]['val'])
                        ID = append_row(current_row)
                        f5 = 0
        if f5 == 1:
            current_row.append('')
            current_row.append('')
            ID = append_row(current_row)
    if curtype is sasoptpy.INT:
        append_row(['', 'MARK0001', '\'MARKER\'', '', '\'INTEND\'',
                          ''])

    append_row(['RHS', '', '', '', '', ''])
    f5 = 0
    for c in all_cons.values():
        if c._direction == 'L' and c._linCoef['CONST']['val'] == -inf:
            continue
        if c._direction == 'G' and c._linCoef['CONST']['val'] == 0:
            continue
        rhs = - c._linCoef['CONST']['val']
        if rhs != 0:
            if f5 == 0:
                current_row = ['', 'RHS', c.get_name(), rhs]
                f5 = 1
            else:
                current_row.append(c.get_name())
                current_row.append(rhs)
                f5 = 0
                append_row(current_row)
    if f5 == 1:
        current_row.append('')
        current_row.append('')
        append_row(current_row)

    append_row(['RANGES', '', '', '', '', ''])
    for c in all_cons.values():
        if c._range != 0:
            append_row(['', 'rng', c.get_name(), c._range, '', ''])

    append_row(['BOUNDS', '', '', '', '', ''])
    for v in all_vars.values():
        if v._lb == v._ub:
            append_row(['FX', 'BND', v.get_name(), v._ub, '', ''])
        if v._lb is not None and v._type is not sasoptpy.BIN:
            if v._ub == inf and v._lb == -inf:
                append_row(['FR', 'BND', v.get_name(), '', '', ''])
            elif not v._ub == v._lb:
                if v._type == sasoptpy.INT and \
                        v._lb == 0 and v._ub == inf:
                    append_row(['PL', 'BND', v.get_name(), '', '', ''])
                elif not (v._type == sasoptpy.CONT and v._lb == 0):
                    append_row(['LO', 'BND', v.get_name(), v._lb, '', ''])
        if v._ub != inf and v._ub is not None and not \
                (v._type is sasoptpy.BIN and v._ub == 1) and \
                v._lb != v._ub:
            append_row(['UP', 'BND', v.get_name(), v._ub, '', ''])
        if v._type is sasoptpy.BIN:
            append_row(['BV', 'BND', v.get_name(), '1.0', '', ''])

    append_row(['ENDATA', '', '', 0.0, '', 0.0])
    mpsdata = pd.DataFrame(data=datarows,
                           columns=['Field1', 'Field2', 'Field3', 'Field4',
                                    'Field5', 'Field6', '_id_'])
    datarows = []

    df = mpsdata
    for f in ['Field4', 'Field6']:
        df[f] = df[f].replace('', np.nan)
    df['_id_'] = df['_id_'].astype('int')
    df[['Field4', 'Field6']] = df[['Field4', 'Field6']].astype(float)

    return df
