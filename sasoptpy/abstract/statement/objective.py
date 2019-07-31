from .statement_base import Statement

import sasoptpy


class ObjectiveStatement(Statement):

    def __init__(self, expression, sense, name=None, multiobj=False):
        super().__init__()
        self.model = None
        self.name = name
        self.expr = expression
        self.sense = sense

    def append(self):
        pass

    def _defn(self):
        return '{} {} = {};'.format(self.sense, self.name, self.expr._expr())

    @classmethod
    def set_objective(cls, model, expression, sense=None, name=None, multiobj=False):
        st = ObjectiveStatement(expression, sense, name, multiobj)
        st.model = model
        if sasoptpy.container:
            sasoptpy.container.append(st)
        else:
            model.add_statement(st)