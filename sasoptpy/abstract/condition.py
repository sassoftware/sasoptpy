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
Condition for symbolic expressions
"""

import sasoptpy

class Condition:

    def __init__(self, left, c_type, right):
        self._left = left
        self._type = c_type
        self._right = right

    def _expr(self):
        if hasattr(self._left, '_cond_expr'):
            left = self._left._cond_expr()
        else:
            left = sasoptpy.to_expression(self._left)

        if hasattr(self._right, '_cond_expr'):
            right = self._right._cond_expr()
        else:
            right = sasoptpy.to_expression(self._right)

        if self._type in ['and', 'or']:
            left = '({})'.format(left)
            right = '({})'.format(right)

        return '{} {} {}'.format(left, self._type, right)

    def _cond_expr(self):
        return self._expr()

    def set_left(self, left):
        self._left = left

    def __bool__(self):
        sasoptpy.conditions.append(self)
        return self

    def __and__(self, other):
        r = Condition(left=self, c_type='and', right=other)
        return r

    def __or__(self, other):
        r = Condition(left=self, c_type='or', right=other)
        return r

    def copy(self):
        return Condition(self._left, self._type, self._right)


class Conditional:

    def __init__(self, parent):
        self._parent = parent
        self._conditions = []

    def add_condition(self, condition):
        if sasoptpy.core.util.is_constraint(condition):
            self.add_exp_condition(condition)
        elif isinstance(condition, Condition):
            self._conditions.append(condition)

    def add_exp_condition(self, condition):
        self._conditions.append(condition)

    def add_custom_condition(self, operation, key):
        c = Condition(left=self._parent, c_type=operation, right=key)
        if not sasoptpy.abstract.util.is_key_abstract(self._parent):
            if sasoptpy.container is not None:
                sasoptpy.container.sym.append(c)
        self._conditions.append(c)

    def get_conditions_len(self):
        return len(self._conditions)

    def get_conditions(self):
        return self._conditions

    def get_conditions_str(self):
        conds = [sasoptpy.util.to_condition_expression(c) for c in self._conditions]
        if len(conds) > 0:
            return ' and '.join(conds)
        else:
            return ''

    def copy_conditions(self, other):
        for i in other.get_conditions():
            con_copy = i.copy()
            con_copy.set_left(self._parent)
            self._conditions.append(con_copy)

    def __contains__(self, key):
        self.add_custom_condition('IN', key)
        return True

    def __eq__(self, key):
        self.add_custom_condition('=', key)
        return True

    def __le__(self, key):
        self.add_custom_condition('<=', key)
        return True

    def __lt__(self, key):
        self.add_custom_condition('<', key)
        return True

    def __ge__(self, key):
        self.add_custom_condition('>=', key)
        return True

    def __gt__(self, key):
        self.add_custom_condition('>', key)
        return True

    def __ne__(self, key):
        self.add_custom_condition('NE', key)
        return True

    def __and__(self, key):
        self.add_custom_condition('AND', key)
        return True

    def __or__(self, key):
        self.add_custom_condition('OR', key)
        return True
