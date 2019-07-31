from .statement_base import Statement

import sasoptpy


class CreateDataStatement(Statement):

    def __init__(self):
        super().__init__()

    def append(self, element):
        pass

    def _defn(self):
        pass
