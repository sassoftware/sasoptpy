from .statement_base import Statement

import sasoptpy


class DropStatement(Statement):

    @sasoptpy.class_containable
    def __init__(self, *elements):
        super().__init__()
        for i in elements:
            self.elements.append(i)

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        s = 'drop '
        cons = []
        for c in self.elements:
            cons.extend(c._get_name_list())
        s += ' '.join(cons) + ';'
        return s

    @classmethod
    def model_drop_constraint(cls, _, c):
        if sasoptpy.core.util.is_droppable(c):
            st = DropStatement(element=c)
            return st

    @classmethod
    def drop_constraint(cls, *constraints):
        if all([sasoptpy.core.util.is_droppable(c) for c in constraints]):
            st = DropStatement(*constraints)
