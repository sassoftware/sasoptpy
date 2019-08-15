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
Set includes :class:`Set` class and implementations for server-side data
operations

"""

import sasoptpy


class ParameterValue(sasoptpy.Expression):
    """
    Represents a single value of a parameter

    Parameters
    ----------
    param : Parameter
        Parameter that the value belongs to
    key : tuple, optional
        Key of the parameter value in the multi-index parameter
    prefix : string
        Prefix of the parameter
    suffix : string
        Suffix of the parameter, such as ``.lb`` and ``.ub``

    Notes
    -----

    - Parameter values are mainly used in abstract expressions
    """

    def __init__(self, param, key=None, prefix='', suffix=''):
        super().__init__()
        self._name = param.get_name()
        tkey = sasoptpy.util.pack_to_tuple(key)
        self._key = tkey
        self._abstract = True
        self._prefix = prefix
        self._suffix = suffix
        self._linCoef[str(self)] = {'ref': self,
                                    'val': 1.0}
        self._ref = param
        self._assign = None
        self._value = 0

    def set_init(self, val):
        """
        Sets the initial value of the parameter

        Parameters
        ----------
        val : Expression
            Initial value

        Examples
        --------

        >>> p = so.Parameter(name='p')
        >>> print(p._defn())
        num p;
        >>> p.set_init(10)
        >>> print(p._defn())
        num p = 10;

        Notes
        -----
        - This method is only available for parameters without index/key.

        """
        if self._key == ('',):
            self._ref.set_init(val)

    def _tag_constraint(self, *argv):
        pass

    def __repr__(self):
        st = 'sasoptpy.ParameterValue(name=\'{}\', key=[{}])'.format(
            self._name, str(self._key))
        return st

    def __str__(self):
        if len(self._key) == 1:
            if isinstance(self._key[0], str):
                if self._key[0] == '':
                    return self._prefix +\
                           self._name +\
                           self._suffix
        return self._prefix +\
            sasoptpy.util._insert_brackets(self._name, self._key) +\
            self._suffix

    def _expr(self):
        return str(self)

    def get_value(self):
        if self._key == ('',):
            return self._ref.get_value()
        else:
            return None

    @sasoptpy.containable
    def set_value(self, value):
        self._value = value








class OldStatement:

    def __init__(self, statement, after_solve=False):
        self.statement = statement
        self._objorder = sasoptpy.util.get_creation_id()
        self._name = sasoptpy.util.get_next_name()
        self._after = after_solve

    def _defn(self):
        return self.statement
