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

from .statement_base import Statement
import sasoptpy


class Assignment(Statement):

    def __init__(self, identifier, expression, keyword=None):
        super().__init__()
        self.keyword = keyword
        self.identifier = identifier
        self.expression = expression

    def _defn(self):
        s = ''
        if self.keyword:
            s += self.keyword + ' '
        s += '{} = {};'.format(sasoptpy.to_expression(self.identifier),
                               sasoptpy.to_expression(self.expression))
        return s

    def append(self, *args, **kwargs):
        if kwargs.get('identifier'):
            self.identifier = kwargs.get('identifier')
        if kwargs.get('expression'):
            self.expression = kwargs.get('expression')
        if kwargs.get('keyword'):
            self.keyword = kwargs.get('keyword')

    @classmethod
    def set_bounds(cls, var, **kwargs):
        statements = []
        lb = kwargs.get('lb')
        ub = kwargs.get('ub')
        if lb and ub and lb is ub:
            from sasoptpy.abstract.statement import FixStatement
            statements.append(FixStatement((var, lb)))
        elif lb and ub:
            lb_identifier = sasoptpy.Symbol
            statements.append(Assignment(identifier=var.lb, expression=lb))
            statements.append(Assignment(identifier=var.ub, expression=ub))
        elif lb:
            statements.append(Assignment(identifier=var.lb, expression=lb))
        elif ub:
            statements.append(Assignment(identifier=var.ub, expression=ub))

        return statements

    @classmethod
    def set_value(cls, obj, value):
        st = Assignment(identifier=obj, expression=value)
        return st

    @classmethod
    def fix_value(cls, obj, value):
        st = Assignment(identifier=obj, expression=value, keyword='fix')
        return st
