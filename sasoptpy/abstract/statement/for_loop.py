
from contextlib import contextmanager

from .statement_base import Statement

import sasoptpy


class ForLoopStatement(Statement):

    def __init__(self, *args):
        super().__init__()
        self.keyword = 'for'
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
        s = f'{self.keyword} '
        s += '{'
        loops = []
        for i, it in enumerate(self.iterators):
            loops.append('{} in {}'.format(
                sasoptpy.util.package_utils._to_sas_string(it),
                sasoptpy.util.package_utils._to_sas_string(self._sets[i])#._expr()
            ))
        s += ', '.join(loops)
        s += '} do;\n'

        eldefs = []
        for i in self.elements:
            eldef = sasoptpy.to_definition(i)
            if eldef is not None:
                eldefs.append(eldef)
        s += sasoptpy.util.addSpaces('\n'.join(eldefs), 3) + '\n'

        s += 'end;'
        return s
