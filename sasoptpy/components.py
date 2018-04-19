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

from itertools import product
from math import copysign, inf
from types import GeneratorType
import warnings

import numpy as np
import pandas as pd

import sasoptpy.utils


class Expression:
    '''
    Creates a linear expression to represent model components

    Parameters
    ----------
    exp : :class:`Expression` object, optional
        An existing expression where arguments are being passed
    name : string, optional
        A local name for the expression
    temp : boolean, optional
        A boolean shows whether expression is temporary or permanent

    Examples
    --------

    >>> x = so.Variable(name='x')
    >>> y = so.VariableGroup(3, name='y')
    >>> e = so.Expression(exp=x + 3 * y[0] - 5 * y[1], name='exp1')
    >>> print(e)
     -  5.0 * y[1]  +  3.0 * y[0]  +  x
    >>> print(repr(e))
    sasoptpy.Expression(exp =  -  5.0 * y[1]  +  3.0 * y[0]  +  x ,
                        name='exp1')

    >>> sales = so.Variable(name='sales')
    >>> material = so.Variable(name='material')
    >>> profit = 5 * sales - 3 * material
    >>> print(profit)
     5.0 * sales  -  3.0 * material
    >>> print(repr(profit))
    sasoptpy.Expression(exp =  5.0 * sales  -  3.0 * material , name=None)

    Notes
    -----
    * Two other classes (:class:`Variable` and :class:`Constraint`) are
      subclasses of this class.
    * Expressions are created automatically after linear math operations
      with variables.
    * An expression object can be called when defining constraints and other
      expressions.
    '''

    def __init__(self, exp=None, name=None, temp=False):
        if name is not None:
            self._name = sasoptpy.utils.check_name(name, 'expr')
            sasoptpy.utils.register_name(self._name, self)
        else:
            self._name = None
        self._value = 0
        self._dual = None
        self._linCoef = {}
        if exp is None:
            self._linCoef = {'CONST': {'ref': None, 'val': 0}}
        else:
            if isinstance(exp, Expression):
                for mylc in exp._linCoef:
                    self._linCoef[mylc] = dict(exp._linCoef[mylc])
            elif np.issubdtype(type(exp), np.number):
                self._linCoef = {'CONST': {'ref': None, 'val': exp}}
            else:
                print('WARNING: An invalid type is passed to create an ' +
                      'Expression: {}'.format(type(exp)))
        self._temp = temp
        self._value = 0

    def copy(self, name=None):
        '''
        Returns a copy of the :class:`Expression` object

        Parameters
        ----------
        name : string, optional
            Name for the copy

        Returns
        -------
        :class:`Expression` object
            Copy of the object

        Examples
        --------

        >>> e = so.Expression(7 * x - y[0], name='e')
        >>> print(repr(e))
        sasoptpy.Expression(exp =  -  y[0]  +  7.0 * x , name='e')
        >>> f = e.copy(name='f')
        >>> print(repr(f))
        sasoptpy.Expression(exp =  -  y[0]  +  7.0 * x , name='f')

        '''
        r = Expression(name=name)
        for mylc in self._linCoef:
            r._linCoef[mylc] = dict(self._linCoef[mylc])
        return r

    def get_value(self):
        '''
        Returns the value of the expression after variable values are changed

        Returns
        -------
        float
            Value of the expression

        Examples
        --------

        >>> profit = so.Expression(5 * sales - 3 * material)
        >>> m.solve()
        >>> print(profit.get_value())
        41.0

        '''
        v = 0
        for mylc in self._linCoef:
            if self._linCoef[mylc]['ref'] is not None:
                v += self._linCoef[mylc]['val'] * \
                    self._linCoef[mylc]['ref']._value
            else:
                v += self._linCoef[mylc]['val']
        return v

    def set_name(self, name):
        '''
        Sets the name of the expression

        Parameters
        ----------
        name : string
            Name of the expression

        Returns
        -------
        string
            Name of the expression after resolving conflicts

        Examples
        --------

        >>> e = x + 2*y
        >>> e.set_name('objective')

        '''
        if self._name is not None:
            if self._name in sasoptpy.utils.__namedict:
                del sasoptpy.utils.__namedict[self._name]
        safe_name = sasoptpy.utils.check_name(name, 'expr')
        if name != safe_name:
            print('NOTE: Name {} is changed to {} to prevent a conflict'
                  .format(name, safe_name))
        sasoptpy.utils.register_name(self._name, self)
        self._name = safe_name
        return self._name

    def get_name(self):
        '''
        Returns the name of the expression

        Returns
        -------
        string
            Name of the expression

        Examples
        --------

        >>> var1 = m.add_variables(name='x')
        >>> print(var1.get_name())
        x
        '''
        return self._name

    def set_permanent(self, name=None):
        '''
        Converts a temporary expression into a permanent one

        Parameters
        ----------
        name : string, optional
            Name of the expression

        Returns
        -------
        string
            Name of the expression in the namespace
        '''
        if self._name is None:
            self._name = sasoptpy.utils.check_name(name, 'expr')
            sasoptpy.utils.register_name(self._name, self)
        self._temp = False
        return self._name

    def __repr__(self):
        s = 'sasoptpy.Expression('
        if self._name is not None:
            s += 'exp = {}, name=\'{}\''.format(str(self), self._name)
        else:
            s += 'exp = {}, name=None'.format(str(self))
        s += ')'
        return s

    def __str__(self):
        s = ''
        firstel = 1
        for v in self._linCoef:
            vx = self._linCoef[v]
            if (self._linCoef[v]['val'] == 0 or
               (v == 'CONST' and isinstance(self, Constraint))):
                continue
            if firstel == 1 and copysign(1, vx['val']) == 1:
                s += ''
            else:
                if copysign(1, vx['val']) == 1:
                    s += ' + '
                else:
                    s += ' - '
            firstel = 0
            if(v is not 'CONST'):
                if vx['val'] == 1 or vx['val'] == -1:
                    s += ' {} '.format(vx['ref'])
                else:
                    s += ' {} * {} '.format(abs(float(vx['val'])), vx['ref'])
            elif not isinstance(self, Constraint):
                if vx['val'] is not 0:
                    s += ' {} '.format(abs(vx['val']))
        return s

    def _add_coef_value(self, var, key, value):
        '''
        Changes value of a variable inside the :class:`Expression` object in
        place

        Parameters
        ----------
        var : :class:`Variable`
            Variable object whose value will be changed
        varname : string
            Name of the variable object
        value : float
            New value or the addition to the existing value of the variable
        '''
        if key in self._linCoef:
            self._linCoef[key]['val'] += value
        else:
            self._linCoef[key] = {'ref': var, 'val': value}

    def add(self, other, sign=1):
        '''
        Combines two expressions and produces a new one

        Parameters
        ----------
        other : float or :class:`Expression` object
            Second expression or constant value to be added
        sign : int, optional
            Sign of the addition, 1 or -1
        in_place : boolean, optional
            Whether the addition will be performed in place or not

        Returns
        -------
        :class:`Expression` object

        Notes
        -----
        * This method is mainly for internal use.
        * Adding an expression is equivalent to calling this method:
          (x-y)+(3*x-2*y) and (x-y).add(3*x-2*y) are interchangeable.
        '''
        if self._temp and type(self) is Expression:
            r = self
        else:
            if isinstance(other, Expression) and other._temp:
                r = other
                other = self
                sign = sign * -1
            else:
                r = self.copy()
        if isinstance(other, Expression):
            for v in other._linCoef:
                if v in r._linCoef:
                    r._linCoef[v]['val'] += sign * other._linCoef[v]['val']
                else:
                    r._linCoef[v] = dict(other._linCoef[v])
                    r._linCoef[v]['val'] *= sign
        elif np.issubdtype(type(other), np.number):
            r._linCoef['CONST']['val'] += sign * other
        return r

    def mult(self, other):
        '''
        Multiplies the :class:`Expression` with a scalar value

        Parameters
        ----------
        other : :class:`Expression` or int
            Second expression to be multiplied

        Returns
        -------
        :class:`Expression` object
            A new :class:`Expression` that represents the multiplication

        Notes
        -----
        * This method is mainly for internal use.
        * Multiplying an expression is equivalent to calling this method:
          3*(x-y) and (x-y).mult(3) are interchangeable.
        '''
        #  TODO r=self could be used whenever expression has no name
        if isinstance(other, Expression):
            raise Exception('Two expressions cannot be multiplied.')
        elif np.issubdtype(type(other), np.number):
            if self._temp and type(self) is Expression:
                if other == 0:
                    self._linCoef = {'CONST': {'ref': None, 'val': 0}}
                else:
                    for mylc in self._linCoef:
                        self._linCoef[mylc]['val'] *= other
                r = self
            else:
                r = Expression()
                if other != 0:
                    for mylc in self._linCoef:
                        r._linCoef[mylc] = dict(self._linCoef[mylc])
                        r._linCoef[mylc]['val'] *= other
        return r

    def _relational(self, other, direction_):
        '''
        Creates a logical relation between :class:`Expression` objects

        Parameters
        ----------
        other: :class:`Expression`
            Expression on the other side of the relation wrt self
        direction_: string
            Direction of the logical relation, either 'E', 'L', or 'G'

        Returns
        -------
        :class:`Constraint`
            Constraint generated as a result of linear relation

        '''
        # If the user provides both an upper and a lower bnd.
        if isinstance(other, list) and direction_ == 'E':
            e = self.copy()
            e._add_coef_value(None, 'CONST', -1*min(other[0], other[1]))
            ranged_constraint = Constraint(exp=e, direction='E',
                                           crange=abs(other[1]-other[0]))
            return ranged_constraint
        elif not isinstance(self, Variable):
            if self._temp and type(self) is Expression:
                r = self
            else:
                r = self.copy()
            #  TODO r=self could be used whenever expression has no name
            if np.issubdtype(type(other), np.number):
                r._linCoef['CONST']['val'] -= other
            elif isinstance(other, Expression):
                for v in other._linCoef:
                    r._add_coef_value(other._linCoef[v]['ref'], v,
                                      -other._linCoef[v]['val'])
            generated_constraint = Constraint(exp=r, direction=direction_,
                                              crange=0)
            return generated_constraint
        else:
            r = Expression()
            for v in self._linCoef:
                r._add_coef_value(self._linCoef[v]['ref'], v,
                                  self._linCoef[v]['val'])
            if np.issubdtype(type(other), np.number):
                r._linCoef['CONST']['val'] -= other
            else:
                for v in other._linCoef:
                    r._add_coef_value(other._linCoef[v]['ref'],
                                      v, -other._linCoef[v]['val'])
            generated_constraint = Constraint(exp=r, direction=direction_,
                                              crange=0)
            return generated_constraint
        return self

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.add(other, -1)

    def __mul__(self, other):
        return self.mult(other)

    def __radd__(self, other):
        return self.add(other)

    def __rsub__(self, other):
        tmp = self.add(other, -1)
        for v in tmp._linCoef:
            tmp._linCoef[v]['val'] *= -1
        return tmp

    def __rmul__(self, other):
        return self.mult(other)

    def __truediv__(self, other):
        return self.mult(1/other)

    def __le__(self, other):
        return self._relational(other, 'L')

    def __ge__(self, other):
        return self._relational(other, 'G')

    def __eq__(self, other):
        return self._relational(other, 'E')

    def __rle__(self, other):
        return self._relational(other, 'G')

    def __rge__(self, other):
        return self._relational(other, 'L')

    def __neg__(self):
        return self.mult(-1)


