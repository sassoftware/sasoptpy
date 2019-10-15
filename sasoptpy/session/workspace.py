
import warnings

import sasoptpy
from sasoptpy.abstract.util import is_solve_statement, is_print_statement

class Workspace:

    def __init__(self, name, session=None):
        self.name = name
        self._load_workspace_defaults()
        self._session = session
        self.response = None
        self._primalSolution = None
        self._dualSolution = None

    def _load_workspace_defaults(self):
        self._elements = []

    def get_elements(self):
        return self._elements

    def __str__(self):
        return 'Workspace[ID={}]'.format(id(self))

    def __repr__(self):
        return 'sasoptpy.Workspace({})'.format(self.name)

    def __enter__(self):
        self.original = sasoptpy.container
        sasoptpy.container = self
        return self

    def __exit__(self, type, value, traceback):
        sasoptpy.container = self.original

    def append(self, element):
        self._elements.append(element)

    def set_session(self, session):
        self._session = session

    def get_session(self):
        return self._session

    def submit(self, **kwargs):
        return sasoptpy.util.submit(self, **kwargs)

    def parse_solve_responses(self):
        keys = self.response.keys()
        solve_statements = [i for i in self.get_elements() if
                            is_solve_statement(i)]

        for i, solve in enumerate(solve_statements):
            ps_key = 'Solve{}.ProblemSummary'.format(i+1)
            ss_key = 'Solve{}.SolutionSummary'.format(i+1)
            ps = None
            ss = None
            if ps_key in keys:
                ps = sasoptpy.interface.parse_optmodel_table(
                    self.response[ps_key])
            if ss_key in keys:
                ss = sasoptpy.interface.parse_optmodel_table(
                    self.response[ss_key])
            if isinstance(solve, sasoptpy.abstract.SolveStatement):
                solve.set_response(problem_summary=ps, solution_summary=ss)

    def parse_print_responses(self):
        keys = self.response.keys()
        print_statements = [i for i in self.get_elements() if
                            is_print_statement(i)]

        for i, p in enumerate(print_statements):
            pp_key = 'Print{}.PrintTable'.format(i+1)
            if pp_key in keys:
                if isinstance(p, sasoptpy.abstract.PrintStatement):
                    p.set_response(self.response[pp_key])

    def get_variable(self, name):
        vars = filter(
            lambda i: isinstance(i, sasoptpy.Variable), self.get_elements())
        variable = list(filter(lambda i: i.get_name() == name, vars))
        if len(variable) > 1:
            warnings.warn('More than one variable has name {}'.format(name),
                          UserWarning)
        if len(variable) >= 1:
            return variable[0]

        vg = list(filter(
            lambda i: isinstance(i, sasoptpy.VariableGroup) and
                      i.get_name() == name, self.get_elements()))
        if len(vg) > 1:
            warnings.warn(
                'More than one variable group has name {}'.format(name),
                UserWarning)
        if len(vg) >= 1:
            return vg[0]

        if '[' in name:
            group_name = sasoptpy.util.get_group_name(name)
            group = self.get_variable(group_name)
            if group:
                return group.get_member_by_name(name)

        return None

    def set_variable_value(self, name, value):
        variable = self.get_variable(name)
        if variable is not None:
            variable.set_value(value)
