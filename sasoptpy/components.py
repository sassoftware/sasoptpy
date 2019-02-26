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

from collections import OrderedDict
from itertools import product
from math import copysign, inf
from types import GeneratorType
import warnings

import numpy as np
import pandas as pd

import sasoptpy.utils


class Expression:
    """
    Creates a mathematical expression to represent model components

    Parameters
    ----------
    exp : Expression, optional
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

    >>> import sasoptpy.math as sm
    >>> f = sm.sin(x) + sm.min(y[1],1) ** 2
    >>> print(type(f))
    <class 'sasoptpy.components.Expression'>
    >>> print(f)
    sin(x) + (min(y[1] , 1)) ** (2)

    Notes
    -----
    * Two other classes (:class:`Variable` and :class:`Constraint`) are
      subclasses of this class.
    * Expressions are created automatically after linear math operations
      with variables.
    * An expression object can be called when defining constraints and other
      expressions.
    """

    def __init__(self, exp=None, name=None, temp=False):
        if name is not None:
            self._name = sasoptpy.utils.check_name(name, 'expr')
            self._objorder = sasoptpy.utils.register_name(self._name, self)
        else:
            self._name = None
        self._value = 0
        self._dual = None
        self._linCoef = OrderedDict()
        if exp is None:
            self._linCoef['CONST'] = {'ref': None, 'val': 0}
        else:
            if isinstance(exp, Expression):
                for mylc in exp._linCoef:
                    self._linCoef[mylc] = dict(exp._linCoef[mylc])
            elif np.issubdtype(type(exp), np.number):
                self._linCoef['CONST'] = {'ref': None, 'val': exp}
            else:
                print('WARNING: An invalid type is passed to create an ' +
                      'Expression: {}'.format(type(exp)))
        self._temp = temp
        self._value = 0
        self._operator = None
        self._arguments = []
        self._iterkey = []
        self._abstract = False
        self._conditions = []
        self._keep = False

    def copy(self, name=None):
        """
        Returns a copy of the :class:`Expression` object

        Parameters
        ----------
        name : string, optional
            Name for the copy

        Returns
        -------
        r : Expression
            Copy of the object

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> y = so.VariableGroup(1, name='y')
        >>> e = so.Expression(7 * x - y[0], name='e')
        >>> print(repr(e))
        sasoptpy.Expression(exp =  -  y[0]  +  7.0 * x , name='e')
        >>> f = e.copy(name='f')
        >>> print(repr(f))
        sasoptpy.Expression(exp =  -  y[0]  +  7.0 * x , name='f')

        """
        r = Expression(name=name)
        for mylc in self._linCoef:
            r._linCoef[mylc] = dict(self._linCoef[mylc])
        r._operator = self._operator
        r._iterkey = self._iterkey
        r._abstract = self._abstract
        r._conditionts = self._conditions
        return r

    def get_value(self):
        """
        Calculates and returns the value of the linear expression

        Returns
        -------
        v : float
            Value of the expression

        Examples
        --------

        >>> sales = so.Variable(name='sales', init=10)
        >>> material = so.Variable(name='material', init=3)
        >>> profit = so.Expression(5 * sales - 3 * material)
        >>> print(profit.get_value())
        41

        """
        v = 0
        for mylc in self._linCoef:
            if self._linCoef[mylc]['ref'] is not None:
                if isinstance(mylc, tuple):
                    v += sasoptpy.utils._evaluate(self._linCoef[mylc])
                else:
                    v += self._linCoef[mylc]['val'] * \
                        self._linCoef[mylc]['ref'].get_value()
            else:
                v += self._linCoef[mylc]['val']
        if self._operator:
            try:
                import sasoptpy.math as sm
                if self._arguments:
                    vals = [i.get_value() if isinstance(i, Expression) else i for i in self._arguments]
                    v = sm.func_equivalent[self._operator](v, *vals)
                else:
                    v = sm.func_equivalent[self._operator](v)
            except:
                print(self._arguments)
                print('ERROR: Unknown operator: {}'.format(self._operator))
        return round(v, 6)

    def get_dual(self):
        """
        Returns the dual value

        Returns
        -------
        dual : float
            Dual value of the variable

        """
        return self._dual

    def set_name(self, name=None):
        """
        Sets the name of the expression

        Parameters
        ----------
        name : string
            Name of the expression

        Returns
        -------
        name : string
            Name of the expression after resolving conflicts

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> e = x**2 + 2*x + 1
        >>> e.set_name('expansion')

        """
        if self._name is not None and not name:
            # Expression has already a name and if no name is passed
            return self._name
        nd = sasoptpy.utils.get_namedict()
        if self._name is not None:
            if self._name in nd:
                del nd[self._name]
        safe_name = sasoptpy.utils.check_name(name, 'expr')
        if name and name != safe_name:
            print('NOTE: Name {} is changed to {} to prevent a conflict'
                  .format(name, safe_name))
        order = sasoptpy.utils.register_name(self._name, self)
        if hasattr(self, '_objorder') and not self._objorder:
            self._objorder = order
        self._name = safe_name
        return self._name

    def get_name(self):
        """
        Returns the name of the expression

        Returns
        -------
        name : string
            Name of the expression

        Examples
        --------

        >>> m = so.Model()
        >>> var1 = m.add_variables(name='x')
        >>> print(var1.get_name())
        x
        """
        return self._name

    def set_permanent(self, name=None):
        """
        Converts a temporary expression into a permanent one

        Parameters
        ----------
        name : string, optional
            Name of the expression

        Returns
        -------
        name : string
            Name of the expression in the namespace
        """
        if self._name is None:
            self._name = sasoptpy.utils.check_name(name, 'expr')
            self._objorder = sasoptpy.utils.register_name(self._name, self)
        self._temp = False
        return self._name

    def _expr(self):
        """
        Generates the OPTMODEL compatible string representation of the object.

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> y = so.Variable(name='y')
        >>> f = x + y ** 2
        >>> print(f)
        x + (y) ** (2)
        >>> print(f._expr())
        x + (y) ^ (2)

        """
        # Add the operator first if exists
        s = ''
        if self._operator:
            s += self._operator
            if self._iterkey:
                if self._operator == 'sum':
                    s += sasoptpy.utils._to_optmodel_loop(self._iterkey)
            s += '('

        itemcnt = 0
        firstel = True

        # Add every element into string one by one
        for idx, el in self._linCoef.items():
            val = el['val']
            ref = el['ref']
            op = el.get('op')
            csign = copysign(1, val)

            # Skip elements with 0 coefficient or constant
            if val == 0 or idx == 'CONST':
                continue

            # Append sign of the value unless it is positive and first
            if firstel and csign == 1:
                pass
            elif csign == 1:
                s += '+ '
            elif csign == -1:
                s += '- '
            firstel = False

            # Add operand if exists, default is product
            if op:
                optext = ' {} '.format(op)
            else:
                optext = ' * '

            # For a list of expressions, a recursive function is called
            if isinstance(ref, list):
                strlist = sasoptpy.utils.recursive_walk(
                    ref, func='_expr')
            else:
                strlist = [ref._expr()]
            if optext != ' * ':
                strlist = ['({})'.format(stritem)
                           for stritem in strlist]

            # Merge all elements in strlist together
            refs = optext.join(strlist)
            if val == 1 or val == -1:
                s += '{} '.format(refs)
            elif op:
                s += '{} * ({}) '.format(round(abs(val), 12), refs)
            else:
                s += '{} * {} '.format(round(abs(val), 12), refs)

            itemcnt += 1

        # CONST is always at the end
        if itemcnt == 0 or (self._linCoef['CONST']['val'] != 0 and
                            not isinstance(self, Constraint)):
            val = self._linCoef['CONST']['val']
            csign = copysign(1, val)
            if csign < 0:
                s += '- '
            elif firstel:
                pass
            else:
                s += '+ '
            s += '{} '.format(abs(val))

        # Close operator parentheses and add remaining elements
        if self._operator:
            if self._arguments:
                s += ', ' + ', '.join(i._expr() if hasattr(i, '_expr') else str(i) for i in self._arguments)
            s = s.rstrip()
            s += ')'
        s = s.rstrip()
        return s

    def __repr__(self):
        """
        Returns a string representation of the object.

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> y = so.Variable(name='y')
        >>> f = x + y ** 2
        >>> print(repr(f))
        sasoptpy.Expression(exp = x + (y) ** (2), name=None)

        """
        s = 'sasoptpy.Expression('
        if self._name is not None:
            s += 'exp = {}, name=\'{}\''.format(str(self), self._name)
        else:
            s += 'exp = {}, name=None'.format(str(self))
        s += ')'
        return s

    def _defn(self):
        if self._operator is None:
            s = self._expr()
        else:
            s = '{}'.format(self._operator)
            if self._iterkey != []:
                s += '{'
                s += ', '.join([i._defn() for i in list(self._iterkey)])
                s += '}'
            s += '('
            s += self._expr()
            s += ')'
        return s

    def __str__(self):
        """
        Generates a representation string that is Python compatible

        Examples
        --------

        >>> f = x + y ** 2
        >>> print(str(f))
        x + (y) ** (2)

        """
        s = ''

        itemcnt = 0
        firstel = True
        if self._operator:
            s += str(self._operator) + '('
        for idx, el in self._linCoef.items():
            val = el['val']
            ref = el['ref']
            op = el.get('op')
            csign = copysign(1, val)

            # Skip elements with 0 coefficient or constant
            if val == 0 or idx == 'CONST':
                continue

            # Append sign of the value unless it is positive and first
            if firstel and csign == 1:
                pass
            elif csign == 1:
                s += '+ '
            elif csign == -1:
                s += '- '
            firstel = False

            if op:
                optext = ' {} '.format(
                    sasoptpy.utils._py_symbol(op))
            else:
                optext = ' * '

            if isinstance(ref, list):
                strlist = sasoptpy.utils.recursive_walk(
                    ref, func='__str__')
            else:
                strlist = [ref.__str__()]
            if optext != ' * ':
                strlist = ['({})'.format(stritem)
                           for stritem in strlist]

            refs = optext.join(strlist)
            refs = optext.join(strlist)
            if val == 1 or val == -1:
                s += '{} '.format(refs)
            elif op:
                s += '{} * ({}) '.format(round(abs(val), 12), refs)
            else:
                s += '{} * {} '.format(round(abs(val), 12), refs)
            itemcnt += 1

        # CONST is always at the end
        if itemcnt == 0 or (self._linCoef['CONST']['val'] != 0 and
                            not isinstance(self, Constraint)):
            val = self._linCoef['CONST']['val']
            csign = copysign(1, val)
            if csign < 0:
                s += '- '
            elif firstel:
                pass
            else:
                s += '+ '
            s += '{} '.format(abs(val))

        if self._operator:
            if self._iterkey:
                forlist = []
                for i in self._iterkey:
                    if isinstance(i, sasoptpy.data.SetIterator):
                        if i._multi:
                            forlist.append('for ({}) in {}'.format(
                                i._expr(), i._set._name))
                        else:
                            forlist.append('for {} in {}'.format(
                                i._expr(), i._set._name))
                    else:
                        forlist.append('for {} in {}'.format(
                            i._name, i._set._name))
                s += ' '.join(forlist)
            if self._arguments:
                s += ', ' + ', '.join(str(i) for i in self._arguments)
            s = s.rstrip()
            s += ')'
        s = s.rstrip()
        return s

    def _add_coef_value(self, var, key, value):
        """
        Changes value of a variable inside the :class:`Expression` object in
        place

        Parameters
        ----------
        var : Variable
            Variable object whose value will be changed
        key : string
            Name of the variable object
        value : float
            New value or the addition to the existing value of the variable
        """
        if key in self._linCoef:
            self._linCoef[key]['val'] += value
        else:
            self._linCoef[key] = {'ref': var, 'val': value}

    def add(self, other, sign=1):
        """
        Combines two expressions and produces a new one

        Parameters
        ----------
        other : float or Expression
            Second expression or constant value to be added
        sign : int, optional
            Sign of the addition, 1 or -1

        Returns
        -------
        r : Expression
            Reference to the outcome of the operation

        Notes
        -----
        * This method is mainly for internal use.
        * Adding an expression is equivalent to calling this method:
          (x-y)+(3*x-2*y) and (x-y).add(3*x-2*y) are interchangeable.
        """
        if self._temp and type(self) is Expression:
            r = self
        else:
            if isinstance(other, Expression) and other._temp:
                r = other
                other = self
                sign = sign * -1
            elif self._operator is not None:
                r = Expression()
                r._linCoef[self.set_name()] = {'val': 1, 'ref': self}
            else:
                r = self.copy()
                if r._operator is not None:
                    r = sasoptpy.utils.wrap(r)
        if isinstance(other, Expression):
            if other._abstract:
                r._abstract = True
            if other._operator is None:
                for v in other._linCoef:
                    if v in r._linCoef:
                        r._linCoef[v]['val'] += sign * other._linCoef[v]['val']
                    else:
                        r._linCoef[v] = dict(other._linCoef[v])
                        r._linCoef[v]['val'] *= sign
            else:
                r._linCoef[other.set_name()] = {'val': sign, 'ref': other}
            r._conditions += self._conditions
            r._conditions += other._conditions
        elif np.issubdtype(type(other), np.number):
            r._linCoef['CONST']['val'] += sign * other
        return r

    def mult(self, other):
        """
        Multiplies the :class:`Expression` with a scalar value

        Parameters
        ----------
        other : Expression or int
            Second expression to be multiplied

        Returns
        -------
        r : Expression
            A new :class:`Expression` that represents the multiplication

        Notes
        -----
        * This method is mainly for internal use.
        * Multiplying an expression is equivalent to calling this method:
          3*(x-y) and (x-y).mult(3) are interchangeable.

        """
        if isinstance(other, Expression):
            r = Expression()
            if self._abstract or other._abstract:
                r._abstract = True
            target = r._linCoef
            for i, x in self._linCoef.items():
                for j, y in other._linCoef.items():
                    if x['ref'] is None and y['ref'] is None:
                        target['CONST'] = {
                            'ref': None, 'val': x['val']*y['val']}
                    elif x['ref'] is None:
                        if x['val'] * y['val'] != 0:
                            target[j] = {
                                'ref': y['ref'], 'val': x['val']*y['val']}
                    elif y['ref'] is None:
                        if x['val'] * y['val'] != 0:
                            target[i] = {
                                'ref': x['ref'], 'val': x['val']*y['val']}
                    else:  # TODO indexing is not interchangable,
                        if x['val'] * y['val'] != 0:
                            if x.get('op') is None and y.get('op') is None:
                                newkey = sasoptpy.utils.tuple_pack(i) +\
                                         sasoptpy.utils.tuple_pack(j)
                                target[newkey] = {
                                    'ref': list(x['ref']) + list(y['ref']),
                                    'val': x['val'] * y['val']}
                            else:
                                newkey = (i, j)
                                x_actual = x['ref']
                                if 'op' in x and x['op'] is not None:
                                    x_actual = sasoptpy.utils.wrap(x)
                                y_actual = y['ref']
                                if 'op' in y and y['op'] is not None:
                                    y_actual = sasoptpy.utils.wrap(y)
                                target[newkey] = {
                                    'ref': [x_actual, y_actual],
                                    'val': x['val'] * y['val']}
            r._conditions += self._conditions
            r._conditions += other._conditions
            return r
        elif np.issubdtype(type(other), np.number):
            if self._temp and type(self) is Expression:
                if other == 0:
                    self._linCoef = OrderedDict()
                    self._linCoef['CONST'] = {'ref': None, 'val': 0}
                else:
                    for mylc in self._linCoef:
                        self._linCoef[mylc]['val'] *= other
                r = self
                return r
            else:
                if other == 0:
                    r = Expression()
                else:
                    r = self.copy()
                    for mylc in r._linCoef:
                        r._linCoef[mylc]['val'] *= other
                return r

    # def _tag_constraint(self, *argv):
    #     pass

    def _relational(self, other, direction_):
        """
        Creates a logical relation between :class:`Expression` objects

        Parameters
        ----------
        other : Expression
            Expression on the other side of the relation wrt self
        direction_ : string
            Direction of the logical relation, either 'E', 'L', or 'G'

        Returns
        -------
        generated_constraint : Constraint
            Constraint generated as a result of linear relation

        """
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
                if self._operator is None:
                    r = self.copy()
                else:
                    r = Expression(0)
                    r += self
            #  TODO r=self could be used whenever expression has no name
            if np.issubdtype(type(other), np.number):
                r._linCoef['CONST']['val'] -= other
            elif isinstance(other, Expression):
                r -= other
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

    def _is_linear(self):
        """
        Checks if the expression is composed of linear components

        Returns
        -------
        is_linear : boolean
            True if the expression is linear, False otherwise

        Examples
        --------

        >>> x = so.Variable()
        >>> e = x*x
        >>> print(e.is_linear())
        False

        >>> f = x*x + x*x - 2*x*x + 5
        >>> print(f.is_linear())
        True

        """

        self._clean()

        # Loop over components
        for val in self._linCoef.values():
            if val.get('op', False):
                return False
            if type(val['ref']) is list:
                return False
            if val['ref'] and val['ref']._operator:
                return False
        return True

    def __hash__(self):
        return hash('{}{}'.format(self._name, id(self)))

    def _clean(self):
        keys_to_clean = []
        for key in self._linCoef.keys():
            if key != 'CONST' and self._linCoef[key]['val'] == 0:
                keys_to_clean.append(key)
        for key in keys_to_clean:
            del self._linCoef[key]

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.add(other, -1)

    def __mul__(self, other):
        return self.mult(other)

    def __pow__(self, other):
        r = Expression()
        if not isinstance(other, Expression):
            other = Expression(other, name='')
        self.set_permanent()
        r._linCoef[self._name, other._name, '^'] = {
            'ref': [self, other],
            'val': 1,
            'op': '^'
            }
        r._abstract = self._abstract or other._abstract
        return r

    def __rpow__(self, other):
        r = Expression()
        if not isinstance(other, Expression):
            other = Expression(other, name='')
        r._linCoef[other._name, self._name, '^'] = {
            'ref': [other, self],
            'val': 1,
            'op': '^'
            }
        r._abstract = self._abstract or other._abstract
        return r

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
        if np.issubdtype(type(other), np.number):
            try:
                return self.mult(1/other)
            except ZeroDivisionError:
                print('ERROR: Float division by zero')
                return None
        r = Expression()
        if not isinstance(other, Expression):
            other = Expression(other, name='')
        r._linCoef[self._name, other._name, '/'] = {
            'ref': [self, other],
            'val': 1,
            'op': '/'
            }
        r._abstract = self._abstract or other._abstract
        return r

    def __rtruediv__(self, other):
        r = Expression()
        if not isinstance(other, Expression):
            other = Expression(other, name='')
        r._linCoef[other._name, self._name, '/'] = {
            'ref': [other, self],
            'val': 1,
            'op': '/'
            }
        r._abstract = self._abstract or other._abstract
        return r

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

    def __iter__(self):
        return iter([self])