class Variable(Expression):
    '''
    Creates an optimization variable to be used inside models

    Parameters
    ----------
    name : string
        Name of the variable
    vartype : string, optional
        Type of the variable
    lb : float, optional
        Lower bound of the variable
    ub : float, optional
        Upper bound of the variable
    init : float, optional
        Initial value of the variable

    Examples
    --------

    >>> x = so.Variable(name='x', lb=0, ub=20, vartype=so.CONT)
    >>> print(repr(x))
    sasoptpy.Variable(name='x', lb=0, ub=20, vartype='CONT')

    >>> y = so.Variable(name='y', init=1, vartype=so.INT)
    >>> print(repr(y))
    sasoptpy.Variable(name='y', lb=0, ub=inf, init=1, vartype='INT')

    See also
    --------
    :func:`sasoptpy.Model.add_variable`

    '''

    def __init__(self, name, vartype=sasoptpy.utils.CONT, lb=0, ub=inf,
                 init=None):
        super().__init__()
        name = sasoptpy.utils.check_name(name, 'var')
        self._name = name
        self._type = vartype
        if lb is None:
            lb = 0
        if ub is None:
            ub = inf
        self._lb = lb
        self._ub = ub
        self._init = init
        if vartype == sasoptpy.utils.BIN:
            self._lb = max(self._lb, 0)
            self._ub = min(self._ub, 1)
        self._linCoef[name] = {'ref': self, 'val': 1.0}
        sasoptpy.utils.register_name(name, self)
        self._cons = set()
        self._key = None
        self._parent = None
        self._temp = False

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    def set_bounds(self, lb=None, ub=None):
        '''
        Changes bounds on a variable

        Parameters
        ----------
        lb : float
            Lower bound of the variable
        ub : float
            Upper bound of the variable

        Examples
        --------

        >>> x = so.Variable(name='x', lb=0, ub=20)
        >>> print(repr(x))
        sasoptpy.Variable(name='x', lb=0, ub=20, vartype='CONT')
        >>> x.set_bounds(lb=5, ub=15)
        >>> print(repr(x))
        sasoptpy.Variable(name='x', lb=5, ub=15, vartype='CONT')

        '''
        if lb is not None:
            self._lb = lb
        if ub is not None:
            self._ub = ub

    def set_init(self, init=None):
        '''
        Changes initial value of a variable

        Parameters
        ----------
        init : float or None
            Initial value of the variable

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> x.set_init(5)

        >>> y = so.Variable(name='y', init=3)
        >>> y.set_init()

        '''
        self._init = init

    def __repr__(self):
        st = 'sasoptpy.Variable(name=\'{}\', '.format(self._name)
        if self._lb is not 0:
            st += 'lb={}, '.format(self._lb)
        if self._ub is not inf:
            st += 'ub={}, '.format(self._ub)
        if self._init is not None:
            st += 'init={}, '.format(self._init)
        st += ' vartype=\'{}\')'.format(self._type)
        return st

    def __str__(self):
        if self._parent is not None and self._key is not None:
            if len(self._key) == 1:
                key = str(self._key)[1:-2]  # Remove comma
            else:
                key = str(self._key)[1:-1]  # Remove parantheses
            return ('{}[{}]'.format(self._parent._name, key))
        return('{}'.format(self._name))

    def _tag_constraint(self, c):
        '''
        Adds a constraint into list of constraints that the variable appears
        '''
        if c is not None:
            self._cons.add(c._name)

    def __setattr__(self, attr, value):
        if attr == '_temp' and value is True:
            print('WARNING: Variables cannot be temporary.')
        else:
            super().__setattr__(attr, value)


