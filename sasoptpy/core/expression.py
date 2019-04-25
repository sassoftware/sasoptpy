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
from math import copysign

import numpy as np

import sasoptpy
import sasoptpy.util


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
            self._name = sasoptpy.util.assign_name(name, 'expr')
            self._objorder = sasoptpy.util.register_globally(self._name, self)
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
        return v

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
        safe_name = sasoptpy.util.assign_name(name, 'expr')
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
            self._name = sasoptpy.util.assign_name(name, 'expr')
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
                s += '{} * ({}) '.format(sasoptpy.util.get_in_digit_format(abs(val)), refs)
            else:
                s += '{} * {} '.format(sasoptpy.util.get_in_digit_format(abs(val)), refs)

            itemcnt += 1

        # CONST is always at the end
        if itemcnt == 0 or (self._linCoef['CONST']['val'] != 0 and
                            not sasoptpy.core.util.is_constraint(self)):
            val = self._linCoef['CONST']['val']
            csign = copysign(1, val)
            if csign < 0:
                s += '- '
            elif firstel:
                pass
            else:
                s += '+ '
            s += '{} '.format(sasoptpy.util.get_in_digit_format(abs(val)))

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
                s += '{} * ({}) '.format(sasoptpy.utils.get_in_digit_format(abs(val)), refs)
            else:
                s += '{} * {} '.format(sasoptpy.utils.get_in_digit_format(abs(val)), refs)
            itemcnt += 1

        # CONST is always at the end
        from sasoptpy.components import Constraint
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
            s += '{} '.format(sasoptpy.utils.get_in_digit_format(abs(val)))

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
        elif not sasoptpy.core.util.is_variable(self):
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
            generated_constraint = sasoptpy.core.Constraint(exp=r, direction=direction_, crange=0)
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
            generated_constraint = sasoptpy.Constraint(exp=r, direction=direction_,
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
