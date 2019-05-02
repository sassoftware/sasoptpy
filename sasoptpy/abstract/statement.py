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

from abc import ABC, abstractmethod
from collections import OrderedDict

import sasoptpy


class Statement(ABC):

    def __init__(self):
        import sasoptpy.util
        self.parent = None
        self.header = OrderedDict()
        self.elements = list()
        self.workspace = dict()
        self._objorder = sasoptpy.util.register_globally(None, self)
        # TODO Remove '_after' after arranging data/structrues py files
        self._after = False

    @abstractmethod
    def _defn(self):
        pass

    def _expr(self):
        pass

    @abstractmethod
    def append(self):
        pass


class LiteralStatement(Statement):

    def __init__(self, literal=None):
        super().__init__()
        self.append(literal)

    def append(self, literal):
        self.elements.append(literal)

    def _expr(self):
        expr = ';\n'.join(self.elements)
        return expr

    def _defn(self):
        defn = ''
        for line in self.elements:
            defn += line + ';\n'
        return defn


class ObjectiveStatement(Statement):

    def __init__(self, expression, sense, name=None, multiobj=False):
        super().__init__()
        self.model = None
        self.name = name
        self.expr = expression
        self.sense = sense

    def append(self):
        pass

    def _defn(self):
        return '{} {} = {};'.format(self.sense, self.name, self.expr._expr())

    @classmethod
    def set_objective(cls, model, expression, sense=None, name=None, multiobj=False):
        st = ObjectiveStatement(expression, sense, name, multiobj)
        st.model = model
        if sasoptpy.container:
            sasoptpy.container.append(st)
        else:
            model.add_statement(st)


class SolveStatement(Statement):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.options = kwargs.get('options', dict())
        self.primalin = kwargs.get('primalin', False)

    def append(self, element):
        pass

    def _defn(self):
        options = self.options
        primalin = self.primalin
        s = ''
        s += 'solve'
        if options.get('with', None):
            s += ' with ' + options['with']
        if options.get('relaxint', False):
            s += ' relaxint'
        if options or primalin:
            primalin_set = False
            optstring = ''
            for key, value in options.items():
                if key not in ('with', 'relaxint', 'primalin'):
                    optstring += ' {}={}'.format(key, value)
                if key is 'primalin':
                    optstring += ' primalin'
                    primalin_set = True
            if primalin and primalin_set is False and options.get('with') is 'milp':
                optstring += ' primalin'
            if optstring:
                s += ' /' + optstring
        s += ';'
        return s


    @classmethod
    def solve(cls, *args, **kwargs):
        st = SolveStatement(*args, **kwargs)
        if sasoptpy.container:
            sasoptpy.container.append(st)
        else:
            model.add_statement(st)


class Assignment(Statement):

    def __init__(self, identifier, expression, keyword=None):
        super().__init__()
        self.keyword = keyword
        self.identifier = identifier
        self.expression = expression

    def _defn(self):
        s = '';
        if self.keyword:
            s += self.keyword + ' '
        s += '{} = {};'.format(self.identifier, self.expression)
        return s

    def append(self, elem):
        self.elements.append(elem)

    @classmethod
    def set_bounds(cls, var, **kwargs):
        statements = []
        lb = kwargs.get('lb')
        ub = kwargs.get('ub')
        if lb and ub and lb == ub:
            statements.append(Assignment(identifier=var, expression=lb, keyword='fix'))
        elif lb and ub:
            statements.append(Assignment(identifier=var._lb, expression=lb))
            statements.append(Assignment(identifier=var._ub, expression=ub))
        elif lb:
            statements.append(Assignment(identifier=var._lb, expression=lb))
        elif ub:
            statements.append(Assignment(identifier=var._ub, expression=ub))

        for st in statements:
            if sasoptpy.container:
                sasoptpy.container.append(st)
            else:
                model.add_statement(st)


    @classmethod
    def set_value(cls, obj, value):
        st = Assignment(identifier=obj, expression=value)
        sasoptpy.container.append(st)


class DropStatement(Statement):

    def __init__(self, constraint):
        super().__init__()
        self.elements.append(constraint)

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        s = ''
        for e in self.elements:
            s += 'drop {};'.format(e._name)
        return s

    @classmethod
    def drop_constraint(cls, _, constraint):
        st = DropStatement(constraint=constraint)
        sasoptpy.container.append(st)


class ReadDataStatement(Statement):

    def __init__(self, index=None, params=None):
        super().__init__()
        self._index = index
        self._params = params

    def append(self, element):
        pass

    def set_index(self, index):
        pass

    def append_parameter(self, element):
        pass

    def _defn(self):
        pass


class CreateDataStatement(Statement):

    def __init__(self):
        super().__init__()

    def append(self, element):
        pass

    def _defn(self):
        pass


class ForLoopStatement(Statement):

    def __init__(self, func=None, variable=None, over_set=None):
        super().__init__()
        self.func = func
        self.variable = variable
        self.actual_variable = None
        self.over_set = over_set
        self.conditions = None
        self._generate_actual_variable()

    def _generate_actual_variable(self):
        import sasoptpy.data
        if isinstance(self.variable, sasoptpy.abstract.ParameterValue):
            self.actual_variable = sasoptpy.abstract.SetIterator(self.over_set)
        else:
            self.actual_variable = self.variable

    def append(self, element):
        self.elements.append(element)

    def _defn(self):

        s = ''
        s += 'for {{{} in {}'.format(self.actual_variable, self.over_set)
        if self.conditions:
            s += ': '
            for i in self.conditions:
                s += i._expr()
        s += '} do;\n'

        if self.actual_variable._name != self.variable._name:
            s += '    ' + LiteralStatement('{} = {};\n'.format(self.variable, self.actual_variable))._expr()

        for el in self.elements:
            s += '    ' + el._defn() + '\n'

        s += 'end;'

        return s


class CoForLoopStatement(ForLoopStatement):

    def __init__(self, loop=None, iterator=None, over=None):
        super().__init__()

    def append(self, element):
        pass

    def _defn(self):
        pass


class IfElseStatement(Statement):

    def __init__(self, condition=None, then=None, elsethen=None):
        super().__init__()

    def append(self, element):
        pass

    def _defn(self):
        pass

