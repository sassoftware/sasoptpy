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
from math import inf

import sasoptpy
from sasoptpy.core import Expression


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
        When set to `True`, indicates that the variable is abstract

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

    @sasoptpy.class_containable
    def __init__(self, name, vartype=None, lb=None, ub=None,
                 init=None, abstract=False, key=None, **kwargs):
        super().__init__(name=name)
        if vartype is None:
            vartype = sasoptpy.CONT
        self._type = vartype

        self._lb, self._ub = sasoptpy.core.util.get_default_bounds_if_none(
            vartype, lb, ub)

        self._init = init
        if self._init is not None:
            self._value = self._init

        self._key = key
        self._parent = None
        self._temp = False
        self._abstract = abstract

        self._shadow = False
        self.sol = sasoptpy.core.Auxiliary(self, suffix='sol')
        self._initialize_self_coef()

    def _initialize_self_coef(self):
        self.set_member(key=self._name, ref=self, val=1)

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    def get_parent_reference(self):
        return self._parent, self._key

    @sasoptpy.containable
    def set_bounds(self, *, lb=None, ub=None):
        """
        Changes bounds on a variable

        Parameters
        ----------
        lb : float or :class:`Expression`
            Lower bound of the variable
        ub : float or :class:`Expression`
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

    def get_attributes(self):
        """
        Returns an ordered dictionary of main attributes

        Returns
        --------
        attributes : OrderedDict
            Dictionary consists of `init`, `lb`, and `ub` attributes

        """
        attributes = OrderedDict()
        attributes['init'] = self._init
        attributes['lb'] = self._lb
        attributes['ub'] = self._ub
        return attributes

    def get_name(self):
        if self._abstract or self._shadow:
            return str(self)
        else:
            return self._name

    @property
    def ub(self):
        """
        Upper bound of the variable
        """
        return sasoptpy.Auxiliary(self, suffix='ub', value=self._ub)

    @property
    def lb(self):
        """
        Lower bound of the variable
        """
        return sasoptpy.Auxiliary(self, suffix='lb', value=self._lb)

    def get_value(self):
        """
        Returns the value of the variable

        Returns
        -------
        value : float
            Value of the variable

        Examples
        --------

        >>> x.set_value(20)
        >>> x.get_value()
        20

        """
        if self._abstract:
            raise ValueError('Abstract variable cannot have a value.')
        return self._value

    @sasoptpy.containable
    def set_value(self, value):
        """
        Sets the value of a variable
        """
        self._value = value

    def set_parent(self, parent):
        self._parent = parent

    def get_type(self):
        """
        Returns the type of variable

        Valid values are:

        * `sasoptpy.CONT`
        * `sasoptpy.INT`
        * `sasoptpy.BIN`

        """
        return self._type

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        st = 'sasoptpy.Variable(name=\'{}\''.format(self.get_name())
        if self._lb != -inf:
            st += ', lb={}'.format(self._lb)
        if self._ub != inf:
            st += ', ub={}'.format(self._ub)
        if self._init is not None:
            st += ', init={}'.format(self._init)
        if self._abstract:
            st += ', abstract=True'
        st += ', vartype=\'{}\')'.format(self._type)
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
        return '{}'.format(self._name)

    def _expr(self):
        if self._parent is not None and self._key is not None:
            keylist = sasoptpy.core.util._to_iterator_expression(self._key)
            key = ', '.join(keylist)
            return ('{}[{}]'.format(self._parent._name, key))
        if self._shadow and self._iterkey:
            keylist = sasoptpy.core.util.package_utils._to_iterator_expression(self._iterkey)
            key = ', '.join(keylist)
            return('{}[{}]'.format(self._name, key))
        return '{}'.format(self._name)

    def _defn(self):
        s = 'var {}'.format(self._name)
        BIN = sasoptpy.BIN
        CONT = sasoptpy.CONT
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

    def _cond_expr(self):
        return self._expr() + '.sol'
