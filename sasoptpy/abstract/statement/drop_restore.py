from .statement_base import Statement

import sasoptpy


class DropStatement(Statement):

    @sasoptpy.class_containable
    def __init__(self, *elements):
        super().__init__()
        for i in elements:
            self.elements.append(i)
        self.keyword = 'drop'

    def append(self, element):
        pass

    def _defn(self):
        s = f'{self.keyword} '
        cons = []
        for c in self.elements:
            cons.extend(c._get_name_list())
        s += ' '.join(cons) + ';'
        return s

    @classmethod
    def model_drop_constraint(cls, _, c):
        if sasoptpy.core.util.is_droppable(c):
            st = DropStatement(c)
            return st

    @classmethod
    def drop_constraint(cls, *constraints):
        if all([sasoptpy.core.util.is_droppable(c) for c in constraints]):
            st = DropStatement(*constraints)

class RestoreStatement(DropStatement):

    def __init__(self, *elements):
        super().__init__(*elements)
        self.keyword = 'restore'

    @classmethod
    def restore_constraint(cls, *constraints):
        if all([sasoptpy.core.util.is_droppable(c) for c in constraints]):
            st = RestoreStatement(*constraints)
