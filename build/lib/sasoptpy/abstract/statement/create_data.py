#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from .statement_base import Statement
import sasoptpy


class CreateDataStatement(Statement):

    def __init__(self, table, index, columns=None):
        super().__init__()
        self._table = table
        self._index = index
        if isinstance(index, list):
            self._index = {'key': index}
        self._columns = list()
        if columns:
            for col in columns:
                self.append(col)

    def append(self, element, **kwargs):
        if isinstance(element, dict):
            self._columns.append(element)
        else:
            self._columns.append({'expression': element})

    def get_table_expr(self):
        if hasattr(self._table, '_expr'):
            return f'({self._table._expr()})'
        elif hasattr(self._table, 'name'):
            return self._table.name
        else:
            return str(self._table)

    def get_table_name(self):
        return self._table

    def get_index_expr(self):
        s = ''
        key = self._index.get('key')
        if isinstance(key, str):
            key = [key]
        index = self._index.get('set')
        if key:
            joined_key = ' '.join([k.get_name() if hasattr(k, 'get_name') else str(k) for k in key])
            s += '[{}]'.format(joined_key)
        if key and index:
            s += ' = '
        if index:
            s += '{' + sasoptpy.util.package_utils._to_sas_string(index) + '}'
        return s

    def get_columns_expr(self):
        cols = self._columns
        columns_string = [CreateDataStatement.get_column_str(c) for c in cols]
        s = ' '.join(columns_string)
        return s

    @classmethod
    def get_column_str(cls, c):
        name = c.get('name')
        expr = c.get('expression', c.get('expr'))
        index = c.get('index')
        if not isinstance(index, list):
            index = [index]
        name_str = ''
        connect_str = ''
        expr_str = ''
        if name:
            if hasattr(name, '_expr'):
                name_str = 'col(' + name._expr() + ')'
            else:
                name_str = str(name)
        if name and expr:
            connect_str += '='
        if expr:
            if sasoptpy.util.has_expr(expr):
                expr_str += expr._expr()
            else:
                expr_str += '{}'.format(expr)

        if name_str == expr_str:
            connect_str = ''
            expr_str = ''

        if name_str != '':
            expr_str = '({})'.format(expr_str)

        s = name_str + connect_str + expr_str

        if index and any(sasoptpy.abstract.util.is_key_abstract(i) for i in index):
            index_str = ', '.join([sasoptpy.to_definition(i) for i in index])
            s = '{{{}}} < {} >'.format(index_str, s)

        return s

    def _defn(self):
        s = 'create data'
        table_str = self.get_table_expr()
        index_str = self.get_index_expr()
        column_str = self.get_columns_expr()

        s += ' ' + table_str + ' from '
        if index_str != '':
            s += index_str + ' '
        if column_str != '':
            s += column_str
        s += ';'
        return s

    @classmethod
    def create_data(cls, *args, **kwargs):
        c = CreateDataStatement(*args, **kwargs)
        return c
