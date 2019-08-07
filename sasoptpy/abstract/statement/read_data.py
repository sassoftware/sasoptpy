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
        if hasattr(self._table, 'name'):
            return self._table.name
        else:
            return str(self._table)

    def get_index(self):
        index = self._index
        s = '{}'.format(index['target'])
        if index.get('column') is not None:
            s += '=[{}]'.format(index['column'])
        return s

    def get_columns(self):
        cols = self._columns
        columns_string = [ReadDataStatement.get_column(c) for c in cols]
        s = ' '.join(columns_string)
        return s

    @classmethod
    def get_column(cls, c):
        target = c.get('target')
        column = c.get('column')
        s = ''
        if target is not None:
            s += '{}'.format(sasoptpy.to_expression(target))
        if column is not None:
            s += '={}'.format(column)
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
        return r
