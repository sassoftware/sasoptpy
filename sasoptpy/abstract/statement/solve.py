from .statement_base import Statement

import sasoptpy


class SolveStatement(Statement):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.model = kwargs.get('model', None)
        self.options = kwargs.get('options', dict())
        self.primalin = kwargs.get('primalin', False)
        self._objorder = sasoptpy.util.get_creation_id()
        self._name = sasoptpy.util.get_next_name()
        self._problem_summary = None
        self._solution_summary = None

    def append(self, element):
        pass

    def _defn(self):

        solve_option_keys = (
            'with', 'obj', 'objective', 'noobj', 'noobjective', 'relaxint',
            'primalin')
        s = ''
        if self.model is not None:
            s = 'use problem {};\n'.format(self.model.get_name())
        s += 'solve'
        pre_opts = []
        pos_opts = []

        options = self.options
        primalin = self.primalin

        if primalin:
            options['primalin'] = True

        if options:
            for key, value in options.items():
                if key in solve_option_keys:
                    if key == 'with':
                        pre_opts.append('with ' + options['with'])
                    elif key == 'relaxint' and options[key] is True:
                        pre_opts.append('relaxint')
                    elif key == 'obj' or key == 'objectives':
                        pre_opts.append('obj ({})'.format(
                            ' '.join(i.get_name() for i in options[key])))
                        multi_obj = True
                    elif key == 'primalin' and options[key] is True:
                        pos_opts.append('primalin')
                else:
                    if type(value) is dict:
                        pos_opts.append('{}=('.format(key) + ','.join(
                            '{}={}'.format(i, j)
                            for i, j in value.items()) + ')')
                    else:
                        pos_opts.append('{}={}'.format(key, value))

            if pre_opts:
                s += ' ' + ' '.join(pre_opts)
            if pos_opts:
                s += ' / ' + ' '.join(pos_opts)
        s += ';'
        return s

    def set_response(self, problem_summary, solution_summary):
        self._problem_summary = problem_summary
        self._solution_summary = solution_summary
        self.response = {
            'Problem Summary': self._problem_summary,
            'Solution Summary': self._solution_summary
        }

    def get_problem_summary(self):
        return self._problem_summary

    def get_solution_summary(self):
        return self._solution_summary

    @classmethod
    def solve(cls, *args, **kwargs):
        st = SolveStatement(*args, **kwargs)
        return st

    @classmethod
    def solve_model(cls, model, **kwargs):
        kwargs['model'] = model
        st = SolveStatement(**kwargs)
        return st
