from .statement_base import Statement
from .literal import LiteralStatement

import sasoptpy


class NestedConditions(Statement):

    def __init__(self):
        super().__init__()

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        eldefs = []
        for i in self.elements:
            eldefs.append(sasoptpy.to_definition(i))
        return '\n'.join(eldefs)


class IfElseStatement(NestedConditions):

    def __init__(self, logic_expression, if_statement, else_statement=None):
        super().__init__()
        original_container = sasoptpy.container
        c = Case('if', logic_expression)
        sasoptpy.container = c
        if_statement()
        self.append(c)
        if else_statement is not None:
            c = Case('else')
            sasoptpy.container = c
            else_statement()
            self.append(c)
        sasoptpy.container = original_container

    @classmethod
    def if_condition(cls, logic_expression, if_statement, else_statement=None):
        if_else_statement = IfElseStatement(logic_expression, if_statement, else_statement)
        return if_else_statement


class SwitchStatement(NestedConditions):

    def __init__(self, *args):
        super().__init__()
        original_container = sasoptpy.container
        condition = None
        for i in args:
            if sasoptpy.core.util.is_constraint(i):
                condition = i
            elif isinstance(i, sasoptpy.abstract.Condition):
                condition = i
            elif callable(i):
                key = self.get_next_key(condition)
                c = Case(keyword=key, condition=condition)
                sasoptpy.container = c
                i()
                self.append(c)
                condition = None
        sasoptpy.container = original_container

    def get_next_key(self, condition):
        if len(self.elements) == 0:
            return 'if'
        else:
            if sasoptpy.core.util.is_constraint(condition):
                return 'else if'
            elif isinstance(condition, sasoptpy.abstract.Condition):
                return 'else if'
            else:
                return 'else'

    @classmethod
    def switch_condition(cls, *args):
        sc = SwitchStatement(*args)
        return sc


class Case(Statement):

    def __init__(self, keyword='if', condition=None):
        super().__init__()
        self.keyword = keyword
        self.condition = condition

    def get_do_word(self):
        if self.keyword == 'if' or self.keyword == 'else if':
            return 'then do'
        else:
            return 'do'

    def _defn(self):
        s = self.keyword + ' '
        if self.condition:
            s += self.condition._expr() + ' '
        s += self.get_do_word() + ';\n'
        eldefs = []
        for i in self.elements:
            eldef = sasoptpy.to_definition(i)
            if eldef is not None:
                eldefs.append(eldef)
        s += sasoptpy.util.addSpaces('\n'.join(eldefs), 3) + '\n'
        s += 'end;'
        return s

    def append(self, x):
        self.elements.append(x)
