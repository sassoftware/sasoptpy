from .statement_base import Statement

import sasoptpy


class SolveStatement(Statement):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.options = kwargs.get('options', dict())
        self.primalin = kwargs.get('primalin', False)
        self._objorder = sasoptpy.util.get_creation_id()
        self._name = sasoptpy.util.get_next_name()

    def append(self, element):
        pass

    def _defn(self):
        options = self.options
        primalin = self.primalin
        s = ''
        s += 'solve'
        if options.get('with', None):
            s += ' with ' + options['with']
        if options.get('relaxint', False):
            s += ' relaxint'
        if options or primalin:
            primalin_set = False
            optstring = ''
            for key, value in options.items():
                if key not in ('with', 'relaxint', 'primalin'):
                    optstring += ' {}={}'.format(key, value)
                if key is 'primalin':
                    optstring += ' primalin'
                    primalin_set = True
            if primalin and primalin_set is False and options.get('with') is 'milp':
                optstring += ' primalin'
            if optstring:
                s += ' /' + optstring
        s += ';'
        return s

    def set_response(self, problem_summary, solution_summary):
        self._problem_summary = problem_summary
        self._solution_summary = solution_summary

    def get_problem_summary(self):
        return self._problem_summary

    def get_solution_summary(self):
        return self._solution_summary

    @classmethod
    def solve(cls, *args, **kwargs):
        st = SolveStatement(*args, **kwargs)
        return st
