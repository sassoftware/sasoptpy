# SAS MVA interface for sasoptpy

import sasoptpy
from sasoptpy._libs import np
from sasoptpy.interface import Mediator
from saspy import SASsession
from sasoptpy.interface.util import wrap_long_lines, replace_long_names

import warnings

class SASMediator(Mediator):

    def __init__(self, caller, sas_session):
        self.caller = caller
        self.session = sas_session
        self.conversion = dict()

    def solve(self, **kwargs):
        """
        Solve action for :class:`Model` objects
        """
        mps_indicator = kwargs.get('mps', kwargs.get('frame', False))
        user_options = kwargs.get('options', dict())

        mps_indicator = self.is_mps_format_needed(mps_indicator, user_options)
        if mps_indicator:
            return self.solve_with_mps(**kwargs)
        else:
            return self.solve_with_optmodel(**kwargs)

    def submit(self, **kwargs):
        return self.submit_optmodel_code(**kwargs)

    def is_mps_format_needed(self, mps_option, user_options):
        enforced = False
        session = self.session
        caller = self.caller

        if not isinstance(caller, sasoptpy.Model):
            return False

        model = caller

        if 'decomp' in user_options:
            mps_option = True
            enforced = True

        if mps_option:
            switch = False

            if model.get_sets() or model.get_parameters():
                warnings.warn(
                    'INFO: Model {} has abstract objects, '.format(
                        model.get_name()) + 'switching to OPTMODEL mode.',
                    UserWarning)
                switch = True
            elif not sasoptpy.is_linear(model):
                warnings.warn(
                    'INFO: Model {} include nonlinear components, '.format(
                        model.get_name()) + 'switching to OPTMODEL mode.',
                    UserWarning)
                switch = True

            if switch and mps_option and enforced:
                raise RuntimeError('Cannot run either in OPTMODEL or MPS mode.')
            elif switch:
                mps_option = False

        return mps_option

    def solve_with_mps(self, **kwargs):
        session = self.session
        model = self.caller

        verbose = kwargs.get('verbose', False)
        submit = kwargs.get('submit', True)
        #name = kwargs.get('name', None)
        name = sasoptpy.util.get_next_name()

        # Get the MPS data
        df = model.to_mps(constant=True)

        if verbose:
            print(df.to_string())

        if not submit:
            return df

        # Upload MPS table with new arguments
        try:
            session.df2sd(df=df, table=name, keep_outer_quotes=True)
        except TypeError:
            # If user is using an old version of saspy, apply the hack
            session.df2sd(df=df, table=name)
            session.submit("""
                        data {};
                            set {};
                            field3=tranwrd(field3, "'MARKER'", "MARKER");
                            field3=tranwrd(field3, "MARKER", "'MARKER'");
                            field5=tranwrd(field5, "'INTORG'", "INTORG");
                            field5=tranwrd(field5, "INTORG", "'INTORG'");
                            field5=tranwrd(field5, "'INTEND'", "INTEND");
                            field5=tranwrd(field5, "INTEND", "'INTEND'");
                        run;
                        """.format(name, name))

        # Find problem type and initial values
        ptype = 1  # LP
        for v in model._variables:
            if v._type != sasoptpy.CONT:
                ptype = 2
                break

        if ptype == 1:
            c = session.submit("""
                        ods output SolutionSummary=SOL_SUMMARY ProblemSummary=PROB_SUMMARY;
                        proc optlp data = {}
                           primalout  = solution
                           dualout    = dual;
                        run;
                        """.format(name))
        else:
            c = session.submit("""
                        ods output SolutionSummary=SOL_SUMMARY ProblemSummary=PROB_SUMMARY;
                        proc optmilp data = {}
                           primalout  = solution
                           dualout    = dual;
                        run;
                        """.format(name))

        for line in c['LOG'].split('\n'):
            print(line)
            # if line[0:4] == '    ' or line[0:4] == 'NOTE':
            #     print(line)

        return self.parse_sas_mps_solution()

    def solve_with_optmodel(self, **kwargs):

        model = self.caller
        session = self.session
        verbose = kwargs.get('verbose', False)
        submit = kwargs.get('submit', True)

        print('NOTE: Converting model {} to OPTMODEL.'.format(
            model.get_name()))
        options = kwargs.get('options', dict())
        primalin = kwargs.get('primalin', False)

        optmodel_string = model.to_optmodel(header=True, options=options,
                                           ods=False, primalin=primalin,
                                           parse=True)

        self.conversion = dict()

        # Check if any object has a long name
        limit_names = kwargs.get('limit_names', False)
        if limit_names:
            optmodel_string, conversion = replace_long_names(optmodel_string)
            self.conversion.update(conversion)

        wrap_lines = kwargs.get('wrap_lines', False)
        if wrap_lines:
            max_length = kwargs.get('max_line_length', 3000)
            optmodel_string = wrap_long_lines(optmodel_string, max_length)

        if verbose:
            print(optmodel_string)
        if not submit:
            return optmodel_string

        print('NOTE: Submitting OPTMODEL code to SAS instance.')

        optmodel_string = 'ods output SolutionSummary=SOL_SUMMARY ProblemSummary=PROB_SUMMARY;\n' + \
                          optmodel_string

        response = session.submit(optmodel_string)

        model.response = response

        # Print output
        for line in response['LOG'].split('\n'):
            print(line)
            if 'WARNING 524' in line:
                raise RuntimeError(
                    r'Some object names are truncated, '
                    r'try submitting with limit_names=True parameter')
            elif 'The submitted line exceeds maximum line length' in line:
                raise RuntimeError(
                    r'Some lines exceed maximum line length, '
                    r'try submitting with wrap_lines=True parameter')

        # Parse solution
        return self.parse_sas_solution()

    def parse_sas_mps_solution(self):

        caller = self.caller
        session = self.session
        response = caller.response

        caller._problemSummary = self.parse_sas_table('PROB_SUMMARY')
        caller._solutionSummary = self.parse_sas_table('SOL_SUMMARY')

        solver = caller._solutionSummary.loc['Solver', 'Value']

        # Parse solution
        solution_df = session.sd2df('WORK.solution')
        primalsoln = solution_df[['_VAR_', '_VALUE_', '_LBOUND_', '_UBOUND_']].copy()
        primalsoln.columns = ['var', 'value', 'lb', 'ub']
        if solver == 'LP':
            primalsoln['rc'] = solution_df['_R_COST_']
        caller._primalSolution = primalsoln

        dual_df = session.sd2df('WORK.dual')
        dualsoln = dual_df[['_ROW_', '_ACTIVITY_']].copy()
        dualsoln.columns = ['con', 'value']
        if solver == 'LP':
            dualsoln['dual'] = dual_df['_VALUE_']
        caller._dualSolution = dualsoln

        caller._status = caller._solutionSummary.loc['Solution Status'].Value
        caller._soltime = float(
            caller._solutionSummary.loc['Solution Time'].Value)

        self.perform_postsolve_operations()
        return caller._primalSolution

    def parse_sas_solution(self):

        caller = self.caller
        session = self.session

        # Parse solution
        caller._primalSolution = session.sd2df('WORK.SOLUTION')
        self.convert_to_original(caller._primalSolution)
        caller._dualSolution = session.sd2df('WORK.DUAL')
        self.convert_to_original(caller._dualSolution)

        caller._problemSummary = self.parse_sas_table('PROB_SUMMARY')
        caller._solutionSummary = self.parse_sas_table('SOL_SUMMARY')

        caller._status = caller._solutionSummary.loc['Solution Status'].Value
        caller._soltime = float(caller._solutionSummary.loc['Solution Time'].Value)

        self.perform_postsolve_operations()
        return caller._primalSolution

    def parse_sas_table(self, table_name):
        session = self.session

        parsed_df = session.sd2df(table_name)[['Label1', 'cValue1']]
        parsed_df.replace(np.nan, '', inplace=True)
        parsed_df.columns = ['Label', 'Value']
        parsed_df = parsed_df.set_index(['Label'])
        return parsed_df

    def convert_to_original(self, table):
        if len(self.conversion) == 0:
            return

        name_from = []
        name_to = []
        for i in self.conversion:
            name_from.append(r'\b' + i + r'\b')
            name_to.append(self.conversion[i])
        table.replace(name_from, name_to, inplace=True, regex=True)



    def perform_postsolve_operations(self):
        caller = self.caller
        response = caller.response
        solution = caller._primalSolution
        dual = caller._dualSolution

        # Variable values
        solver = caller.get_solution_summary().loc['Solver', 'Value']
        for _, row in solution.iterrows():
            caller.set_variable_value(row['var'], row['value'])
            if solver == 'LP':
                caller.set_dual_value(row['var'], row['rc'])

        # Constraint values (dual) only for LP
        solver = caller.get_solution_summary().loc['Solver', 'Value']
        if solver == 'LP':
            for _, row in dual.iterrows():
                con = caller.get_constraint(row['con'])
                if con is not None:
                    con.set_dual(row['dual'])

        # Objective value
        if sasoptpy.core.util.is_model(caller):
            objval = caller._solutionSummary.loc['Objective Value'].Value
            objval = float(objval)
            caller.set_objective_value(objval)

        # Variable init values
        if sasoptpy.core.util.is_model(caller):
            for v in caller.get_variables():
                v.set_init(v.get_value())

    def submit_optmodel_code(self, **kwargs):

        caller = self.caller
        session = self.session
        optmodel_code = sasoptpy.util.to_optmodel(caller,
                                                  header=False,
                                                  parse=True,
                                                  ods=True)
        verbose = kwargs.get('verbose', None)

        # Check if any object has a long name
        limit_names = kwargs.get('limit_names', False)
        if limit_names:
            optmodel_code = replace_long_names(optmodel_code)

        wrap_lines = kwargs.get('wrap_lines', False)
        if wrap_lines:
            max_length = kwargs.get('max_line_length', 3000)
            optmodel_code = wrap_long_lines(optmodel_code, max_length)

        if verbose:
            print(optmodel_code)

        response = session.runOptmodel(
            optmodel_code
        )

        caller.response = response
        caller.parse_solve_responses()
        caller.parse_print_responses()

        return self.parse_cas_workspace_response()
