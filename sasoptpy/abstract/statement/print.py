from .statement_base import Statement

import sasoptpy


class PrintStatement(Statement):

    def __init__(self, *args):
        super().__init__()
        for arg in args:
            self.elements.append(arg)
        self._print_type = 'print'
        self._print_names = False

    def append(self, arg):
        self.elements.append(arg)

    def set_print_type(self, print_type):
        self._print_type = print_type

    def allow_print_names(self):
        self._print_names = True

    def _defn(self):
        keyword = f'{self._print_type}'
        items = []
        for i in self.elements:
            word = sasoptpy.to_expression(i)
            if self._print_names:
                word += '='
            items.append(word)
        return keyword + ' ' + ' '.join(items) + ';'

    @classmethod
    def print_item(cls, *args):
        ps = PrintStatement(*args)
        return ps

    @classmethod
    def put_item(cls, *args, names=False):
        ps = PrintStatement(*args)
        ps.set_print_type('put')
        if names:
            ps.allow_print_names()
        return ps
