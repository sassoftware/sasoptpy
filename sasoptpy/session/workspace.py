
import warnings

import sasoptpy
from sasoptpy.abstract.util import (
    is_solve_statement, is_print_statement, is_create_data_statement)

class Workspace:
    """
    Workspace represents an OPTMODEL block that allows multiple solves

    Parameters
    ----------
    name : string
        Name of the workspace
    session : :class:`saspy.SASsession` or :class:`swat.cas.connection.CAS`, optional
        Session to be submitted
    """

    def __init__(self, name, session=None):
        self.name = name
        self._load_workspace_defaults()
        self._session = session
        self.response = None
        self._primalSolution = None
        self._dualSolution = None
        self.active_model = '_start_'

    def _load_workspace_defaults(self):
        self._elements = []

    def get_elements(self):
        """
        Returns a list of elements in the workspace
        """
        return self._elements

    def set_active_model(self, model):
        """
        Marks the specified model as active; to be used in solve statements

        Parameters
        ----------
        model : :class:`Model`
            Model to be activated
        """
        self.active_model = model

    def __str__(self):
        return 'Workspace[ID={}]'.format(id(self))

    def __repr__(self):
        return 'sasoptpy.Workspace({})'.format(self.name)

    def __enter__(self):
        sasoptpy.lock.acquire()
        self.original = sasoptpy.container
        sasoptpy.container = self
        return self

    def __exit__(self, type, value, traceback):
        sasoptpy.container = self.original
        sasoptpy.lock.release()

    def append(self, element):
        """
        Appends a new element (operation or statement) to the workspace

        Parameters
        ----------
        element : :class:`sasoptpy.abstract.Statement`
            Any statement that can be appended
        """
        self._elements.append(element)

    def set_session(self, session):
        self._session = session

    def get_session(self):
        return self._session

    def submit(self, **kwargs):
        """
        Submits the workspace as an OPTMODEL block and returns solutions
        """
        return sasoptpy.util.submit(self, **kwargs)

    def parse_solve_responses(self):
        """
        Retrieves the solutions to all solve statements
        """
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
            elif isinstance(solve, sasoptpy.abstract.Statement):
                solve.set_response(ss)

    def parse_print_responses(self):
        """
        Retrieves responses to all print statements
        """
        keys = self.response.keys()
        print_statements = [i for i in self.get_elements() if
                            is_print_statement(i)]

        for i, p in enumerate(print_statements):
            pp_key = 'Print{}.PrintTable'.format(i+1)
            if pp_key in keys:
                if isinstance(p, sasoptpy.abstract.Statement):
                    p.set_response(self.response[pp_key])

    def parse_create_data_responses(self, mediator):
        """
        Grabs responses to all print statements
        """
        keys = self.response.keys()
        cd_statements = [i for i in self.get_elements() if
                            is_create_data_statement(i)]
        session = self._session

        for i, c in enumerate(cd_statements):
            table = c.get_table_expr()
            try:
                tabledf = mediator.parse_table(table)
                c.set_response(tabledf)
            except:
                continue

    def get_variable(self, name):
        """
        Obtains the value of a specified variable name

        Parameters
        ----------
        name : string
            Name of the variable
        """
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
        """
        Specifies the value of a variable

        Parameters
        ----------
        name : string
            Name of the variable
        value : float
            New value of the variable
        """
        variable = self.get_variable(name)
        if variable is not None:
            variable.set_value(value)

    def to_optmodel(self):
        """
        Returns equivalent OPTMODEL code of the workspace

        Returns
        -------
        optmodel : string
            Generated OPTMODEL code of the workspace object

        """
        return sasoptpy.to_optmodel(self)