class Constraint(Expression):
    '''
    Creates a linear or quadratic constraint for optimization models

    Constraints should be created by adding logical relations to
    :class:`Expression` objects.

    Parameters
    ----------
    exp : :class:`Expression`
        A logical expression that forms the constraint
    direction : string
        Direction of the logical expression, 'E' (=), 'L' (<=) or 'G' (>=)
    name : string, optional
        Name of the constraint object
    range : float, optional
        Range for ranged constraints

    Examples
    --------

    >>> c1 = so.Constraint( 3 * x - 5 * y <= 10, name='c1')
    >>> print(repr(c1))
    sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

    >>> c2 = so.Constraint( - x + 2 * y - 5, direction='L', name='c2')
    sasoptpy.Constraint( -  x  +  2.0 * y  <=  5, name='c2')

    Notes
    -----

    * A constraint can be generated in multiple ways:

      1. Using the :func:`sasoptpy.Model.add_constraint` method

         >>> c1 = m.add_constraint(3 * x - 5 * y <= 10, name='c1')
         >>> print(repr(c1))
         sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

      2. Using the constructor

         >>> c1 = sasoptpy.Constraint(3 * x - 5 * y <= 10, name='c1')
         >>> print(repr(c1))
         sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

    * The same constraint can be included into other models using the
      :func:`Model.include` method.

    See also
    --------
    :func:`sasoptpy.Model.add_constraint`
    '''

    def __init__(self, exp, direction=None, name=None, crange=0):
        super().__init__()
        if name is not None:
            name = sasoptpy.utils.check_name(name, 'con')
            self._name = name
            sasoptpy.utils.register_name(name, self)
        else:
            self._name = None
        if exp._name is None:
            self._linCoef = exp._linCoef
            for m in self._linCoef:
                if name is not None and m != 'CONST':
                        self._linCoef[m]['ref']._tag_constraint(self)
        else:
            for m in exp._linCoef:
                self._linCoef[m] = dict(exp._linCoef[m])
                if name is not None and m != 'CONST':
                    self._linCoef[m]['ref']._tag_constraint(self)
        if direction is None:
            self._direction = exp._direction
        else:
            self._direction = direction
        self._range = crange
        self._key = None
        self._parent = None
        self._block = None
        self._temp = False

    def update_var_coef(self, var, value):
        '''
        Updates the coefficient of a variable inside the constraint

        Parameters
        ----------
        var : :class:`Variable` object
            Variable to be updated
        value : float
            Coefficient of the variable in the constraint

        Examples
        --------

        >>> c1 = so.Constraint(exp=3 * x - 5 * y <= 10, name='c1')
        >>> print(repr(c1))
        sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')
        >>> c1.update_var_coef(x, -1)
        >>> print(repr(c1))
        sasoptpy.Constraint( -  5.0 * y  -  x  <=  10, name='c1')

        See also
        --------
        :func:`sasoptpy.Model.set_coef`

        '''
        varname = var._name
        if varname in self._linCoef:
            self._linCoef[varname]['val'] = value
        else:
            self._linCoef[varname] = {'ref': var, 'val': value}

    def set_rhs(self, value):
        '''
        Changes the RHS of a constraint

        Parameters
        ----------
        value : float
            New RHS value for the constraint

        Examples
        --------

        >>> x = m.add_variable(name='x')
        >>> y = m.add_variable(name='y')
        >>> c = m.add_constraint(x + 3*y <= 10, name='con_1')
        >>> print(c)
        x  +  3.0 * y  <=  10
        >>> c.set_rhs(5)
        >>> print(c)
        x  +  3.0 * y  <=  5

        '''
        self._linCoef['CONST']['val'] = -value

    def set_direction(self, direction):
        '''
        Changes the direction of a constraint

        Parameters
        ----------
        direction : string
            Direction of the constraint, 'E', 'L', or 'G' for equal to,
            less than or equal to, and greater than or equal to, respectively

        Examples
        --------

        >>> c1 = so.Constraint(exp=3 * x - 5 * y <= 10, name='c1')
        >>> print(repr(c1))
        sasoptpy.Constraint( 3.0 * x  -  5.0 * y  <=  10, name='c1')
        >>> c1.set_direction('G')
        >>> print(repr(c1))
        sasoptpy.Constraint( 3.0 * x  -  5.0 * y  >=  10, name='c1')

        '''
        if direction in ['E', 'L', 'G']:
            self._direction = direction
        else:
            print('WARNING: Cannot change constraint direction {} {}'.format(
                self._name, direction))

    def set_block(self, block_number):
        '''
        Sets the decomposition block number for a constraint

        Parameters
        ----------
        block_number : int
            Block number of the constraint

        Examples
        --------

        >>> c1 = m.add_constraints((x + 2 * y[i] <= 5 for i in NODES),
                                   name='c1')
        >>> for i in NODES:
              c1[i].set_block(i)

        '''
        self._block = block_number

    def get_value(self, rhs=False):
        '''
        Returns the current value of the constraint

        Parameters
        ----------
        rhs : boolean, optional
            Whether constant values (RHS) will be included in the value or not.
            Default is false

        Examples
        --------

        >>> m.solve()
        >>> print(c1.get_value())
        6.0
        >>> print(c1.get_value(rhs=True))
        0.0

        '''
        v = super().get_value()
        if rhs:
            return v
        else:
            v -= self._linCoef['CONST']['val']
            return v

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    def __str__(self):
        s = super().__str__()
        if self._direction == 'E':
            s += ' == '
        elif self._direction == 'L':
            s += ' <= '
        elif self._direction == 'G':
            s += ' >= '
        else:
            raise Exception('Constraint has no direction!')
        if self._range == 0:
            s += ' {}'.format(- self._linCoef['CONST']['val'])
        else:
            s += ' [{}, {}]'.format(- self._linCoef['CONST']['val'],
                                    - self._linCoef['CONST']['val'] +
                                    self._range)
        return s

    def __repr__(self):
        if self._name is not None:
            st = 'sasoptpy.Constraint({}, name=\'{}\')'
            s = st.format(str(self), self._name)
        else:
            st = 'sasoptpy.Constraint({}, name=None)'
            s = st.format(str(self))
        return s