class Variable(Expression):
    """
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
    abstract : boolean, optional
        Indicator of whether the variable is abstract or not
    shadow : boolean, optional
        Indicator of whether the variable is shadow or not\
        Used for internal purposes

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

    """

    def __init__(self, name, vartype=sasoptpy.utils.CONT, lb=-inf, ub=inf,
                 init=None, abstract=False, shadow=False, key=None):
        super().__init__()
        if not shadow:
            name = sasoptpy.utils.check_name(name, 'var')
        self._name = name
        self._type = vartype
        if lb is None:
            lb = -inf
        if ub is None:
            ub = inf
        self._lb = lb
        self._ub = ub
        self._init = init
        if self._init is not None:
            self._value = self._init
        if vartype == sasoptpy.utils.BIN:
            self._lb = max(self._lb, 0)
            self._ub = min(self._ub, 1)
        if shadow:
            self._linCoef[name + str(id(self))] = {'ref': self, 'val': 1}
        else:
            self._linCoef[name] = {'ref': self, 'val': 1}
            self._objorder = sasoptpy.utils.register_name(name, self)
        self._key = key
        self._parent = None
        self._temp = False
        self._abstract = abstract
        self._shadow = shadow

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    def set_bounds(self, lb=None, ub=None):
        """
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

        """
        if lb is not None:
            self._lb = lb
        if ub is not None:
            self._ub = ub

    def set_init(self, init=None):
        """
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

        """
        self._init = init

    def get_value(self):
        """
        Returns value of a variable
        """
        return self._value

    def set_value(self, value):
        """
        Sets the value of a variable
        """
        self._value = value

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        st = 'sasoptpy.Variable(name=\'{}\', '.format(self._name)
        if self._lb is not 0:
            st += 'lb={}, '.format(self._lb)
        if self._ub is not inf:
            st += 'ub={}, '.format(self._ub)
        if self._init is not None:
            st += 'init={}, '.format(self._init)
        if self._abstract:
            st += 'abstract=True, '
        if self._shadow:
            st += 'shadow=True, '
        st += ' vartype=\'{}\')'.format(self._type)
        return st

    def __str__(self):
        """
        Generates a representation string
        """
        if self._parent is not None and self._key is not None:
            keylist = [i._expr() if isinstance(i, Expression)
                       else str(i) for i in self._key]
            key = ', '.join(keylist)
            return ('{}[{}]'.format(self._parent._name, key))
        if self._shadow and self._iterkey:
            keylist = [i._expr() if isinstance(i, Expression)
                       else str(i) for i in self._iterkey]
            key = ', '.join(keylist)
            return('{}[{}]'.format(self._name, key))
        return('{}'.format(self._name))

    def _expr(self):
        if self._parent is not None and self._key is not None:
            keylist = sasoptpy.utils._to_iterator_expression(self._key)
            key = ', '.join(keylist)
            return ('{}[{}]'.format(self._parent._name, key))
        if self._shadow and self._iterkey:
            keylist = sasoptpy.utils._to_iterator_expression(self._iterkey)
            key = ', '.join(keylist)
            return('{}[{}]'.format(self._name, key))
        return('{}'.format(self._name))

    def _defn(self):
        s = 'var {}'.format(self._name)
        BIN = sasoptpy.utils.BIN
        CONT = sasoptpy.utils.CONT
        if self._type != CONT:
            if self._type == BIN:
                s += ' binary'
            else:
                s += ' integer'
        if self._lb != -inf:
            if not (self._lb == 0 and self._type == BIN):
                s += ' >= {}'.format(self._lb)
        if self._ub != inf:
            if not (self._ub == 1 and self._type == BIN):
                s += ' <= {}'.format(self._ub)
        if self._init is not None:
            s += ' init {}'.format(self._init)
        s += ';'
        return(s)

    # def _tag_constraint(self, c):
    #     """
    #     Adds a constraint into list of constraints that the variable appears
    #     """
    #     if c is not None:
    #         self._cons.add(c._name)


