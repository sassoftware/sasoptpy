from .statement_base import Statement

import sasoptpy


class ObjectiveStatement(Statement):

    def __init__(self, expression, **kwargs):
        super().__init__()
        self.model = None
        self.name = kwargs.get('name')
        self.expr = expression
        self.sense = kwargs.get('sense')

    def append(self):
        pass

    def _defn(self):
        return '{} {} = {};'.format(self.sense, self.name, self.expr._expr())

    @classmethod
    def set_objective_of_model(cls, model, expression, **kwargs):
        st = ObjectiveStatement(expression, **kwargs)
        st.model = model
        return st

    @classmethod
    def set_objective(cls, expression, name, sense):
        st = ObjectiveStatement(expression, name=name, sense=sense)
        return st
