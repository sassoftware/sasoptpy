from .statement_base import Statement

import sasoptpy


class ForLoopStatement(Statement):

    def __init__(self, func=None, over_set=None):
        super().__init__()
        self.func = func
        self.over_set = over_set
        if sasoptpy.abstract.is_abstract_set(self.over_set):
            self.variable = sasoptpy.abstract.SetIterator(self.over_set)
        self.conditions = None

    def append(self, element):
        self.elements.append(element)

    def _defn(self):

        s = ''
        s += 'for {{{} in {}'.format(self.variable, self.over_set)
        if self.conditions:
            s += ': '
            for i in self.conditions:
                s += i._expr()
        s += '} do;\n'

        # if self.variable and self.actual_variable._name != self.variable._name:
        #     s += '    ' + LiteralStatement('{} = {};\n'.format(self.variable, self.actual_variable))._expr()

        for el in self.elements:
            s += '    ' + el._defn() + '\n'

        s += 'end;'

        return s
