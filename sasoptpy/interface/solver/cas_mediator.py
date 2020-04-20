# CAS (SAS Viya) interface for sasoptpy

import inspect

import pandas as pd
import numpy as np
import warnings

import sasoptpy
from sasoptpy.interface import Mediator

class CASMediator(Mediator):
    """
    Handles the connection between sasoptpy and the SAS Viya (CAS) server

    Parameters
    ----------
    caller : :class:`sasoptpy.Model` or :class:`sasoptpy.Workspace`
        Model or workspace that mediator belongs to
    cas_session : :class:`swat.cas.connection.CAS`
        CAS connection

    Notes
    -----

    * CAS Mediator is used by :class:`sasoptpy.Model` and :class:`sasoptpy.Workspace` objects
      internally.

    """

    def __init__(self, caller, cas_session):
        self.caller = caller
        self.session = cas_session

    def solve(self, **kwargs):
        """
        Solve action for :class:`Model` objects
        """
        self.session.loadactionset(actionset='optimization')

        has_user_called_mps = kwargs.get('mps', kwargs.get('frame', False))
        options = kwargs.get('options', dict())

        mps_indicator = self.is_mps_format_needed(
            has_user_called_mps, options)

        if mps_indicator:
            return self.solve_with_mps(**kwargs)
        else:
            return self.solve_with_optmodel(**kwargs)

    def submit(self, **kwargs):
        """
        Submit action for custom input and :class:`sasoptpy.Workspace` objects
        """
        self.session.loadactionset(actionset='optimization')
        return self.submit_optmodel_code(**kwargs)

    def tune(self, **kwargs):
        """
        Wrapper for the MILP tuner
        """
        self.session.loadactionset(actionset='optimization')

        if not hasattr(self.session, 'optimization.tuner'):
            raise RuntimeError('Current CAS session version do not have tuner capability.')

        return self.tune_problem(**kwargs)


    def is_mps_format_needed(self, mps_option, options):

        enforced = False
        mps_option = mps_option
        session = self.session
        caller = self.caller

        model = caller

        # If runOptmodel action is not available on server
        if not hasattr(session.optimization, 'runoptmodel'):
            mps_option = True
            enforced = True

        if 'decomp' in options:
            mps_option = True
            enforced = True

        if mps_option:
            switch = False
            # Sets and parameter belong to abstract models
            if model.get_sets() or model.get_parameters():
                warnings.warn(
                    'INFO: Model {} has abstract elements, '.format(
                        model.get_name()) +
                    'switching to OPTMODEL mode.', UserWarning)
                switch = True
            # MPS format cannot represent nonlinear problems
            elif not sasoptpy.is_linear(model):
                warnings.warn(
                    'INFO: Model {} includes nonlinear or abstract '.format(
                        model.get_name()) +
                    'components, switching to OPTMODEL mode.', UserWarning)
                switch = True

            if switch and enforced and mps_option:
                raise RuntimeError('Problem requires runOptmodel action which '
                                   'is not available or appropriate')
            elif switch:
                mps_option = False

        return mps_option

    def solve_with_mps(self, **kwargs):
        """
        Submits the problem in MPS (DataFrame) format, supported by old versions

        Parameters
        ----------
        kwargs : dict
            Keyword arguments for solver settings and options

        Returns
        -------
        primal_solution : :class:`swat.dataframe.SASDataFrame`
            Solution of the model or None

        """

        model = self.caller
        session = self.session
        verbose = kwargs.get('verbose', False)
        submit = kwargs.get('submit', True)
        options = kwargs.get('options', dict())
        primalin = kwargs.get('primalin', False)
        name = kwargs.get('name', None)
        replace = kwargs.get('replace', True)
        drop = kwargs.get('drop', False)
        user_blocks = None

        print('NOTE: Converting model {} to DataFrame.'.format(model.get_name()))
        # Pre-upload argument parse

        # Find problem type and initial values
        ptype = 1  # LP
        for v in model.get_grouped_variables().values():
            if v._type != sasoptpy.CONT:
                ptype = 2
                break

        # Decomp check
        try:
            if options['decomp']['method'] == 'user':
                        user_blocks = self.upload_user_blocks()
                        options['decomp'] = {'blocks': user_blocks}
        except KeyError:
            pass

        # Initial value check for MIP
        if primalin:
            init_values = []
            var_names = []
            if ptype == 2:
                for v in model.loop_variables():
                    if v._init is not None:
                        var_names.append(v.get_name())
                        init_values.append(v._init)
                if (len(init_values) > 0 and
                   options.get('primalin', 1) is not None):
                    primalinTable = pd.DataFrame(
                        data={'_VAR_': var_names, '_VALUE_': init_values})
                    session.upload_frame(
                        primalinTable, casout={
                            'name': 'PRIMALINTABLE', 'replace': True})
                    options['primalin'] = 'PRIMALINTABLE'

        # Check if objective constant workaround is needed
        sfunc = session.solveLp if ptype == 1 else session.solveMilp
        has_arg = 'objconstant' in inspect.signature(sfunc).parameters
        if has_arg and 'objconstant' not in options:
            objconstant = model.get_objective()._linCoef['CONST']['val']
            options['objconstant'] = objconstant

        # Upload the problem
        mps_table = self.upload_model(name, replace=replace,
                                      constant=not has_arg, verbose=verbose)

        if verbose:
            print(mps_table.to_string())
        if not submit:
            return mps_table

        if ptype == 1:
            valid_opts = inspect.signature(session.solveLp).parameters
            lp_opts = {}
            for key, value in options.items():
                if key in valid_opts:
                    lp_opts[key] = value
            response = session.solveLp(
                data=mps_table.name, **lp_opts,
                primalOut={'caslib': 'CASUSER', 'name': 'primal',
                           'replace': True},
                dualOut={'caslib': 'CASUSER', 'name': 'dual',
                         'replace': True},
                objSense=model.get_objective().get_sense())
        elif ptype == 2:
            valid_opts = inspect.signature(session.solveMilp).parameters
            milp_opts = {}
            for key, value in options.items():
                if key in valid_opts:
                    milp_opts[key] = value
            response = session.solveMilp(
                data=mps_table.name, **milp_opts,
                primalOut={'caslib': 'CASUSER', 'name': 'primal',
                           'replace': True},
                dualOut={'caslib': 'CASUSER', 'name': 'dual',
                         'replace': True},
                objSense=model.get_objective().get_sense())

        model.response = response

        # Parse solution
        if(response.get_tables('status')[0] == 'OK'):
            model._primalSolution = session.CASTable(
                'primal', caslib='CASUSER').to_frame()
            model._dualSolution = session.CASTable(
                'dual', caslib='CASUSER').to_frame()
            # Bring solution to variables
            for _, row in model._primalSolution.iterrows():
                if ('_SOL_' in model._primalSolution and row['_SOL_'] == 1)\
                     or '_SOL_' not in model._primalSolution:
                    model.get_variable(row['_VAR_']).set_value(row['_VALUE_'])

            # Capturing dual values for LP problems
            if ptype == 1:
                model._primalSolution = model._primalSolution[
                    ['_VAR_', '_LBOUND_', '_UBOUND_', '_VALUE_',
                     '_R_COST_']]
                model._primalSolution.columns = ['var', 'lb', 'ub',
                                                'value', 'rc']
                model._dualSolution = model._dualSolution[
                    ['_ROW_', '_ACTIVITY_', '_VALUE_']]
                model._dualSolution.columns = ['con', 'value', 'dual']
                for row in model._primalSolution.itertuples():
                    model.get_variable(row.var)._dual = row.rc
                for row in model._dualSolution.itertuples():
                    model.get_constraint(row.con)._dual = row.dual
            elif ptype == 2:
                model._primalSolution = model._primalSolution[
                    ['_VAR_', '_LBOUND_', '_UBOUND_', '_VALUE_',
                     '_SOL_']]
                model._primalSolution.columns = ['var', 'lb', 'ub',
                                                'value', 'solution']
                model._dualSolution = model._dualSolution[
                    ['_ROW_', '_ACTIVITY_', '_SOL_']]
                model._dualSolution.columns = ['con', 'value',
                                              'solution']

        # Drop tables
        if drop:
            session.table.droptable(table=mps_table.name)
            if user_blocks is not None:
                session.table.droptable(table=user_blocks)
            if primalin:
                session.table.droptable(table='PRIMALINTABLE')

        # Post-solve parse
        if(response.get_tables('status')[0] == 'OK'):
            # Print problem and solution summaries
            model._problemSummary = response.ProblemSummary[['Label1',
                                                            'cValue1']]
            model._solutionSummary = response.SolutionSummary[['Label1',
                                                              'cValue1']]
            model._problemSummary.set_index(['Label1'], inplace=True)
            model._problemSummary.columns = ['Value']
            model._problemSummary.index.names = ['Label']
            model._solutionSummary.set_index(['Label1'], inplace=True)
            model._solutionSummary.columns = ['Value']
            model._solutionSummary.index.names = ['Label']
            # Record status and time
            model._status = response.solutionStatus
            model._soltime = response.solutionTime
            if('OPTIMAL' in response.solutionStatus):
                model._objval = response.objective
                # Replace initial values with current values
                for v in model.loop_variables():
                    v._init = v._value
                return model._primalSolution
            else:
                warnings.warn('Solution message is not OPTIMAL: {}'.format(response.solutionStatus), UserWarning)
                model._objval = 0
                return None
        else:
            raise RuntimeError('Solve came back with message: {}'.format(
                response.get_tables('status')[0]))

    def solve_with_optmodel(self, **kwargs):
        """
        Submits the problem in OPTMODEL format

        Parameters
        ----------
        kwargs : dict
            Keyword arguments for solver settings and options

        Returns
        -------
        primal_solution : :class:`swat.dataframe.SASDataFrame`
            Solution of the model or None

        """

        model = self.caller
        session = self.session
        verbose = kwargs.get('verbose', False)
        submit = kwargs.get('submit', True)

        print('NOTE: Converting model {} to OPTMODEL.'.format(
            model.get_name()))
        options = kwargs.get('options', dict())
        primalin = kwargs.get('primalin', False)
        optmodel_string = model.to_optmodel(header=False, options=options,
                                           ods=False, primalin=primalin,
                                            parse=True)
        if verbose:
            print(optmodel_string)
        if not submit:
            return optmodel_string
        print('NOTE: Submitting OPTMODEL code to CAS server.')
        response = session.runOptmodel(
            optmodel_string,
            outputTables={
                'names': {'solutionSummary': 'solutionSummary',
                          'problemSummary': 'problemSummary'}
                }
            )

        model.response = response

        # Parse solution
        return self.parse_cas_solution()

    def parse_cas_solution(self):
        """
        Performs post-solve operations

        Returns
        -------
        solution : :class:`swat.dataframe.SASDataFrame`
            Solution of the problem
        """
        caller = self.caller
        session = self.session
        response = caller.response

        if response.status == 'Syntax Error':
            raise SyntaxError('An invalid symbol is generated, check object names')
        elif response.status == 'Semantic Error':
            raise RuntimeError('A semantic error has occured, check statements and object types')

        solution = session.CASTable('solution').to_frame()
        dual_solution = session.CASTable('dual').to_frame()

        caller._primalSolution = solution
        caller._dualSolution = dual_solution

        caller._problemSummary = self.parse_cas_table('problemSummary')
        caller._solutionSummary = self.parse_cas_table('solutionSummary')

        caller._status = response.solutionStatus
        caller._soltime = response.solutionTime

        self.set_variable_values(solution)
        self.set_constraint_values(dual_solution)

        self.set_model_objective_value()
        self.set_variable_init_values()

        return solution

    def parse_table(self, table):
        session = self.session
        table = session.CASTable(table).to_frame()
        return table

    def parse_cas_table(self, table):
        """
        Converts requested :class:`swat.cas.table.CASTable` objects to
        :class:`swat.dataframe.SASDataFrame`
        """
        session = self.session
        table = session.CASTable(table).to_frame()
        return sasoptpy.interface.parse_optmodel_table(table)

    def set_variable_values(self, solution):
        """
        Performs post-solve assignment of variable values

        Parameters
        ----------
        solution : class:`swat.dataframe.SASDataFrame`
            Primal solution of the problem
        """
        caller = self.caller
        solver = caller.get_solution_summary().loc['Solver', 'Value']
        for row in solution.itertuples():
            caller.set_variable_value(row.var, row.value)
            if solver == 'LP':
                caller.set_dual_value(row.var, row.rc)

    def set_constraint_values(self, solution):
        """
        Performs post-solve assignment of constraint values

        Parameters
        ----------
        solution : class:`swat.dataframe.SASDataFrame`
            Primal solution of the problem
        """
        caller = self.caller
        solver = caller.get_solution_summary().loc['Solver', 'Value']
        if solver == 'LP':
            for row in solution.itertuples():
                con = caller.get_constraint(row.con)
                if con is not None:
                    con.set_dual(row.dual)

    def set_model_objective_value(self):
        """
        Performs post-solve assignment of objective values

        Parameters
        ----------
        solution : class:`swat.dataframe.SASDataFrame`
            Primal solution of the problem
        """
        caller = self.caller
        if sasoptpy.core.util.is_model(caller):
            if hasattr(caller.response, 'objective'):
                objval = caller.response.objective
                caller.set_objective_value(objval)

    def set_variable_init_values(self):
        """
        Performs post-solve assignment of variable initial values

        Parameters
        ----------
        solution : class:`swat.dataframe.SASDataFrame`
            Primal solution of the problem
        """
        caller = self.caller
        if sasoptpy.core.util.is_model(caller):
            for v in caller.loop_variables():
                v.set_init(v.get_value())

    def upload_user_blocks(self):
        """
        Uploads user-defined decomposition blocks to the CAS server

        Returns
        -------
        name : string
            CAS table name of the user-defined decomposition blocks

        Examples
        --------

        >>> userblocks = m.upload_user_blocks()
        >>> m.solve(milp={'decomp': {'blocks': userblocks}})

        """
        sess = self.session
        model = self.caller

        blocks_dict = {}
        block_counter = 0
        decomp_table = []
        for c in model.loop_constraints():
            if c._block is not None:
                if c._block not in blocks_dict:
                    blocks_dict[c._block] = block_counter
                    block_counter += 1
                block_no = blocks_dict[c._block]
                decomp_table.append([c.get_name(), block_no])
        frame_decomp_table = pd.DataFrame(decomp_table,
                                          columns=['_ROW_', '_BLOCK_'])
        response = sess.upload_frame(frame_decomp_table,
                                     casout={'name': 'BLOCKSTABLE',
                                             'replace': True})
        return(response.name)

    def upload_model(self, name=None, replace=True, constant=False,
                     verbose=False):
        """
        Converts internal model to MPS table and upload to CAS session

        Parameters
        ----------
        name : string, optional
            Desired name of the MPS table on the server
        replace : boolean, optional
            Option to replace the existing MPS table

        Returns
        -------
        frame : :class:`swat.cas.table.CASTable`
            Reference to the uploaded CAS Table

        Notes
        -----

        - This method returns None if the model session is not valid.
        - Name of the table is randomly assigned if name argument is None
          or not given.
        - This method should not be used if :func:`Model.solve` is going
          to be used. :func:`Model.solve` calls this method internally.

        """
        model = self.caller
        df = model.to_mps(constant=constant)
        if verbose:
            print(df.to_string())

        print('NOTE: Uploading the problem DataFrame to the server.')
        if name is not None:
            return self.session.upload_frame(
                data=df, casout={'name': name, 'replace': replace})
        else:
            return self.session.upload_frame(
                data=df, casout={'replace': replace})

    def submit_optmodel_code(self, **kwargs):
        """
        Converts caller into OPTMODEL code and submits using
        optimization.runOptmodel action

        Parameters
        ----------
        kwargs :
            Solver settings and options
        """

        caller = self.caller
        session = self.session
        optmodel_code = sasoptpy.util.to_optmodel(caller, header=False, parse=True)
        verbose = kwargs.get('verbose', None)

        if verbose:
            print(sasoptpy.to_optmodel(caller))

        response = session.runOptmodel(
            optmodel_code
        )

        caller.response = response
        caller.parse_solve_responses()
        caller.parse_print_responses()
        caller.parse_create_data_responses(self)

        return self.parse_cas_workspace_response()

    def parse_cas_workspace_response(self):
        """
        Parses results of workspace submission
        """
        caller = self.caller
        session = self.session
        response = caller.response

        if response.status == 'Syntax Error':
            raise SyntaxError('An invalid symbol is generated, check object names')
        elif response.status == 'Semantic Error':
            raise RuntimeError('A semantic error has occured, check statements and object types')

        solution = session.CASTable('solution').to_frame()
        dual_solution = session.CASTable('dual').to_frame()

        caller._primalSolution = solution
        caller._dualSolution = dual_solution

        self.set_workspace_variable_values(solution)
        #self.set_constraint_values(dual_solution)

        # self.set_model_objective_value()
        # self.set_variable_init_values()

        return solution

    def set_workspace_variable_values(self, solution):
        """
        Performs post-solve assignment of :class:`sasoptpy.Workspace` variable values
        """
        caller = self.caller
        for row in solution.itertuples():
            caller.set_variable_value(row.var, row.value)

    def tune_problem(self, **kwargs):
        """
        Calls optimization.tuner CAS action to finds out the ideal configuration
        """
        model = self.caller
        session = self.session
        name = model.get_name()

        if not sasoptpy.is_linear(model):
            raise TypeError('Model {} is not linear'.format(model.get_name()))
        if not sasoptpy.util.has_integer_variables(model):
            raise TypeError('Model {} do not have integer or binary variables'.format(model.get_name()))

        self.upload_model(name=name)

        if kwargs.get('tunerParameters') is None:
            kwargs['tunerParameters'] = {'maxconfigs': 100}

        response = session.optimization.tuner(
            instances=[{'data': name}],
            **kwargs
        )

        def replace_column_names(sasdf):
            colnames = sasdf.columns
            collabels = []
            for i in colnames:
                if sasdf.colinfo[i].label is not None:
                    collabels.append(sasdf.colinfo[i].label)
                else:
                    collabels.append(i)
            sasdf.columns = collabels
            return sasdf

        performance = response.PerformanceInformation
        info = response.TunerInformation
        summary = response.TunerSummary
        results = response.TunerResults

        performance = replace_column_names(performance)
        info = replace_column_names(info)
        summary = replace_column_names(summary)
        results = replace_column_names(results)

        model._tunerResults = {
            'Performance Information': performance,
            'Tuner Information': info,
            'Tuner Summary': summary,
            'Tuner Results': results
        }

        return results
