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
import warnings

from sasoptpy.libs import np

import sasoptpy


class Expression:
    """
    Creates a mathematical expression to represent model components

    Parameters
    ----------
    exp : :class:`Expression`, optional
        An existing expression where arguments are being passed
    name : string, optional
        A local name for the expression

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

    >>> import sasoptpy.abstract.math as sm
    >>> f = sm.sin(x) + sm.min(y[1],1) ** 2
    >>> print(type(f))
    <class 'sasoptpy.core.Expression'>
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

    def __init__(self, exp=None, name=None):
        self._name = name
        if self._is_named_expression():
            self._objorder = sasoptpy.util.get_creation_id()
        self._value = 0
        self._dual = None
        self._linCoef = OrderedDict()
        if exp is None:
            self.set_member(key='CONST', ref=None, val=0)
        else:
            if isinstance(exp, Expression):
                self._copy_coef(exp)
            elif np.issubdtype(type(exp), np.number):
                self.set_member(key='CONST', ref=None, val=exp)
            else:
                raise TypeError('ERROR: Invalid type for expression: {}, {}'.format(exp, type(exp)))
        self._temp = False
        self._value = 0
        self._operator = None
        self._arguments = []
        self._iterkey = []
        self._abstract = False
        self.sym = sasoptpy.abstract.Conditional(self)
        self._keep = False

    @classmethod
    def to_expression(cls, obj):
        if sasoptpy.core.util.is_expression(obj):
            return obj
        else:
            if np.isinstance(type(obj), np.number):
                r = Expression(name=str(obj))
                r.add_to_member_value('CONST', obj)
                return r
            else:
                raise RuntimeError(
                    'Cannot convert type {} to Expression'.format(type(obj)))

    def copy(self, name=None):
        """
        Returns a copy of the :class:`Expression` object

        Parameters
        ----------
        name : string, optional
            Name for the copy

        Returns
        -------
        r : :class:`Expression`
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
            r.copy_member(mylc, self)
        r._operator = self._operator
        r._iterkey = self._iterkey
        r._abstract = self._abstract
        r.sym.copy_conditions(self.sym)
        return r

    def _copy_coef(self, exp):
        for mylc in exp.get_member_dict():
            self.copy_member(mylc, exp)

    def _is_named_expression(self):
        return self._name is not None

    def get_member_dict(self):
        """
        Returns an ordered dictionary of elements
        """
        return self._linCoef

    def get_member(self, key):
        """
        Returns the requested member of the expression

        Parameters
        ----------
        key : string
            Identifier of the member, name for single objects

        Returns
        -------
        member : dict
            A dictionary of coefficient, operator, and reference of member
        """
        return self._linCoef.get(key, None)

    def set_member(self, key, ref, val, op=None):
        """
        Adds a new member or changes an existing member

        Parameters
        ----------
        key : string
            Identifier of the new or existing member
        ref : Object
            A reference to the new or existing member
        val : float
            Initial coefficient of the new or existing member
        op : string, optional
            Operator, if member has multiple children
        """
        self._linCoef[key] = {'ref': ref, 'val': val}
        if op:
            self._linCoef[key]['op'] = op

    def delete_member(self, key):
        """
        Deletes the requested member from the core dictionary
        """
        self._linCoef.pop(key, None)

    def copy_member(self, key, exp):
        """
        Copies the member of another expression

        Parameters
        ----------
        key : string
            Identifier of the member
        exp : :class:`Expression`
            Other expression to be copied from

        """
        self._linCoef[key] = dict(exp.get_member(key))

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
        for mylc in self.get_member_dict():
            if self.get_member(mylc)['ref'] is not None:
                if isinstance(mylc, tuple):
                    v += sasoptpy.core.util._evaluate(self.get_member(mylc))
                else:
                    m = self.get_member(mylc)
                    v += m['val'] * m['ref'].get_value()
            else:
                v += self.get_member(mylc)['val']
        if self._operator:
            try:
                import sasoptpy.abstract.math as sm
                if self._arguments:
                    vals = [i.get_value() if isinstance(i, Expression) else i for i in self._arguments]
                    v = sm.func_equivalent[self._operator](v, *vals)
                else:
                    v = sm.func_equivalent[self._operator](v)
            except KeyError:
                warnings.warn(
                    'Cannot evaluate operator: {} in {}'.format(
                        self._operator, self._expr()), RuntimeWarning)
        return v

    def get_member_value(self, key):
        """
        Returns coefficient of requested member

        Parameters
        ----------
        key : string
            Identifier of the member

        Returns
        -------
        value : float
            Coefficient value of the requested member
        """
        member = self.get_member(key)
        return member['val']

    def set_member_value(self, key, value):
        """
        Changes the coefficient of the requested member

        Parameters
        ----------
        key : string
            Identifier of the member
        value : float
            New coefficient value of the member
        """
        member = self.get_member(key)
        member['val'] = value

    def add_to_member_value(self, key, value):
        """
        Adds `value` to the coefficient of the requested member

        Parameters
        ----------
        key : string
            Identifier of the member
        value : float
            Value to be added
        """
        member = self.get_member(key)
        member['val'] += value

    def mult_member_value(self, key, value):
        """
        Multiplies the coefficient of the requested member by the specified
        `value`

        Parameters
        ----------
        key : string
            Identifier of the member
        value : float
            Value to be multiplied with
        """
        member = self.get_member(key)
        member['val'] *= value

    def get_dual(self):
        """
        Returns the dual value

        Returns
        -------
        dual : float
            Dual value of the object

        """
        return self._dual

    def set_dual(self, value):
        self._dual = value

    def set_name(self, name=None):
        """
        Specifies the name of the expression

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
        if name:
            self._name = name
        else:
            self._name = 'o' + str(self._objorder)
        return self._name

    def get_name(self):
        """
        Returns the name of the object

        Returns
        -------
        name : string
            Name of the object

        Examples
        --------

        >>> m = so.Model()
        >>> var1 = m.add_variables(name='x')
        >>> print(var1.get_name())
        x
        """
        return self._name

    def get_name_with_keys(self, name=None):
        if name is None:
            name = self.get_name()

        if sasoptpy.core.util.is_key_empty(self._iterkey):
            return name
        else:
            return '{}{}'.format(
                name,
                sasoptpy.util.package_utils._to_optmodel_loop(self._iterkey))

    def set_temporary(self):
        """
        Converts expression into a temporary expression to enable in-place operations
        """
        self._temp = True

    def set_permanent(self):
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
        self._temp = False
        if not sasoptpy.util.get_object_order(self):
            self._objorder = sasoptpy.util.get_creation_id()
        if self.get_name() is None:
            self.set_name()

    def get_constant(self):
        """
        Returns the constant term in the expression

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> e = 2 * x + 5
        >>> print(e.get_constant())
        5

        """
        return self.get_member('CONST')['val']

    def _expr_string(self, operator_type='sas'):
        # Add the operator first if exists
        s = ''
        if self._operator:
            s += self._operator
            if operator_type == 'sas':
                if self._iterkey:
                    if self._operator == 'sum':
                        s += sasoptpy.util.package_utils._to_optmodel_loop(
                            self._iterkey, subindex=False) + ' '
            s += '('

        itemcnt = 0
        firstel = True

        # Add every element into string one by one
        for idx, el in self.get_member_dict().items():
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
                if operator_type == 'python':
                    optext = ' {} '.format(sasoptpy.util.get_python_symbol(op))
                else:
                    optext = ' {} '.format(op)
            else:
                optext = ' * '

            # For a list of expressions, a recursive function is called
            if isinstance(ref, list):
                if operator_type == 'python':
                    strlist = sasoptpy.util.package_utils._recursive_walk(
                        ref, func='__str__')
                else:
                    strlist = sasoptpy.util.package_utils._recursive_walk(
                        ref, func='_expr')
            elif sasoptpy.util.has_expr(ref):
                if operator_type == 'python':
                    strlist = [ref.__str__()]
                else:
                    strlist = [ref._expr()]
            else:
                strlist = [str(val)]

            if optext != ' * ' and optext != ' || ':
                strlist = ['({})'.format(stritem)
                           for stritem in strlist]

            # Merge all elements in strlist together
            refs = optext.join(strlist)
            if val == 1 or val == -1:
                if val == -1 and any(special_op in refs for special_op in
                                     sasoptpy.util.get_unsafe_operators()):
                    s += '({}) '.format(refs)
                else:
                    s += '{} '.format(refs)
            else:
                if op or any(special_op in refs for special_op in
                             sasoptpy.util.get_unsafe_operators()):
                    s += '{} * ({}) '.format(
                        sasoptpy.util.get_in_digit_format(abs(val)), refs)
                else:
                    s += '{} * {} '.format(
                        sasoptpy.util.get_in_digit_format(abs(val)), refs)

            itemcnt += 1

        # CONST is always at the end
        if itemcnt == 0 or (self.get_member_value('CONST') != 0 and
                            not sasoptpy.core.util.is_constraint(self)):
            val = self.get_member_value('CONST')
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
            if operator_type == 'python':
                if self._iterkey:
                    forlist = []
                    for i in self._iterkey:
                        key_expr = sasoptpy.core.util.get_key_for_expr(i)
                        if key_expr:
                            forlist.append(key_expr)
                    s += ' '.join(forlist)
            if self._arguments:
                if operator_type == 'sas':
                    s += ', ' + ', '.join(
                        i._expr() if hasattr(i, '_expr') else str(i) for i in
                        self._arguments)
                else:
                    s += ', ' + ', '.join(str(i) for i in self._arguments)
            s = s.rstrip()
            s += ')'
        s = s.rstrip()
        return s

    def _expr(self):
        """
        Generates the OPTMODEL-compatible string representation of the object

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
        return self._expr_string(operator_type='sas')


    def __repr__(self):
        """
        Returns a string representation of the object

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

    def __str__(self):
        """
        Generates a representation string that is Python-compatible

        Examples
        --------

        >>> f = x + y ** 2
        >>> print(str(f))
        x + (y) ** (2)

        """
        try:
            return self._expr_string(operator_type='python')
        except:
            return 'sasoptpy.Expression(id={})'.format(id(self))


    def _add_coef_value(self, var, key, value):
        """
        Changes value of a variable inside the :class:`Expression` object in
        place

        Parameters
        ----------
        var : :class:`Variable`
            Variable object whose value will be changed
        key : string
            Name of the variable object
        value : float
            New value or the addition to the existing value of the variable
        """
        if key in self.get_member_dict():
            self.set_member_value(key, value)
        else:
            self.set_member(key=key, ref=var, val=value)

    def add(self, other, sign=1):
        """
        Combines two expressions and produces a new one

        Parameters
        ----------
        other : float or :class:`Expression`
            Second expression or constant value to be added
        sign : int, optional
            Sign of the addition, 1 or -1

        Returns
        -------
        r : :class:`Expression`
            Reference to the outcome of the operation

        Notes
        -----
        * It is preferable to use regular Python operation, instead of calling
          this method:

          >>> e = x - y
          >>> f = 3 * x + 2 * y
          >>> g = e + f
          >>> print(g)
          4 * x + y

        """
        if self._temp and type(self) is Expression:
            r = self
        else:
            r = self.copy()

        if isinstance(other, Expression):
            r._abstract = self._abstract or other._abstract

            for v in other.get_member_dict():
                if r.get_member(v):
                    r.add_to_member_value(v, sign * other.get_member_value(v))
                else:
                    r.copy_member(v, other)
                    r.mult_member_value(v, sign)

            r.sym.copy_conditions(self.sym)
            r.sym.copy_conditions(other.sym)

        elif np.issubdtype(type(other), np.number):
            r.add_to_member_value('CONST', sign*other)
        else:
            raise TypeError(
                'Type {} for arithmetic operation is not valid.'.format(type(other)))

        return r

    def mult(self, other):
        """
        Multiplies the :class:`Expression` by a scalar value

        Parameters
        ----------
        other : :class:`Expression` or int
            Second expression to be multiplied

        Returns
        -------
        r : :class:`Expression`
            A new :class:`Expression` that represents the multiplication

        Notes
        -----
        * This method is mainly for internal use.
        * It is preferable to use regular Python operation, instead of calling
          this method:

          >>> e = 3 * (x-y)
          >>> f = 3
          >>> g = e*f
          >>> print(g)
          9 * x - 9 * y

        """
        if isinstance(other, Expression):
            r = Expression()
            r._abstract = self._abstract or other._abstract

            sasoptpy.core.util.multiply_coefficients(
                left=self.get_member_dict(),
                right=other.get_member_dict(),
                target=r.get_member_dict())

            r.sym.copy_conditions(self.sym)
            r.sym.copy_conditions(other.sym)

            return r
        elif np.issubdtype(type(other), np.number):
            if other == 0:
                r = Expression()
            else:
                r = self.copy()
                for e in r.get_member_dict():
                    r.mult_member_value(e, other)
            return r
        else:
            raise TypeError('Type for arithmetic operation is not valid.')

    def _relational(self, other, direction_):
        """
        Creates a logical relation between :class:`Expression` objects

        Parameters
        ----------
        other : :class:`Expression`
            Expression on the other side of the relation with respect to self
        direction_ : string
            Direction of the logical relation, either `E`, `L`, or `G`

        Returns
        -------
        generated_constraint : :class:`Constraint`
            Constraint generated as a result of linear relation

        """
        return sasoptpy.core.util.expression_to_constraint(left=self, relation=direction_, right=other)

    def _is_linear(self):
        """
        Checks whether the expression is composed of linear components

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

        # Loop over components
        for val in self.get_member_dict().values():
            if val.get('op', False):
                return False
            if type(val['ref']) is list:
                return False
            if val['ref'] and val['ref']._operator:
                return False
        return True

    def __hash__(self):
        return hash('{}{}'.format(self._name, id(self)))

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.add(other, -1)

    def __mul__(self, other):
        return self.mult(other)

    def __pow__(self, other):
        r = Expression()
        other = Expression.to_expression(other)
        self.set_permanent()
        other.set_permanent()
        key = (self.get_name(), other.get_name(), '^')
        ref = [self, other]
        val = 1
        op = '^'
        r.set_member(key=key, ref=ref, val=val, op=op)
        r._abstract = self._abstract or other._abstract
        return r

    def __rpow__(self, other):
        r = Expression()
        other = Expression.to_expression(other)
        self.set_permanent()
        other.set_permanent()
        key = (other.get_name(), self.get_name(), '^')
        ref = [other, self]
        val = 1
        op = '^'
        r.set_member(key=key, ref=ref, val=val, op=op)
        r._abstract = self._abstract or other._abstract
        return r

    def __radd__(self, other):
        return self.add(other)

    def __rsub__(self, other):
        tmp = self.add(other, -1)
        for v in tmp.get_member_dict():
            tmp.mult_member_value(v, -1)
        return tmp

    def __rmul__(self, other):
        return self.mult(other)

    def __truediv__(self, other):
        if np.issubdtype(type(other), np.number):
            try:
                return self.mult(1/other)
            except ZeroDivisionError:
                warnings.warn('Expression is divided by zero', RuntimeWarning)
                return None
        elif not isinstance(other, Expression):
            raise TypeError('Type for arithmetic operation is not valid.')

        r = Expression()
        other = Expression.to_expression(other)
        self.set_permanent()
        other.set_permanent()
        key = (self.get_name(), other.get_name(), '/')
        ref = [self, other]
        val = 1
        op = '/'
        r.set_member(key=key, ref=ref, val=val, op=op)
        r._abstract = self._abstract or other._abstract
        return r

    def __rtruediv__(self, other):
        r = Expression()
        other = Expression.to_expression(other)
        self.set_permanent()
        other.set_permanent()
        key = (other.get_name(), self.get_name(), '/')
        ref = [other, self]
        val = 1
        op = '/'
        r.set_member(key=key, ref=ref, val=val, op=op)
        r._abstract = self._abstract or other._abstract
        return r

    def concat(self, other):
        r = sasoptpy.Expression()
        key = (id(self), id(other), '||')
        ref = [self, other]
        val = 1
        op = '||'
        r.set_member(key=key, ref=ref, val=val, op=op)
        return r

    def __lt__(self, other):
        return self._relational(other, 'LT')

    def __gt__(self, other):
        return self._relational(other, 'GT')

    def __le__(self, other):
        return self._relational(other, 'L')

    def __ge__(self, other):
        return self._relational(other, 'G')

    def __eq__(self, other):
        return self._relational(other, 'E')

    def __ne__(self, other):
        return self._relational(other, 'NE')

    def __neg__(self):
        return self.mult(-1)

    def __iter__(self):
        return iter([self])


