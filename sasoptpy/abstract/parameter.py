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


class Parameter(Expression):

    @sasoptpy.class_containable
    def __init__(self, name, ptype=None, value=None, init=None, **kwargs):
        super().__init__(name=name)
        if name is None:
            name = sasoptpy.util.get_next_name()
        if ptype is None:
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
                s += ' init {}'.format(self._init)
            elif self._fix_value:
                s += ' = {}'.format(self._fix_value)
            s += ';'
            return s

    def __str__(self):
        return self._name
