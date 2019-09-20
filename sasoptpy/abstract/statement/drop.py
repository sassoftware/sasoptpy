from .statement_base import Statement

import sasoptpy


class DropStatement(Statement):

    def __init__(self, constraint):
        super().__init__()
        self.elements.append(constraint)

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        s = ''
        for e in self.elements:
            s += 'drop {};'.format(e.get_name())
        return s

    @classmethod
    def drop_constraint(cls, _, constraint):
        st = DropStatement(constraint=constraint)
        return st