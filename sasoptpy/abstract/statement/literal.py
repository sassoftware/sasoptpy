from .statement_base import Statement

import sasoptpy


class LiteralStatement(Statement):

    @sasoptpy.class_containable
    def __init__(self, literal=None):
        super().__init__()
        self.append(literal)

    def append(self, literal):
        self.elements.append(literal)

    def _expr(self):
        expr = '\n'.join(self.elements)
        return expr

    def _defn(self):
        defn = '\n'.join(self.elements)
        return defn

    @classmethod
    def expand(cls):
        LiteralStatement('expand;')
