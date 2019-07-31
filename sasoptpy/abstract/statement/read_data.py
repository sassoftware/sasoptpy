from .statement_base import Statement

import sasoptpy


class ReadDataStatement(Statement):

    def __init__(self, index=None, params=None):
        super().__init__()
        self._index = index
        self._params = params

    def append(self, element):
        pass
        #self._params.append(element)

    def set_index(self, index):
        self._index = index

    def append_parameter(self, element):
        self._params.append(element)

    def _defn(self):
        pass
