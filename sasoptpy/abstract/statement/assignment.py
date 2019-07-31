from .statement_base import Statement

class Assignment(Statement):

    def __init__(self, identifier, expression, keyword=None):
        super().__init__()
        self.keyword = keyword
        self.identifier = identifier
        self.expression = expression

    def _defn(self):
        s = '';
        if self.keyword:
            s += self.keyword + ' '
        s += '{} = {};'.format(self.identifier, self.expression)
        return s

    def append(self, elem):
        self.elements.append(elem)

    @classmethod
    def set_bounds(cls, var, **kwargs):
        statements = []
        lb = kwargs.get('lb')
        ub = kwargs.get('ub')
        if lb and ub and lb == ub:
            statements.append(Assignment(identifier=var, expression=lb, keyword='fix'))
        elif lb and ub:
            statements.append(Assignment(identifier=var._lb, expression=lb))
            statements.append(Assignment(identifier=var._ub, expression=ub))
        elif lb:
            statements.append(Assignment(identifier=var._lb, expression=lb))
        elif ub:
            statements.append(Assignment(identifier=var._ub, expression=ub))

        for st in statements:
            if sasoptpy.container:
                sasoptpy.container.append(st)
            else:
                model.add_statement(st)


    @classmethod
    def set_value(cls, obj, value):
        st = Assignment(identifier=obj, expression=value)
        sasoptpy.container.append(st)