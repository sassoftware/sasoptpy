from .statement_base import Statement

import sasoptpy


class Assignment(Statement):

    def __init__(self, identifier, expression, keyword=None):
        super().__init__()
        self.keyword = keyword
        self.identifier = identifier
        self.expression = expression

    def _defn(self):
        s = ''
        if self.keyword:
            s += self.keyword + ' '
        s += '{} = {};'.format(sasoptpy.to_expression(self.identifier),
                               sasoptpy.to_expression(self.expression))
        return s

    def append(self, arg, **kwargs):
        pass

    @classmethod
    def set_bounds(cls, var, **kwargs):
        statements = []
        lb = kwargs.get('lb')
        ub = kwargs.get('ub')
        if lb and ub and lb is ub:
            statements.append(Assignment(identifier=var, expression=lb,
                                         keyword='fix'))
        elif lb and ub:
            lb_identifier = sasoptpy.Symbol
            statements.append(Assignment(identifier=var.lb, expression=lb))
            statements.append(Assignment(identifier=var.ub, expression=ub))
        elif lb:
            statements.append(Assignment(identifier=var.lb, expression=lb))
        elif ub:
            statements.append(Assignment(identifier=var.ub, expression=ub))

        return statements

    @classmethod
    def set_value(cls, obj, value):
        st = Assignment(identifier=obj, expression=value)
        return st
