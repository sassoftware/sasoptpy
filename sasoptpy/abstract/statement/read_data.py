from .statement_base import Statement

import sasoptpy


import sasoptpy

class ReadDataStatement(Statement):

    def __init__(self, table, index=None, columns=None):
        super().__init__()
        self._table = table
        self._index = index
        self._columns = columns

    def append(self, element):
        pass

    def set_index(self, index):
        self._index = index

    def append_column(self, element):
        self._columns.append(element)

    def get_table(self):
        return str(self._table)

    def get_index(self):
        index = self._index
        s = '{}'.format(index['target'])
        if index.get('column') is not None:
            s += ' = {}'.format(index['column'])
        return s

    def get_columns(self):
        cols = self._columns
        s = ' '.join(sasoptpy.to_expression(c['column']) for c in cols)
        return s

    def _defn(self):
        s = 'read data '
        s += self.get_table() + ' into '
        s += self.get_index()
        if self._columns is not None:
            s += ' ' + self.get_columns()
        s += ';'
        return s

    @classmethod
    def read_data(cls, *args, **kwargs):
        r = ReadDataStatement(*args, **kwargs)
        if sasoptpy.container:
            sasoptpy.container.append(r)
        return r