class VariableGroup:
    '''
    Creates a group of :class:`Variable` objects

    Parameters
    ----------
    argv : list, dict, int, :class:`pandas.Index`
        Loop index for variable group
    name : string, optional
        Name (prefix) of the variables
    vartype : string, optional
        Type of variables, `BIN`, `INT`, or `CONT`
    lb : list, dict, :class:`pandas.Series`, optional
        Lower bounds of variables
    ub : list, dict, :class:`pandas.Series`, optional
        Upper bounds of variables
    init : float, optional
        Initial values of variables

    Examples
    --------

    >>> PERIODS = ['Period1', 'Period2', 'Period3']
    >>> production = so.VariableGroup(PERIODS, vartype=so.INT,
                                      name='production', lb=10)
    >>> print(production)
    Variable Group (production) [
      [Period1: production['Period1']]
      [Period2: production['Period2']]
      [Period3: production['Period3']]
    ]

    >>> x = so.VariableGroup(4, vartype=so.BIN, name='x')
    >>> print(x)
    Variable Group (x) [
      [0: x[0]]
      [1: x[1]]
      [2: x[2]]
      [3: x[3]]
    ]

    >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z')
    >>> print(z)
    Variable Group (z) [
      [(0, 'a'): z[0, 'a']]
      [(0, 'b'): z[0, 'b']]
      [(0, 'c'): z[0, 'c']]
      [(1, 'a'): z[1, 'a']]
      [(1, 'b'): z[1, 'b']]
      [(1, 'c'): z[1, 'c']]
    ]
    >>> print(repr(z))
    sasoptpy.VariableGroup([0, 1], ['a', 'b', 'c'], name='z')

    Notes
    -----
    * When working with a single model, use the
      :func:`sasoptpy.Model.add_variables` method.
    * If a variable group object is created, it can be added to a model using
      the :func:`sasoptpy.Model.include` method.
    * An individual variable inside the group can be accessed using indices.

      >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
      >>> print(repr(z[0, 'a']))
      sasoptpy.Variable(name='z_0_a', lb=0, ub=10, vartype='CONT')

    See also
    --------
    :func:`sasoptpy.Model.add_variables`
    :func:`sasoptpy.Model.include`

    '''

    def __init__(self, *argv, name, vartype=sasoptpy.utils.CONT, lb=0,
                 ub=inf, init=None):
        self._vardict = {}
        self._groups = {}
        self._recursive_add_vars(*argv, name=name,
                                 vartype=vartype, lb=lb, ub=ub, init=init,
                                 vardict=self._vardict)
        if name is not None:
            name = sasoptpy.utils.check_name(name, 'var')
            self._name = name
            sasoptpy.utils.register_name(name, self)
        else:
            self._name = None
        self._set_var_info()

    def get_name(self):
        '''
        Returns the name of the variable group

        Returns
        -------
        string
            Name of the variable group

        Examples
        --------

        >>> var1 = m.add_variables(4, name='x')
        >>> print(var1.get_name())
        x
        '''
        return self._name

    def _recursive_add_vars(self, *argv, name, vartype, lb, ub, init,
                            vardict={}, vkeys=()):
        the_list = sasoptpy.utils.extract_argument_as_list(argv[0])
        for _, i in enumerate(the_list):
            if isinstance(i, tuple):
                newfixed = vkeys + i
            else:
                newfixed = vkeys + (i,)
            if len(argv) == 1:
                varname = '{}'.format(name)
                # Proposed change:
                # varname = '{}['.format(name) + ','.join(format(k)
                #                                    for k in newfixed) + ']'
                for j, k in enumerate(newfixed):
                    varname += '_{}'.format(k)
                    try:
                        self._groups[j].add(k)
                    except KeyError:
                        self._groups[j] = set()
                        self._groups[j].add(k)
                varlb = sasoptpy.utils.extract_list_value(newfixed, lb)
                varub = sasoptpy.utils.extract_list_value(newfixed, ub)
                varin = sasoptpy.utils.extract_list_value(newfixed, init)
                new_var = sasoptpy.Variable(
                    name=varname, lb=varlb, ub=varub, init=varin,
                    vartype=vartype)
                vardict[newfixed] = new_var
            else:
                self._recursive_add_vars(*argv[1:], vardict=vardict,
                                         vkeys=newfixed,
                                         name=name, vartype=vartype,
                                         lb=lb, ub=ub, init=init)

    def _set_var_info(self):
        for i in self._vardict:
            self._vardict[i]._set_info(parent=self, key=i)

    def __getitem__(self, key):
        '''
        Overloaded method to access individual variables

        Parameters
        ----------
        key : string or int
            Key of the variable

        Returns
        -------
        :class:`Variable` object or list of :class:`Variable` objects
        '''
        k = sasoptpy.utils.tuple_pack(key)
        if k in self._vardict:
            return self._vardict[k]
        else:
            indices_to_filter = []
            filter_values = {}
            list_of_variables = []
            for i, _ in enumerate(k):
                if k[i] != '*':
                    indices_to_filter.append(i)
                    filter_values[i] = sasoptpy.utils._list_item(k[i])
            for v in self._vardict:
                eligible = True
                for f in indices_to_filter:
                    if v[f] not in filter_values[f]:
                        eligible = False
                if eligible:
                    list_of_variables.append(self._vardict[v])
            if not list_of_variables:
                warnings.warn('Requested variable group is empty:' +
                              ' {}[{}] ({})'.
                              format(self._name, key, type(key)),
                              RuntimeWarning, stacklevel=2)
            return list_of_variables

    def __iter__(self):
        try:
            ls = [self._vardict[key] for key in sorted(self._vardict.keys())]
        except TypeError:
            ls = [self._vardict[key] for key in self._vardict.keys()]
        return iter(ls)

    def sum(self, *argv):
        '''
        Quick sum method for the variable groups

        Parameters
        ----------
        argv : Arguments
            List of indices for the sum

        Returns
        -------
        :class:`Expression` object
            Expression that represents the sum of all variables in the group

        Examples
        --------

        >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
        >>> e1 = z.sum('*', '*')
        >>> print(e1)
        z[1, 'c']  +  z[1, 'a']  +  z[1, 'b']  +  z[0, 'a']  +  z[0, 'b']  +
        z[0, 'c']
        >>> e2 = z.sum('*', 'a')
        >>> print(e2)
         z[1, 'a']  +  z[0, 'a']
        >>> e3 = z.sum('*', ['a', 'b'])
        >>> print(e3)
         z[1, 'a']  +  z[0, 'b']  +  z[1, 'b']  +  z[0, 'a']

        '''
        r = Expression(temp=True)
        feas_set = []
        for i, a in enumerate(argv):
            if a == '*':
                feas_set.append(self._groups[i])
            elif hasattr(a, "__iter__") and not isinstance(a, str):
                feas_set.append(a)
            else:
                feas_set.append([a])
        combs = product(*feas_set)
        for i in combs:
            var_key = sasoptpy.utils.tuple_pack(i)
            if var_key in self._vardict:
                r.add(self._vardict[var_key], 1)
        r.set_permanent()
        return r

    def mult(self, vector):
        '''
        Quick multiplication method for the variable groups

        Parameters
        ----------
        vector : list, dictionary, :class:`pandas.Series` object,
                 or :class:`pandas.DataFrame` object
            Vector to be multiplied with the variable group

        Returns
        -------
        :class:`Expression` object
            An expression that is the product of the variable group with the
            given vector

        Examples
        --------

        Multiplying with a list

        >>> x = so.VariableGroup(4, vartype=so.BIN, name='x')
        >>> e1 = x.mult([1, 5, 6, 10])
        >>> print(e1)
         10.0 * x[3]  +  6.0 * x[2]  +  x[0]  +  5.0 * x[1]

        Multiplying with a dictionary

        >>> y = so.VariableGroup([0, 1], ['a', 'b'], name='y', lb=0, ub=10)
        >>> dvals = {(0, 'a'): 1, (0, 'b'): 2, (1, 'a'): -1, (1, 'b'): 5}
        >>> e2 = y.mult(dvals)
        >>> print(e2)
         2.0 * y[0, 'b']  -  y[1, 'a']  +  y[0, 'a']  +  5.0 * y[1, 'b']

        Multiplying with a pandas.Series object

        >>> u = so.VariableGroup(['a', 'b', 'c', 'd'], name='u')
        >>> ps = pd.Series([0.1, 1.5, -0.2, 0.3], index=['a', 'b', 'c', 'd'])
        >>> e3 = u.mult(ps)
        >>> print(e3)
         1.5 * u['b']  +  0.1 * u['a']  -  0.2 * u['c']  +  0.3 * u['d']

        Multiplying with a pandas.DataFrame object

        >>> data = np.random.rand(3, 3)
        >>> df = pd.DataFrame(data, columns=['a', 'b', 'c'])
        >>> print(df)
        >>> NOTE: Initialized model model1
                  a         b         c
        0  0.966524  0.237081  0.944630
        1  0.821356  0.074753  0.345596
        2  0.065229  0.037212  0.136644
        >>> y = m.add_variables(3, ['a', 'b', 'c'], name='y')
        >>> e = y.mult(df)
        >>> print(e)
         0.9665237354418064 * y[0, 'a']  +  0.23708064143289442 * y[0, 'b']  +
        0.944629500537536 * y[0, 'c']  +  0.8213562592159828 * y[1, 'a']  +
        0.07475256894157478 * y[1, 'b']  +  0.3455957019116668 * y[1, 'c']  +
        0.06522945752546017 * y[2, 'a']  +  0.03721153533250843 * y[2, 'b']  +
        0.13664422498043194 * y[2, 'c']

        '''
        r = Expression()
        if isinstance(vector, list) or isinstance(vector, np.ndarray):
            for i, key in enumerate(vector):
                var = self._vardict[i, ]
                r._linCoef[var._name] = {'ref': var, 'val': vector[i]}
        elif isinstance(vector, pd.Series):
            for key in vector.index:
                k = sasoptpy.utils.tuple_pack(key)
                var = self._vardict[k]
                r._linCoef[var._name] = {'ref': var, 'val': vector[key]}
        elif isinstance(vector, pd.DataFrame):
            vectorflat = sasoptpy.utils.flatten_frame(vector)
            for key in vectorflat.index:
                k = sasoptpy.utils.tuple_pack(key)
                var = self._vardict[k]
                r._linCoef[var._name] = {'ref': var, 'val': vectorflat[key]}
        else:
            for i, key in enumerate(vector):
                if isinstance(key, tuple):
                    k = key
                else:
                    k = (key,)
                var = self._vardict[k]
                r._linCoef[var._name] = {'ref': var, 'val': vector[i]}
        return r

    def set_bounds(self, lb=None, ub=None):
        '''
        Sets / updates bounds for the given variable

        Parameters
        ----------
        lb : Lower bound, optional
        ub : Upper bound, optional

        Examples
        --------

        >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
        >>> print(repr(z[0, 'a']))
        sasoptpy.Variable(name='z_0_a', lb=0, ub=10, vartype='CONT')
        >>> z.set_bounds(lb=3, ub=5)
        >>> print(repr(z[0, 'a']))
        sasoptpy.Variable(name='z_0_a', lb=3, ub=5, vartype='CONT')

        >>> u = so.VariableGroup(['a', 'b', 'c', 'd'], name='u')
        >>> lb_vals = pd.Series([1, 4, 0, -1], index=['a', 'b', 'c', 'd'])
        >>> u.set_bounds(lb=lb_vals)
        >>> print(repr(u['b']))
        sasoptpy.Variable(name='u_b', lb=4, ub=inf, vartype='CONT')

        '''
        for v in self._vardict:
            varlb = sasoptpy.utils.extract_list_value(v, lb)
            varub = sasoptpy.utils.extract_list_value(v, ub)
            self._vardict[v].set_bounds(lb=varlb, ub=varub)

    def __str__(self):
        s = 'Variable Group ({}) [\n'.format(self._name)
        try:
            vd = sorted(self._vardict)
        except TypeError:
            vd = self._vardict
        for k in vd:
            v = self._vardict[k]
            s += '  [{}: {}]\n'.format(sasoptpy.utils.tuple_unpack(k),
                                       v)
        s += ']'
        return s

    def __repr__(self):
        s = 'sasoptpy.VariableGroup('
        keylen = max(map(len, self._vardict))
        for i in range(keylen):
            ls = []
            try:
                vd = sorted(self._vardict)
            except TypeError:
                vd = self._vardict
            for k in vd:
                if k[i] not in ls:
                    ls.append(k[i])
            s += '{}, '.format(ls)
        s += 'name=\'{}\')'.format(self._name)
        return s


