# SAS MVA interface for sasoptpy

import sasoptpy
from sasoptpy._libs import np
from sasoptpy.interface import Mediator
from saspy import SASsession

import warnings

class SASMediator(Mediator):

    def __init__(self, caller, sas_session):
        self.caller = caller
        self.session = sas_session

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
        pass

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
                        ods output SolutionSummary=SOL_SUMMARY;
                        ods output ProblemSummary=PROB_SUMMARY;
                        proc optlp data = {}
                           primalout  = solution
                           dualout    = dual;
                        run;
                        """.format(name))
        else:
            c = session.submit("""
                        ods output SolutionSummary=SOL_SUMMARY;
                        ods output ProblemSummary=PROB_SUMMARY;
                        proc optmilp data = {}
                           primalout  = solution
                           dualout    = dual;
                        run;
                        """.format(name))

        for line in c['LOG'].split('\n'):
            if line[0:4] == '    ' or line[0:4] == 'NOTE':
                if '_____' not in line and '   524' not in line:
                    print(line)

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
        if verbose:
            print(optmodel_string)
        if not submit:
            return optmodel_string
        print('NOTE: Submitting OPTMODEL code to SAS instance.')

        optmodel_string = 'ods output SolutionSummary=SOL_SUMMARY;\n' + \
                          'ods output ProblemSummary=PROB_SUMMARY;\n' + \
                          optmodel_string

        response = session.submit(optmodel_string)

        model.response = response

        # Print output
        for line in response['LOG'].split('\n'):
            if line[0:4] == '    ' or line[0:4] == 'NOTE':
                print(line)

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
        solution_df = session.sd2df('solution')
        primalsoln = solution_df[['_VAR_', '_VALUE_', '_LBOUND_', '_UBOUND_']]
        primalsoln.columns = ['var', 'value', 'lb', 'ub']
        if solver == 'LP':
            primalsoln['rc'] = solution_df['_R_COST_']
        caller._primalSolution = primalsoln

        dual_df = session.sd2df('dual')
        dualsoln = dual_df[['_ROW_', '_ACTIVITY_']]
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
        response = caller.response

        # Parse solution
        caller._primalSolution = session.sd2df('solution')
        caller._dualSolution = session.sd2df('dual')

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

    # def submit(self, **kwargs):
    #     if isinstance(self.session, SASsession) and isinstance(self.caller, sasoptpy.Model):
    #         return self.solve(session=self.session, **kwargs)
    #
    def OLD_solve(self, session, options, submit, name,
                     frame, drop, replace, primalin, verbose):
        """
        Solves the optimization problem on SAS Clients

        Notes
        -----

        - This function should not be called directly. Instead, use :meth:`Model.solve`.

        See also
        --------
        :func:`Model.solve`

        """

        if not name:
            name = 'MPS'

        try:
            import saspy as sp
        except ImportError:
            print('ERROR: saspy cannot be imported.')
            return False

        if not isinstance(session, sp.SASsession):
            print('ERROR: session= argument is not a valid SAS session.')
            return False

        # Will be enabled later when runOptmodel supports blocks
        if 'decomp' in options:
            frame = True

        # Check if OPTMODEL mode is needed
        if frame:
            switch = False
            # Check if model has sets or parameters
            if self._sets or self._parameters:
                print('INFO: Model {} has data on server,'.format(self._name),
                      'switching to OPTMODEL mode.')
                switch = True
            # Check if model is nonlinear (or abstract)
            elif not self._is_linear():
                print('INFO: Model {} includes nonlinear or abstract ',
                      'components, switching to OPTMODEL mode.')
                switch = True
            if switch:
                frame = False

        if frame:  # MPS

            # Get the MPS data
            df = self.to_frame(constant=True)

            # Upload MPS table with new arguments
            try:
                session.df2sd(df, table=name, keep_outer_quotes=True)
            except TypeError:
                # If user is using an old version of saspy, apply the hack
                print(df.to_string())
                session.df2sd(df, table=name)
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
            for v in self._variables:
                if v._type != sasoptpy.CONT:
                    ptype = 2
                    break

            if ptype == 1:
                c = session.submit("""
                ods output SolutionSummary=SOL_SUMMARY;
                ods output ProblemSummary=PROB_SUMMARY;
                proc optlp data = {}
                   primalout  = primal_out
                   dualout    = dual_out;
                run;
                """.format(name))
            else:
                c = session.submit("""
                ods output SolutionSummary=SOL_SUMMARY;
                ods output ProblemSummary=PROB_SUMMARY;
                proc optmilp data = {}
                   primalout  = primal_out
                   dualout    = dual_out;
                run;
                """.format(name))

            for line in c['LOG'].split('\n'):
                if line[0:4] == '    ' or line[0:4] == 'NOTE':
                    print(line)

            self._primalSolution = session.sd2df('PRIMAL_OUT')
            self._dualSolution = session.sd2df('DUAL_OUT')

            # Get Problem Summary
            self._problemSummary = session.sd2df('PROB_SUMMARY')
            self._problemSummary.replace(np.nan, '', inplace=True)
            self._problemSummary = self._problemSummary[['Label1',
                                                         'cValue1']]
            self._problemSummary.set_index(['Label1'], inplace=True)
            self._problemSummary.columns = ['Value']
            self._problemSummary.index.names = ['Label']

            # Get Solution Summary
            self._solutionSummary = session.sd2df('SOL_SUMMARY')
            self._solutionSummary.replace(np.nan, '', inplace=True)
            self._solutionSummary = self._solutionSummary[['Label1',
                                                           'cValue1']]
            self._solutionSummary.set_index(['Label1'], inplace=True)
            self._solutionSummary.columns = ['Value']
            self._solutionSummary.index.names = ['Label']

            # Parse solutions
            for _, row in self._primalSolution.iterrows():
                self._variableDict[row['_VAR_']]._value = row['_VALUE_']

            return self._primalSolution

        else:  # OPTMODEL

            # Find problem type and initial values
            ptype = 1  # LP
            for v in self._variables:
                if v._type != sasoptpy.CONT:
                    ptype = 2
                    break

            print('NOTE: Converting model {} to OPTMODEL.'.format(self._name))
            optmodel_string = self.to_optmodel(header=True, options=options,
                                               ods=True, primalin=primalin)
            if verbose:
                print(optmodel_string)
            if not submit:
                return optmodel_string
            print('NOTE: Submitting OPTMODEL codes to SAS server.')
            optmodel_string = 'ods output SolutionSummary=SOL_SUMMARY;\n' +\
                              'ods output ProblemSummary=PROB_SUMMARY;\n' +\
                              optmodel_string
            c = session.submit(optmodel_string)

            # Print output
            for line in c['LOG'].split('\n'):
                if line[0:4] == '    ' or line[0:4] == 'NOTE':
                    print(line)

            # Parse solution
            self._primalSolution = session.sd2df('PRIMAL_OUT')
            self._primalSolution = self._primalSolution[
                    ['.VAR..NAME', '.VAR..LB', '.VAR..UB', '_VAR_',
                     '.VAR..RC']]
            self._primalSolution.columns = ['var', 'lb', 'ub', 'value', 'rc']
            self._dualSolution = session.sd2df('DUAL_OUT')
            self._dualSolution = self._dualSolution[
                    ['.CON..NAME', '.CON..BODY', '.CON..DUAL']]
            self._dualSolution.columns = ['con', 'value', 'dual']

            # Get Problem Summary
            self._problemSummary = session.sd2df('PROB_SUMMARY')
            self._problemSummary.replace(np.nan, '', inplace=True)
            self._problemSummary = self._problemSummary[['Label1', 'cValue1']]
            self._problemSummary.set_index(['Label1'], inplace=True)
            self._problemSummary.columns = ['Value']
            self._problemSummary.index.names = ['Label']

            # Get Solution Summary
            self._solutionSummary = session.sd2df('SOL_SUMMARY')
            self._solutionSummary.replace(np.nan, '', inplace=True)
            self._solutionSummary = self._solutionSummary[['Label1',
                                                           'cValue1']]
            self._solutionSummary.set_index(['Label1'], inplace=True)
            self._solutionSummary.columns = ['Value']
            self._solutionSummary.index.names = ['Label']

            # Parse solutions
            for _, row in self._primalSolution.iterrows():
                if row['var'] in self._variableDict:
                    self._variableDict[row['var']]._value = row['value']

            # Capturing dual values for LP problems
            if ptype == 1:
                for _, row in self._primalSolution.iterrows():
                    if row['var'] in self._variableDict:
                        self._variableDict[row['var']]._dual = row['rc']
                for _, row in self._dualSolution.iterrows():
                    if row['con'] in self._constraintDict:
                        self._constraintDict[row['con']]._dual = row['dual']

            return self._primalSolution