class Constraint(Expression):
    """
    Creates a linear or quadratic constraint for optimization models

    Constraints should be created by adding logical relations to
    :class:`Expression` objects.

    Parameters
    ----------
    exp : Expression
        A logical expression that forms the constraint
    direction : string
        Direction of the logical expression, 'E' (=), 'L' (<=) or 'G' (>=)
    name : string, optional
        Name of the constraint object
    crange : float, optional
        Range for ranged constraints

    Examples
    --------

    >>> x = so.Variable(name='x')
    >>> y = so.Variable(name='y')
    >>> c1 = so.Constraint( 3 * x - 5 * y <= 10, name='c1')
    >>> print(repr(c1))
    sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

    >>> c2 = so.Constraint( - x + 2 * y - 5, direction='L', name='c2')
    sasoptpy.Constraint( -  x  +  2.0 * y  <=  5, name='c2')

    Notes
    -----

    * A constraint can be generated in multiple ways:

      1. Using the :func:`sasoptpy.Model.add_constraint` method

         >>> m = so.Model(name='m')
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
    """

    def __init__(self, exp, direction=None, name=None, crange=0):
        super().__init__()
        if name is not None:
            name = sasoptpy.utils.check_name(name, 'con')
            self._name = name
            self._objorder = sasoptpy.utils.register_name(name, self)
        else:
            self._name = None
        if exp._name is None:
            self._linCoef = exp._linCoef
        else:
            for m in exp._linCoef:
                self._linCoef[m] = dict(exp._linCoef[m])
        if direction is None:
            self._direction = exp._direction
        else:
            self._direction = direction
        self._range = crange
        self._key = None
        self._parent = None
        self._block = None
        self._temp = False

    def __and__(self, other):
        print('Called!')
        print(self)
        print(other)
        return self

    def update_var_coef(self, var, value):
        """
        Updates the coefficient of a variable inside the constraint

        Parameters
        ----------
        var : Variable
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

        """
        varname = var._name
        if varname in self._linCoef:
            self._linCoef[varname]['val'] = value
        else:
            self._linCoef[varname] = {'ref': var, 'val': value}

    def set_rhs(self, value):
        """
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

        """
        self._linCoef['CONST']['val'] = -value

    def set_direction(self, direction):
        """
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

        """
        if direction in ['E', 'L', 'G']:
            self._direction = direction
        else:
            print('WARNING: Cannot change constraint direction {} {}'.format(
                self._name, direction))

    def set_block(self, block_number):
        """
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

        """
        self._block = block_number

    def get_value(self, rhs=False):
        """
        Returns the current value of the constraint

        Parameters
        ----------
        rhs : boolean, optional
            Whether constant values (RHS) will be included in the value or not.
            Default is false

        Examples
        --------

        >>> x = so.Variable(name='x', init=2)
        >>> c = so.Constraint(x ** 2 + 2 * x <= 15, name='c')
        >>> print(c.get_value())
        8
        >>> print(c.get_value(rhs=True))
        -7

        """
        v = super().get_value()
        if rhs:
            return v
        else:
            v -= self._linCoef['CONST']['val']
            return v

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    def _defn(self):
        s = ''
        if self._parent is None:
            s = 'con {} : '.format(self._name)
        if self._range != 0:
            s += '{} <= '.format(- self._linCoef['CONST']['val'])
        s += super()._expr()
        if self._direction == 'E' and self._range == 0:
            s += ' = '
        elif self._direction == 'L':
            s += ' <= '
        elif self._direction == 'G':
            s += ' >= '
        elif self._direction == 'E' and self._range != 0:
            s += ' <= '
        else:
            raise Exception('Constraint has no direction!')
        s += '{}'.format(- self._linCoef['CONST']['val'] + self._range)
        if self._parent is None:
            s += ';'
            # Currently we switch to frame when blocks are set
            # if self._block:
            #     s += '\n'
            #     s += self._name + '.block = ' + str(self._block) + ';'
        return(s)

    def __str__(self):
        """
        Generates a representation string
        """
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
        """
        Returns a string representation of the object.
        """
        if self._name is not None:
            st = 'sasoptpy.Constraint({}, name=\'{}\')'
            s = st.format(str(self), self._name)
        else:
            st = 'sasoptpy.Constraint({}, name=None)'
            s = st.format(str(self))
        return s


