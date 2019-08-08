
from .statement_base import Statement
import sasoptpy


class ReadDataStatement(Statement):

    def __init__(self, table, index=None, columns=None):
        super().__init__()
        self._table = table
        self._index = index
        self._columns = list()
        if columns:
            for col in columns:
                self.append(col)

    def append(self, element, **kwargs):
        self._columns.append(element)

    def get_table_expr(self):
        if hasattr(self._table, 'name'):
            return self._table.name
        else:
            return str(self._table)

    def get_index_expr(self):
        index = self._index
        target = index.get('target')
        key = index.get('key')

        s = ''
        if target:
            s += '{}'.format(index['target'])
        if target and key:
            s += '='
        if key:
            s += '[{}]'.format(
                ReadDataStatement.flatten_column(key))
        return s

    def get_columns_expr(self):
        cols = self._columns
        columns_string = [ReadDataStatement.get_column_str(c) for c in cols]
        s = ' '.join(columns_string)
        return s

    @classmethod
    def flatten_column(cls, col):
        if isinstance(col, list):
            ind = [ReadDataStatement.flatten_column(c) for c in col]
            return ' '.join(ind)
        elif isinstance(col, str):
            return col
        else:
            return str(col)

    @classmethod
    def get_column_str(cls, c):
        target = c.get('target')
        column = c.get('column')
        index = c.get('index')
        s = ''
        if target:
            s += '{}'.format(ReadDataStatement.get_target_expr(target))
        if target and column:
            s += '='
        if column:
            if hasattr(column, '_expr'):
                s += 'col(' + column._expr() + ')'
            else:
                s += '{}'.format(column)

        if index and sasoptpy.abstract.util.is_key_abstract(index):
            s = '{{{}}} < {} >'.format(sasoptpy.to_definition(index), s)

        return s

    @classmethod
    def get_target_expr(cls, target):
        return sasoptpy.to_expression(target)

    def _defn(self):
        s = 'read data '
        s += self.get_table_expr() + ' into '
        s += self.get_index_expr()
        if self._columns is not None:
            s += ' ' + self.get_columns_expr()
        s += ';'
        return s

    @classmethod
    def read_data(cls, *args, **kwargs):
        r = ReadDataStatement(*args, **kwargs)
        return r