class ConstraintGroup:
    '''
    Creates a group of :class:`Constraint` objects

    Parameters
    ----------
    argv : GeneratorType object
        A Python generator that includes :class:`sasoptpy.Expression` objects
    name : string, optional
        Name (prefix) of the constraints

    Examples
    --------

    >>> var_ind = ['a', 'b', 'c', 'd']
    >>> u = so.VariableGroup(var_ind, name='u')
    >>> t = so.Variable(name='t')
    >>> cg = so.ConstraintGroup((u[i] + 2 * t <= 5 for i in var_ind),
                                name='cg')
    >>> print(cg)
    Constraint Group (cg) [
      [a:  2.0 * t  +  u['a']  <=  5]
      [b:  u['b']  +  2.0 * t  <=  5]
      [c:  2.0 * t  +  u['c']  <=  5]
      [d:  2.0 * t  +  u['d']  <=  5]
    ]

    >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
    >>> cg2 = so.ConstraintGroup((2 * z[i, j] + 3 * z[i-1, j] >= 2 for i in
                                  [1] for j in ['a', 'b', 'c']), name='cg2')
    >>> print(cg2)
    Constraint Group (cg2) [
      [(1, 'a'):  3.0 * z[0, 'a']  +  2.0 * z[1, 'a']  >=  2]
      [(1, 'b'):  2.0 * z[1, 'b']  +  3.0 * z[0, 'b']  >=  2]
      [(1, 'c'):  2.0 * z[1, 'c']  +  3.0 * z[0, 'c']  >=  2]
    ]

    Notes
    -----
    Use :func:`sasoptpy.Model.add_constraints` when working with a single
    model.

    See also
    --------
    :func:`sasoptpy.Model.add_constraints`
    :func:`sasoptpy.Model.include`

    '''

    def __init__(self, argv, name):
        self._condict = {}
        if type(argv) == list or type(argv) == GeneratorType:
            self._recursive_add_cons(argv, name=name, condict=self._condict)
        if name is not None:
            name = sasoptpy.utils.check_name(name, 'con')
            self._name = name
            sasoptpy.utils.register_name(name, self)
        else:
            self._name = None

    def get_name(self):
            '''
            Returns the name of the constraint group

            Returns
            -------
            string
                Name of the constraint group

            Examples
            --------

            >>> c1 = m.add_constraints((x + y[i] <= 4 for i in indices),
                                       name='con1')
            >>> print(c1.get_name())
            con1
            '''
            return self._name

    def _recursive_add_cons(self, argv, name, condict, ckeys=()):
        conctr = 0
        for idx, c in enumerate(argv):
            if type(argv) == list:
                newkeys = ckeys + (idx,)
            elif type(argv) == GeneratorType:
                newkeys = ()
                if argv.gi_code.co_nlocals == 1:
                    vnames = argv.gi_code.co_cellvars
                else:
                    vnames = argv.gi_code.co_varnames
                vdict = argv.gi_frame.f_locals
                for ky in vnames:
                    if ky != '.0':
                        newkeys = newkeys + (vdict[ky],)
            conname = '{}_{}'.format(name, conctr)
            # Proposed change:
            # conname = '{}[{}]'.format(name, ','.join(format(k)
            #                                          for k in newkeys))
            conname = sasoptpy.utils.check_name(conname, 'con')
            newcon = sasoptpy.Constraint(exp=c, name=conname, crange=c._range)
            condict[newkeys] = newcon
            conctr += 1
        self._set_con_info()

    def get_expressions(self, rhs=False):
        '''
        Returns constraints as a list of expressions

        Parameters
        ----------
        rhs : boolean, optional
            Whether to pass the constant part (rhs) of the constraint or not

        Returns
        -------
        :class:`pandas.DataFrame`
            Returns a DataFrame consisting of constraints as expressions

        Examples
        --------

        >>> cg = so.ConstraintGroup((u[i] + 2 * t <= 5 for i in var_ind),
                                    name='cg')
        >>> ce = cg.get_expressions()
        >>> print(ce)
                             cg
        c   u['c']  +  2.0 * t
        b   u['b']  +  2.0 * t
        d   u['d']  +  2.0 * t
        a   u['a']  +  2.0 * t
        >>> ce_rhs = cg.get_expressions(rhs=True)
        >>> print(ce_rhs)
                                      cg
        b      u['b']  -  5  +  2.0 * t
        c   -  5  +  u['c']  +  2.0 * t
        d   -  5  +  u['d']  +  2.0 * t
        a   -  5  +  2.0 * t  +  u['a']

        '''
        cd = {}
        for i in self._condict:
            cd[i] = self._condict[i].copy()
            if rhs is False:
                cd[i]._linCoef['CONST']['val'] = 0
        cd_df = sasoptpy.utils.dict_to_frame(cd, cols=[self._name])
        return cd_df

    def __getitem__(self, key):
        '''
        Overloaded method to access individual constraints

        Parameters
        ----------
        key : string or int
            Key of the constraint

        Returns
        -------
        :class:`Constraint` object
        '''
        key = sasoptpy.utils.tuple_pack(key)
        return self._condict.__getitem__(key)

    def __iter__(self):
        return iter(self._condict.values())

    def _set_con_info(self):
        for i in self._condict:
            self._condict[i]._set_info(parent=self, key=i)

    def __str__(self):
        s = 'Constraint Group ({}) [\n'.format(self._name)
        for k in sorted(self._condict):
            v = self._condict[k]
            s += '  [{}: {}]\n'.format(sasoptpy.utils.tuple_unpack(k),
                                       v)
        s += ']'
        return s

    def __repr__(self):
        s = 'sasoptpy.ConstraintGroup(['
        for i in self._condict:
            s += '{}, '.format(str(self._condict[i]))
        s += '], '
        s += 'name=\'{}\')'.format(self._name)
        return s