class VariableGroup:
    """
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

    """

    def __init__(self, *argv, name, vartype=sasoptpy.utils.CONT, lb=-inf,
                 ub=inf, init=None, abstract=False):
        self._vardict = OrderedDict()
        self._varlist = []
        self._groups = OrderedDict()
        self._keyset = []

        if vartype == sasoptpy.utils.BIN and ub is None:
            ub = 1
        if vartype == sasoptpy.utils.BIN and lb is None:
            lb = 0
        if vartype == sasoptpy.utils.INT and lb is None:
            lb = 0

        self._recursive_add_vars(*argv, name=name,
                                 vartype=vartype, lb=lb, ub=ub, init=init,
                                 vardict=self._vardict, varlist=self._varlist,
                                 abstract=abstract)

        self._lb = lb if lb is not None else -inf
        self._ub = ub if ub is not None else inf
        self._init = init
        self._type = vartype

        if name is not None:
            name = sasoptpy.utils.check_name(name, 'var')
            self._name = name
            self._objorder = sasoptpy.utils.register_name(name, self)
        else:
            self._name = None
        self._abstract = abstract
        for arg in argv:
            if isinstance(arg, int):
                self._keyset.append(
                    sasoptpy.utils.extract_argument_as_list(arg))
            else:
                self._keyset.append(sasoptpy.utils.extract_argument_as_list(arg))
                if not self._abstract and isinstance(arg, sasoptpy.data.Set):
                    self._abstract = True
                    for _, v in self._vardict.items():
                        v._abstract = True
        self._shadows = OrderedDict()
        self._set_var_info()

    def get_name(self):
        """
        Returns the name of the variable group

        Returns
        -------
        name : string
            Name of the variable group

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> var1 = m.add_variables(4, name='x')
        >>> print(var1.get_name())
        x
        """
        return self._name

    def add_member(self, key, var=None, name=None, vartype=None, lb=None,
                   ub=None, init=None, shadow=False):
        """
        (Experimental) Adds a new member to Variable Group

        Notes
        -----

        - This method is mainly intended for internal use.

        """

        key = sasoptpy.utils.tuple_pack(key)
        dict_to_add = self._vardict if not shadow else self._shadows

        if var is not None:
            dict_to_add[key] = var
            return var
        else:
            vartype = vartype if vartype is not None else self._type
            lb = lb if lb is not None else self._lb
            ub = ub if ub is not None else self._ub
            if name is not None:
                varname = name
            else:
                varname = '{}['.format(self._name) + ','.join(
                        format(k) for k in key) + ']'
            new_var = sasoptpy.Variable(
                name=varname, lb=lb, ub=ub, init=init, vartype=vartype,
                shadow=shadow, abstract=False)
            dict_to_add[key] = new_var
            return new_var

    def _recursive_add_vars(self, *argv, name, vartype, lb, ub, init,
                            vardict=None, varlist=None, vkeys=(), abstract=False):
        if vardict is None:
            vardict = OrderedDict()
        if varlist is None:
            varlist = list()
        the_list = sasoptpy.utils.extract_argument_as_list(argv[0])
        for _, i in enumerate(the_list):
            if isinstance(i, tuple):
                newfixed = vkeys + i
            else:
                newfixed = vkeys + (i,)
            if len(argv) == 1:
                varname = '{}['.format(name) + ','.join(
                    format(k) for k in newfixed) + ']'
                for j, k in enumerate(newfixed):
                    try:
                        self._groups[j] = self._groups[j].union(pd.Index([k]))
                    except KeyError:
                        self._groups[j] = pd.Index([k])  # pd.Index behaves as an ordered set
                varlb = sasoptpy.utils.extract_list_value(newfixed, lb)
                varub = sasoptpy.utils.extract_list_value(newfixed, ub)
                varin = sasoptpy.utils.extract_list_value(newfixed, init)
                new_var = sasoptpy.Variable(
                    name=varname, lb=varlb, ub=varub, init=varin,
                    vartype=vartype, abstract=abstract)
                vardict[newfixed] = new_var
                varlist.append(newfixed)
            else:
                self._recursive_add_vars(*argv[1:], vardict=vardict,
                                         vkeys=newfixed,
                                         name=name, vartype=vartype,
                                         lb=lb, ub=ub, init=init,
                                         varlist=varlist)

    def _set_var_info(self):
        for i in self._vardict:
            self._vardict[i]._set_info(parent=self, key=i)

    def __getitem__(self, key):
        """
        Overloaded method to access individual variables

        Parameters
        ----------
        key : tuple, string or int
            Key of the variable

        Returns
        -------
        ref : Variable or list
            Reference to a single Variable or a list of Variable objects

        """
        if self._abstract or isinstance(key, sasoptpy.data.SetIterator):
            # TODO check if number of keys correct e.g. x[I], x[1,2] requested
            tuple_key = sasoptpy.utils.tuple_pack(key)
            tuple_key = tuple(i for i in sasoptpy.utils.flatten_tuple(tuple_key))
            if tuple_key in self._vardict:
                return self._vardict[tuple_key]
            elif tuple_key in self._shadows:
                return self._shadows[tuple_key]
            else:
                k = list(self._vardict)[0]
                v = self._vardict[k]
                vname = self._name
                vname = vname.replace(' ', '')
                shadow = Variable(name=vname, vartype=v._type, lb=v._lb,
                                  ub=v._ub, init=v._init, abstract=True,
                                  shadow=True)
                ub = sasoptpy.data.ParameterValue(shadow, key=tuple_key,
                                                  suffix='.ub')
                lb = sasoptpy.data.ParameterValue(shadow, key=tuple_key,
                                                  suffix='.lb')
                shadow._ub = ub
                shadow._lb = lb
                shadow._iterkey = tuple_key
                self._shadows[tuple_key] = shadow
                return shadow

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
        """
        Yields an iterable list of variables inside the variable group

        Returns
        -------
        i : list
            Iterable list of Variable objects
        """
        for i in self._varlist:
            yield self._vardict[i]

    def _defn(self, tabs=''):
        """
        Returns string to be used in OPTMODEL definition

        Parameters
        ----------

        tabs : string, optional
            Tab string that is used in :meth:`Model.to_optmodel` method

        """
        s = tabs + 'var {}'.format(self._name)
        s += ' {'
        for i in self._keyset:
            if isinstance(i, sasoptpy.data.Set):
                s += '{}, '.format(i._name)
            elif isinstance(i, list) or isinstance(i, range):
                ind_list = []
                for j in i:
                    ind_list.append(sasoptpy.utils._to_quoted_string(j))
                s += '{{{}}}, '.format(','.join(ind_list))
            elif isinstance(i, dict):
                s += '{{{}}}, '.format(','.join(
                    sasoptpy.utils._to_quoted_string(j) for j in i.keys()))
            else:
                try:
                    s += '{}, '.format(i)
                except:
                    print('ERROR: VariableGroup {} has invalid index {} ({})'.
                          format(self._name, str(i), type(i)))
        s = s[:-2]
        s += '} '
        # Grab features
        CONT = sasoptpy.utils.CONT
        BIN = sasoptpy.utils.BIN
        INT = sasoptpy.utils.INT
        if self._type != CONT:
            if self._type == BIN:
                s += 'binary '
            if self._type == INT:
                s += 'integer '
        if self._lb is not None and\
           np.issubdtype(type(self._lb), np.number) and\
           self._lb != -inf and\
           not(self._lb == 0 and self._type == BIN):
            s += '>= {} '.format(self._lb)
        if self._ub is not None and\
           np.issubdtype(type(self._ub), np.number) and\
           self._ub != inf and\
           not(self._ub == 1 and self._type == BIN):
            s += '<= {} '.format(self._ub)
        if self._init is not None:
            s += 'init {} '.format(self._init)

        s = s.rstrip()
        s += ';'
        # Check bounds to see if they are parameters
        if self._abstract:
            for i in self._shadows:
                v = self._shadows[i]
                lbparam = str(v) + '.lb' != str(v._lb)
                ubparam = str(v) + '.ub' != str(v._ub)
                if lbparam or ubparam:
                    s += '\n' + tabs
                    loop_text = sasoptpy.utils._to_optmodel_loop(i)
                    if loop_text != '':
                        s += 'for' + loop_text + ' '
                    if lbparam:
                        if isinstance(v._lb, Expression):
                            s += str(v) + '.lb=' + v._lb._defn()
                        else:
                            s += str(v) + '.lb=' + str(v._lb)
                        s += ' '
                    if ubparam:
                        if isinstance(v._ub, Expression):
                            s += str(v) + '.ub=' + v._ub._defn()
                        else:
                            s += str(v) + '.ub=' + str(v._ub)
                        s += ' '
                    s = s.rstrip()
                    s += ';'
                initparam = v._init is not None and v._init != self._init
                if initparam:
                    print(i)
                    print(self._shadows[i])
                    print(self._shadows[i]._init)
                    print(self._init)
                    print(v._init)
                    print(str(v._init))
                    s += '\n' + tabs
                    loop_text = sasoptpy.utils._to_optmodel_loop(i)
                    if loop_text != '':
                        s += 'for ' + loop_text
                    s += str(v) + ' = ' + str(v._init)
                    s = s.rstrip()
                    s += ';'
        else:
            for _, v in self._vardict.items():
                # Check if LB needs to be printed
                printlb = False
                defaultlb = -inf if self._type is CONT else 0
                if v._lb is not None:
                    if self._lb is None or not np.issubdtype(type(self._lb), np.number):
                        printlb = True
                    elif v._lb == defaultlb and (self._lb is not None and self._lb != defaultlb):
                        printlb = True
                    elif v._lb != self._lb:
                        printlb = True
                if printlb:
                    s += '\n' + tabs + '{}.lb = {};'.format(v._expr(), v._lb if v._lb != -inf else "-constant('BIG')")

                # Check if UB needs to be printed
                printub = False
                defaultub = 1 if self._type is BIN else inf
                if v._ub is not None:
                    if self._ub is None or not np.issubdtype(type(self._ub), np.number):
                        printub = True
                    elif v._ub == defaultub and (self._ub is not None and self._ub != defaultub):
                        printub = True
                    elif v._ub != self._ub:
                        printub = True
                if printub:
                    s += '\n' + tabs + '{}.ub = {};'.format(v._expr(), v._ub if v._ub != inf else "constant('BIG')")

                # Check if init needs to be printed
                if v._init is not None:
                    if v._init != self._init:
                        s += '\n' + tabs + '{} = {};'.format(v._expr(), v._init)

        return(s)

    def sum(self, *argv):
        """
        Quick sum method for the variable groups

        Parameters
        ----------
        argv : Arguments
            List of indices for the sum

        Returns
        -------
        r : Expression
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

        """
        if self._abstract:
            r = Expression()
            ind_set = list()
            iter_key = list()
            for i, a in enumerate(argv):
                if isinstance(a, str) and a == '*':
                    si = sasoptpy.data.SetIterator(self._keyset[i])
                    ind_set.append(si)
                    iter_key.append(si)
                else:
                    ind_set.append(a)
            r = r.add(self[tuple(ind_set)])
            r._operator = 'sum'
            r._iterkey = iter_key
            return r
        else:
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
        """
        Quick multiplication method for the variable groups

        Parameters
        ----------
        vector : list, dictionary, :class:`pandas.Series`,\
                 or :class:`pandas.DataFrame`
            Vector to be multiplied with the variable group

        Returns
        -------
        r : Expression
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
        NOTE: Initialized model model1
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

        """

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

    def set_init(self, init):
        """
        Sets / updates initial value for the given variable

        Parameters
        ----------
        init : float, list, dict, :class:`pandas.Series`
            Initial value of the variables

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> y = m.add_variables(3, name='y')
        >>> print(y._defn())
        var y {{0,1,2}};
        >>> y.set_init(5)
        >>> print(y._defn())
        var y {{0,1,2}} init 5;

        """
        self._init = init
        for v in self._vardict:
            inval = sasoptpy.utils.extract_list_value(v, init)
            self._vardict[v].set_init = inval
        for v in self._shadows:
            self._shadows[v].set_init = init

    def set_bounds(self, lb=None, ub=None):
        """
        Sets / updates bounds for the given variable

        Parameters
        ----------
        lb : float, :class:`pandas.Series`, optional
            Lower bound
        ub : float, :class:`pandas.Series`, optional
            Upper bound

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

        """
        if lb is not None:
            self._lb = lb
        if ub is not None:
            self._ub = ub
        for v in self._vardict:
            varlb = sasoptpy.utils.extract_list_value(v, lb)
            if lb is not None:
                self._vardict[v].set_bounds(lb=varlb)
            varub = sasoptpy.utils.extract_list_value(v, ub)
            if ub is not None:
                self._vardict[v].set_bounds(ub=varub)

    def __str__(self):
        """
        Generates a representation string
        """
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
        """
        Returns a string representation of the object.
        """
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
    """
    Creates a group of :class:`Constraint` objects

    Parameters
    ----------
    argv : Generator-type object
        A Python generator that includes :class:`Expression` objects
    name : string, optional
        Name (prefix) of the constraints

    Examples
    --------

    >>> var_ind = ['a', 'b', 'c', 'd']
    >>> u = so.VariableGroup(var_ind, name='u')
    >>> t = so.Variable(name='t')
    >>> cg = so.ConstraintGroup((u[i] + 2 * t <= 5 for i in var_ind), name='cg')
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

    """

    def __init__(self, argv, name):
        self._condict = OrderedDict()
        self._conlist = []
        if type(argv) == list or type(argv) == GeneratorType:
            self._recursive_add_cons(argv, name=name, condict=self._condict,
                                     conlist=self._conlist)
        if name is not None:
            name = sasoptpy.utils.check_name(name, 'con')
            self._name = name
            self._objorder = sasoptpy.utils.register_name(name, self)
        else:
            self._name = None

    def get_name(self):
            """
            Returns the name of the constraint group

            Returns
            -------
            name : string
                Name of the constraint group

            Examples
            --------

            >>> m = so.Model(name='m')
            >>> x = m.add_variable(name='x')
            >>> indices = ['a', 'b', 'c']
            >>> y = m.add_variables(indices, name='y')
            >>> c1 = m.add_constraints((x + y[i] <= 4 for i in indices),
                                       name='con1')
            >>> print(c1.get_name())
            con1
            """
            return self._name

    def _recursive_add_cons(self, argv, name, condict, conlist, ckeys=()):
        conctr = 0

        if sasoptpy.utils.transfer_allowed:
            argv.gi_frame.f_globals.update(sasoptpy.utils._transfer)

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
            else:
                print('ERROR: Unknown argument type for constraint generation', type(argv))
                return None
            keylist = sasoptpy.utils._to_iterator_expression(newkeys)
            conname = '{}[{}]'.format(name, ','.join(keylist))
            conname = sasoptpy.utils.check_name(conname, 'con')
            newcon = sasoptpy.Constraint(exp=c, name=conname, crange=c._range)
            condict[newkeys] = newcon
            conlist.append(newkeys)
            conctr += 1
        self._set_con_info()

    def get_expressions(self, rhs=False):
        """
        Returns constraints as a list of expressions

        Parameters
        ----------
        rhs : boolean, optional
            Whether to pass the constant part (rhs) of the constraint or not

        Returns
        -------
        df : :class:`pandas.DataFrame`
            Returns a DataFrame consisting of constraints as expressions

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> var_ind = ['a', 'b', 'c', 'd']
        >>> u = m.add_variables(var_ind, name='u')
        >>> t = m.add_variable(name='t')
        >>> cg = so.ConstraintGroup((u[i] + 2 * t <= 5 for i in var_ind),
                                    name='cg')
        >>> ce = cg.get_expressions()
        >>> print(ce)
                     cg
        a  u[a] + 2 * t
        b  u[b] + 2 * t
        c  u[c] + 2 * t
        d  u[d] + 2 * t
        >>> ce_rhs = cg.get_expressions(rhs=True)
        >>> print(ce_rhs)
                         cg
        a  u[a] + 2 * t - 5
        b  u[b] + 2 * t - 5
        c  u[c] + 2 * t - 5
        d  u[d] + 2 * t - 5

        """
        cd = OrderedDict()
        for i in self._condict:
            cd[i] = self._condict[i].copy()
            if rhs is False:
                cd[i]._linCoef['CONST']['val'] = 0
        cd_df = sasoptpy.utils.dict_to_frame(cd, cols=[self._name])
        return cd_df

    def __getitem__(self, key):
        """
        Overloaded method to access individual constraints

        Parameters
        ----------
        key : string or int
            Key of the constraint

        Returns
        -------
        item : Constraint
            Reference to the constraint
        """
        key = sasoptpy.utils.tuple_pack(key)
        return self._condict.__getitem__(key)

    def __iter__(self):
        for i in self._conlist:
            yield self._condict[i]

    def _set_con_info(self):
        for i in self._condict:
            self._condict[i]._set_info(parent=self, key=i)

    def _get_keys(self):
        return list(self._condict)[0]

    def _defn(self, tabs=''):
        s = ''
        for key_ in self._conlist:
            s += tabs + 'con {}'.format(self._name)
            keys = sasoptpy.utils._to_optmodel_loop(key_)
            s += keys
            s += ' : ' + self._condict[key_]._defn()
            s += ';\n'
        return s

    def __str__(self):
        """
        Generates a representation string
        """
        s = 'Constraint Group ({}) [\n'.format(self._name)
        for k in sorted(self._condict):
            v = self._condict[k]
            s += '  [{}: {}]\n'.format(sasoptpy.utils.tuple_unpack(k),
                                       v)
        s += ']'
        return s

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        s = 'sasoptpy.ConstraintGroup(['
        for i in self._condict:
            s += '{}, '.format(str(self._condict[i]))
        s += '], '
        s += 'name=\'{}\')'.format(self._name)
        return s
