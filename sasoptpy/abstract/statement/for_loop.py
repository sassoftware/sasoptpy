
from contextlib import contextmanager

from .statement_base import Statement

import sasoptpy


class ForLoopStatement(Statement):

    def __init__(self, *args):
        super().__init__()
        self._sets = list(args)

    @classmethod
    def for_loop(cls, *args):
        loop = ForLoopStatement(*args)
        return loop

    def __iter__(self):
        iterators = []
        for i in self._sets:
            j = sasoptpy.abstract.SetIterator(i)
            iterators.append(j)
        self.iterators = iterators
        self.original = sasoptpy.container

        sasoptpy.container = self
        if len(self.iterators) == 1:
            yield self.iterators[0]
        else:
            yield iter(self.iterators)
        sasoptpy.container = self.original

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        s = 'for '
        s += '{'
        loops = []
        for i, it in enumerate(self.iterators):
            loops.append('{} in {}'.format(
                it._expr(), self._sets[i]._expr()
            ))
        s += ', '.join(loops)
        s += '} do;\n'

        eldefs = []
        for i in self.elements:
            eldef = sasoptpy.to_definition(i)
            if eldef is not None:
                eldefs.append(eldef)
        s += sasoptpy.util.addSpaces('\n'.join(eldefs), 4) + '\n'

        s += 'end;'
        return s





    # def __init__(self, func=None, over_set=None):
    #     super().__init__()
    #     self.func = func
    #     self.over_set = over_set
    #     if sasoptpy.abstract.is_abstract_set(self.over_set):
    #         self.variable = sasoptpy.abstract.SetIterator(self.over_set)
    #     self.conditions = None
    #
    # def append(self, element):
    #     self.elements.append(element)
    #
    # def _defn(self):
    #
    #     s = ''
    #     s += 'for {{{} in {}'.format(self.variable, self.over_set)
    #     if self.conditions:
    #         s += ': '
    #         for i in self.conditions:
    #             s += i._expr()
    #     s += '} do;\n'
    #
    #     # if self.variable and self.actual_variable._name != self.variable._name:
    #     #     s += '    ' + LiteralStatement('{} = {};\n'.format(self.variable, self.actual_variable))._expr()
    #
    #     for el in self.elements:
    #         s += '    ' + el._defn() + '\n'
    #
    #     s += 'end;'
    #
    #     return s
    #
    # def __enter__(self):
    #     self.original = sasoptpy.container
    #     sasoptpy.container = self
    #
    # def __exit__(self, *args):
    #     sasoptpy.container = self.original
    #
    # def __iter__(self):
    #     yield (1,1)
    #
    # @classmethod
    # #@contextmanager
    # def for_loop(cls, *args):
    #     loop = ForLoopStatement()
    #     if sasoptpy.container:
    #         sasoptpy.container.append(loop)
    #     return loop
    #     #original = sasoptpy.container
    #     #sasoptpy.container = loop
    #     #yield
    #     #sasoptpy.container = original
