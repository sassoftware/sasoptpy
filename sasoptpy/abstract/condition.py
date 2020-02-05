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
        left = self._left._cond_expr() if hasattr(self._left, '_cond_expr') \
            else sasoptpy.to_expression(self._left)

        right = self._right._cond_expr() if hasattr(self._right, '_cond_expr') \
            else sasoptpy.to_expression(self._right)

        if self._type in ['and', 'or', 'AND', 'OR']:
            left = '({})'.format(left)
            right = '({})'.format(right)

        return '{} {} {}'.format(left, self._type, right)

    def _cond_expr(self):
        return self._expr()

    def set_left(self, left):
        self._left = left

    def __and__(self, other):
        r = Condition(left=self, c_type='and', right=other)
        return r

    def __or__(self, other):
        r = Condition(left=self, c_type='or', right=other)
        return r

    def copy(self):
        return Condition(self._left, self._type, self._right)


class Conditional:

    def __init__(self, parent, format=None):
        self._parent = parent
        self._conditions = []

    def under_condition(self, condition):
        self.add_condition(condition)
        return True

    def add_condition(self, condition):
        if sasoptpy.core.util.is_constraint(condition):
            self.add_exp_condition(condition)
        elif isinstance(condition, Condition):
            self._conditions.append(condition)

    def add_exp_condition(self, condition):
        self._conditions.append(condition)

    def add_custom_condition(self, operation, key):
        c = Condition(left=self._parent, c_type=operation, right=key)
        self._conditions.append(c)
        return c

    def get_conditions_len(self):
        return len(self._conditions)

    def get_conditions(self):
        return self._conditions

    def get_conditions_str(self):
        keyword_list = [' and ', ' or ']
        conds = [sasoptpy.util.to_condition_expression(c) for c in self._conditions]
        if len(conds) > 0:
            for i, c in enumerate(conds):
                if any(keyword in c for keyword in keyword_list):
                    conds[i] = '(' + c + ')'
            return ' and '.join(conds)
        else:
            return ''

    def copy_conditions(self, other):
        for i in other.get_conditions():
            con_copy = i.copy()
            con_copy.set_left(self._parent)
            self._conditions.append(con_copy)

    def is_in(self, set):
        c = self.add_custom_condition('IN', set)
        return c

    def __eq__(self, key):
        c = self.add_custom_condition('EQ', key)
        return c

    def __le__(self, key):
        c = self.add_custom_condition('<=', key)
        return c

    def __lt__(self, key):
        c = self.add_custom_condition('<', key)
        return c

    def __ge__(self, key):
        c = self.add_custom_condition('>=', key)
        return c

    def __gt__(self, key):
        c = self.add_custom_condition('>', key)
        return c

    def __ne__(self, key):
        c = self.add_custom_condition('NE', key)
        return c
