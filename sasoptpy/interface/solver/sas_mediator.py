# SAS MVA interface for sasoptpy

import sasoptpy
from sasoptpy.interface import Mediator

class SASMediator(Mediator):

    def __init__(self, sas_session):
        self.session = sas_session

    def solve(self, session, options, submit, name,
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