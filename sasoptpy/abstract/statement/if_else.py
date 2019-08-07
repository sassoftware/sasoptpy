from .statement_base import Statement

import sasoptpy


class IfElseStatement(Statement):

    def __init__(self, condition=None, then=None, elsethen=None):
        super().__init__()

    def append(self, element):
        pass

    def _defn(self):
        pass