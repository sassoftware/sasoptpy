from .statement_base import Statement

import sasoptpy


class PrintStatement(Statement):

    def __init__(self, *args):
        super().__init__()
        for arg in args:
            self.elements.append(arg)

    def append(self, arg):
        self.elements.append(arg)

    def set_response(self, response):
        self.response = response

    def _defn(self):
        return 'print ' + ' '.join(sasoptpy.to_expression(i) for i in self.elements) + ';'

    @classmethod
    def print_item(cls, *args):
        ps = PrintStatement(*args)
        return ps