class Auxiliary(Expression):
    """
    Represents an auxiliary expression, often as a symbolic attribute

    Parameters
    ----------
    base : :class:`Expression`
        Original owner of the auxiliary value
    prefix : string, optional
        Prefix of the expression
    suffix : string, optional
        Suffix of the expression
    operator : string, optional
        Wrapping operator
    value : float, optional
        Initial value of the symbolic object

    Notes
    -----
    * Auxiliary objects are for internal use
    """

    def __init__(self, base, prefix=None, suffix=None, operator=None, value=None):
        super().__init__()
        self._base = base
        self._prefix = prefix
        self._suffix = suffix
        self._operator = operator
        self._value = value
        self.set_member(key=self.get_name(), ref=self, val=1)

    def get_prefix_str(self):
        if self._prefix is None:
            return ''
        return self._prefix

    def get_base_str(self):
        if self._base is None:
            return ''
        return sasoptpy.to_expression(self._base)

    def get_suffix_str(self):
        if self._suffix is None:
            return ''
        return self._suffix

    def wrap_operator_str(self, s):
        if self._operator is None:
            return s
        return '{}({})'.format(
            self._operator, s
        )

    def get_name(self):
        return self._expr()

    def _expr(self):
        prefix_str = self.get_prefix_str()
        base_str = self.get_base_str()
        suffix_str = self.get_suffix_str()
        s = prefix_str + base_str
        if suffix_str != '':
            s += '.' + suffix_str
        s = self.wrap_operator_str(s)
        return s


class Symbol(Expression):
    """
    Represents a symbolic string, to be evaluated on server-side

    Parameters
    ----------
    name : string
        String to be symbolized

    Notes
    -----
    * A Symbol object can be used for any values that does not translate to a value
      on client-side, but has meaning on execution. For example, `_N_` is a
      SAS symbol, which can be used in PROC OPTMODEL strings.
    """

    def __init__(self, name):
        super().__init__(name=name)
        self.set_member(key=self._name, ref=self, val=1)

    def _expr(self):
        return self._name

    def _defn(self):
        pass

    def __str__(self):
        return self._name
