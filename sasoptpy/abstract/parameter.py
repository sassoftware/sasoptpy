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

import sasoptpy
from sasoptpy.core import Expression
from sasoptpy.util.package_utils import _to_sas_string


class Parameter(Expression):
    """
    Represents a problem input parameter

    Parameters
    ----------
    name : string
        Name of the parameter
    ptype : string, optional
        Type of the parameter. Possible values are `sasoptpy.STR` and
        `sasoptpy.NUM`
    value : float, optional
        Value of the parameter
    init : float, optional
        Initial value of the parameter

    Examples
    --------

    >>> with so.Workspace('w') as w:
    ...     p = so.Parameter(name='p', init=3)
    ...     p.set_value(5)
    ...
    <sasoptpy.abstract.statement.assignment.Assignment object at 0x7f7952e9bb38>
    >>> print(so.to_optmodel(w))
    proc optmodel;
       num p init 3;
       p = 5;
    quit;

    """

    @sasoptpy.class_containable
    def __init__(self, name, ptype=None, value=None, init=None, **kwargs):
        super().__init__(name=name)
        if name is None:
            name = sasoptpy.util.get_next_name()
        if ptype is None:
            if value is not None and isinstance(value, str):
                ptype = sasoptpy.STR
            elif init is not None and isinstance(init, str):
                ptype = sasoptpy.STR
            else:
                ptype = sasoptpy.NUM
        self._type = ptype
        self._fix_value = value
        self._init = init
        self._parent = None
        self._initialize_self_coef()
        self._abstract = True

    def set_parent(self, parent, key):
        self._parent = parent
        self._key = key

    def _initialize_self_coef(self):
        self.set_member(key=self._name, ref=self, val=1)

    def set_init(self, value):
        self._init = value

    @sasoptpy.containable
    def set_value(self, value):
        self._fix_value = value

    def get_value(self):
        return self._fix_value

    def _expr(self):
        if self._parent:
            return self._parent.get_element_name(self._key)
        return self.get_name()

    def _defn(self):
        if self._parent:
            return None
        else:
            s = '{} {}'.format(self._type, self.get_name())
            if self._init:
                #s += ' init {}'.format(_to_python_string(self._init))
                s += ' init {}'.format(_to_sas_string(self._init))
            elif self._fix_value is not None:
                #s += ' = {}'.format(_to_python_string(self._fix_value))
                s += ' = {}'.format(_to_sas_string(self._fix_value))
            s += ';'
            return s

    def __str__(self):
        return self._name


class ParameterValue(Expression):
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

    def __init__(self, param, key=None):
        super().__init__()
        self._param = param
        tkey = sasoptpy.util.pack_to_tuple(key)
        self._key = tkey
        self._abstract = True
        self.set_member(key=str(self), ref=self, val=1)

    def __str__(self):
        return \
            sasoptpy.util.package_utils._insert_brackets(
                self._param.get_name(), self._key)

    def _expr(self):
        return str(self)
