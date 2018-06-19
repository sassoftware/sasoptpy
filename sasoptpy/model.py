#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

'''
Model includes :class:`Model` class, the main structure of an opt. model

'''


import inspect
from math import inf
from types import GeneratorType
import warnings

import numpy as np
import pandas as pd

import sasoptpy.components
import sasoptpy.utils


class Model:
    '''
    Creates an optimization model

    Parameters
    ----------
    name : string
        Name of the model
    session : :class:`swat.cas.connection.CAS` object or :class:`saspy.SASsession` object, optional
        CAS or SAS Session object

    Examples
    --------

    >>> from swat import CAS
    >>> import sasoptpy as so
    >>> s = CAS('cas.server.address', port=12345)
    >>> m = so.Model(name='my_model', session=s)
    NOTE: Initialized model my_model

    >>> mip = so.Model(name='mip')
    NOTE: Initialized model mip
    '''

    def __init__(self, name, session=None):
        self._name = sasoptpy.utils.check_name(name, 'model')
        self._session = session
        self._variables = []
        self._constraints = []
        self._vargroups = []
        self._congroups = []
        self._objective = sasoptpy.components.Expression(0, name=name+'_obj')
        self._datarows = []
        self._sense = sasoptpy.utils.MIN
        self._variableDict = {}
        self._constraintDict = {}
        self._vcid = {}
        self._soltime = 0
        self._objval = 0
        self._status = ''
        self._castablename = None
        self._mpsmode = 0
        self._problemSummary = None
        self._solutionSummary = None
        self._primalSolution = pd.DataFrame()
        self._dualSolution = pd.DataFrame()
        self._milp_opts = {}
        self._lp_opts = {}
        self._sets = []
        self._parameters = []
        self._impvars = []
        self._statements = []
        # self._events = [] 
        self._objorder = sasoptpy.utils.register_name(name, self)
        print('NOTE: Initialized model {}.'.format(name))

    def __eq__(self, other):
        if not isinstance(other, sasoptpy.Model):
            warnings.warn('Cannot compare Model object with {}'.
                          format(type(other)), RuntimeWarning, stacklevel=2)
            return False
        return super().__eq__(other)

    def add_variable(self, var=None, vartype=sasoptpy.utils.CONT, name=None,
                     lb=0, ub=inf, init=None, abstract=False):
        '''
        Adds a new variable to the model

        New variables can be created via this method or existing variables
        can be added to the model.

        Parameters
        ----------
        var : :class:`Variable` object, optional
            Existing variable to be added to the problem
        vartype : string, optional
            Type of the variable, either 'BIN', 'INT' or 'CONT'
        name : string, optional
            Name of the variable to be created
        lb : float, optional
            Lower bound of the variable
        ub : float, optional
            Upper bound of the variable
        init : float, optional
            Initial value of the variable

        Returns
        -------
        :class:`Variable` object
            Variable that is added to the model

        Examples
        --------
        Adding a variable on the fly

        >>> m = so.Model(name='demo')
        >>> x = m.add_variable(name='x', vartype=so.INT, ub=10, init=2)
        >>> print(repr(x))
        NOTE: Initialized model demo
        sasoptpy.Variable(name='x', lb=0, ub=10, init=2, vartype='INT')

        Adding an existing variable to a model

        >>> y = so.Variable(name='y', vartype=so.BIN)
        >>> m = so.Model(name='demo')
        >>> m.add_variable(var=y)

        Notes
        -----
        * If argument *var* is not None, then all other arguments are ignored.
        * A generic variable name is generated if name argument is None.

        See also
        --------
        :func:`Model.include`
        '''
        # name = check_name(name, 'var')
        # Check bounds
        if lb is None:
            lb = 0
        if ub is None:
            ub = inf
        # Existing or new variable
        if var is not None:
            if isinstance(var, sasoptpy.components.Variable):
                self._variables.append(var)
            else:
                print('ERROR: Use the appropriate argument name for variable.')
        else:
            var = sasoptpy.components.Variable(name, vartype, lb, ub, init)
            self._variables.append(var)
        self._variableDict[var._name] = var
        return var

    def add_variables(self, *argv, vg=None, name=None,
                      vartype=sasoptpy.utils.CONT,
                      lb=None, ub=None, init=None, abstract=None):
        '''
        Adds a group of variables to the model

        Parameters
        ----------
        argv : list, dict, :class:`pandas.Index`
            Loop index for variable group
        vg : :class:`VariableGroup` object, optional
            An existing object if it is being added to the model
        name : string, optional
            Name of the variables
        vartype : string, optional
            Type of variables, `BIN`, `INT`, or `CONT`
        lb : list, dict, :class:`pandas.Series`
            Lower bounds of variables
        ub : list, dict, :class:`pandas.Series`
            Upper bounds of variables
        init : list, dict, :class:`pandas.Series`
            Initial values of variables

        See also
        --------
        :class:`VariableGroup`

        Notes
        -----
        If `vg` argument is passed, all other arguments are ignored.

        Examples
        --------

        >>> production = m.add_variables(PERIODS, vartype=so.INT,
                                        name='production', lb=min_production)
        >>> print(production)
        >>> print(repr(production))
        Variable Group (production) [
          [Period1: production['Period1',]]
          [Period2: production['Period2',]]
          [Period3: production['Period3',]]
        ]
        sasoptpy.VariableGroup(['Period1', 'Period2', 'Period3'],
        name='production')

        '''
        if vg is not None:
            if isinstance(vg, sasoptpy.components.VariableGroup):
                for i in vg:
                    self._variables.append(i)
            else:
                print('ERROR: Cannot add variable group of type {}'.format(
                    type(vg)))
        else:
            name = sasoptpy.utils.check_name(name, 'var')
            if abstract is None:
                abstract = isinstance(argv[0], sasoptpy.data.Set)
            vg = sasoptpy.components.VariableGroup(*argv, name=name,
                                                   vartype=vartype,
                                                   lb=lb, ub=ub, init=init,
                                                   abstract=abstract)
            for i in vg:
                self._variables.append(i)
        for i in vg:
            self._variableDict[i._name] = i
        self._vargroups.append(vg)
        return vg

    def add_constraint(self, c, name=None):
        '''
        Adds a single constraint to the model

        Parameters
        ----------
        c : Constraint
            Constraint to be added to the model
        name : string, optional
            Name of the constraint

        Returns
        -------
        :class:`Constraint` object

        Examples
        --------

        >>> x = m.add_variable(name='x', vartype=so.INT, lb=0, ub=5)
        >>> y = m.add_variables(3, name='y', vartype=so.CONT, lb=0, ub=10)
        >>> c1 = m.add_constraint(x + y[0] >= 3, name='c1')
        >>> print(c1)
         x  +  y[0]  >=  3

        >>> c2 = m.add_constraint(x - y[2] == [4, 10], name='c2')
        >>> print(c2)
         -  y[2]  +  x  =  [4, 10]

        '''
        if isinstance(c, sasoptpy.components.Constraint):
            # Do not add if the constraint is not valid
            if ((c._direction == 'L' and c._linCoef['CONST']['val'] == -inf) or
               (c._direction == 'G' and c._linCoef['CONST']['val'] == inf)):
                return None
            self._constraints.append(c)
            if name is not None or (name is None and c._name is None):
                name = sasoptpy.utils.check_name(name, 'con')
                c._name = name
                c._objorder = sasoptpy.utils.register_name(name, c)
            self._constraintDict[c._name] = c
        else:
            raise Exception('Expression is not a constraint!')
        # Return reference to the Constraint object
        return c

    def add_constraints(self, argv, cg=None, name=None):
        '''
        Adds a set of constraints to the model

        Parameters
        ----------
        argv : Generator type objects
            List of constraints as a Generator-type object
        cg : :class:`ConstraintGroup` object, optional
            An existing list of constraints if an existing group is being added
        name : string, optional
            Name for the constraint group and individual constraint prefix

        Returns
        -------
        :class:`ConstraintGroup` object
            A group object for all constraints aded

        Examples
        --------

        >>> x = m.add_variable(name='x', vartype=so.INT, lb=0, ub=5)
        >>> y = m.add_variables(3, name='y', vartype=so.CONT, lb=0, ub=10)
        >>> c = m.add_constraints((x + 2 * y[i] >= 2 for i in [0, 1, 2]),
                                  name='c')
        >>> print(c)
        Constraint Group (c) [
          [0:  2.0 * y[0]  +  x  >=  2]
          [1:  2.0 * y[1]  +  x  >=  2]
          [2:  2.0 * y[2]  +  x  >=  2]
        ]

        >>> t = m.add_variables(3, 4, name='t')
        >>> ct = m.add_constraints((t[i, j] <= x for i in range(3)
                                   for j in range(4)), name='ct')
        >>> print(ct)
        Constraint Group (ct) [
          [(0, 0):  -  x  +  t[0, 0]  <=  0]
          [(0, 1):  t[0, 1]  -  x  <=  0]
          [(0, 2):  -  x  +  t[0, 2]  <=  0]
          [(0, 3):  t[0, 3]  -  x  <=  0]
          [(1, 0):  t[1, 0]  -  x  <=  0]
          [(1, 1):  t[1, 1]  -  x  <=  0]
          [(1, 2):  -  x  +  t[1, 2]  <=  0]
          [(1, 3):  -  x  +  t[1, 3]  <=  0]
          [(2, 0):  -  x  +  t[2, 0]  <=  0]
          [(2, 1):  t[2, 1]  -  x  <=  0]
          [(2, 2):  t[2, 2]  -  x  <=  0]
          [(2, 3):  t[2, 3]  -  x  <=  0]
        ]

        '''
        if cg is not None:
            if isinstance(cg, sasoptpy.components.ConstraintGroup):
                for i in cg:
                    self._constraints.append(i)
                    self._constraintDict[i._name] = i
            else:
                print('ERROR: Cannot add constraint group of type {}'.format(
                    type(cg)))
            self._congroups.append(cg)
            return cg
        else:
            if type(argv) == list or type(argv) == GeneratorType:
                name = sasoptpy.utils.check_name(name, 'con')
                cg = sasoptpy.components.ConstraintGroup(argv, name=name)
                for i in cg:
                    self._constraints.append(i)
                    self._constraintDict[i._name] = i
                self._congroups.append(cg)
                return cg
            elif type(argv) == sasoptpy.components.Constraint:
                print('WARNING: add_constraints argument is a single' +
                      ' constraint, inserting as a single constraint')
                name = sasoptpy.utils.check_name(name, 'con')
                c = self.add_constraint(c=argv, name=name)
                return c

    def add_set(self, name, init=None, settype='num'):
        if init:
            if isinstance(init, range):
                newinit = str(init.start) + '..' + str(init.stop)
                if init.step != 1:
                    newinit = ' by ' + init.step
                init = newinit
            elif isinstance(init, list):
                init = '[' + ' '.join([str(i) for i in init]) + ']'
        newset = sasoptpy.data.Set(name, init=init, settype=settype)
        self._sets.append(newset)
        return newset

    def add_parameter(self, *argv, name=None, init=None):
        if len(argv) == 0:
            p = sasoptpy.data.Parameter(name, keys=(), init=init)
            self._parameters.append(p)
            return p['']
        else:
            keylist = list(argv)
            p = sasoptpy.data.Parameter(name, keys=keylist, init=init)
            self._parameters.append(p)
            return p

    def add_implicit_variable(self, argv=None, name=None):
        '''
        Adds an implicit variable to the model
        '''
        iv = sasoptpy.data.ExpressionDict(name=name)
        if argv:
            if type(argv) == GeneratorType:
                for arg in argv:
                    keynames = ()
                    keyrefs = ()
                    if argv.gi_code.co_nlocals == 1:
                        itlist = argv.gi_code.co_cellvars
                    else:
                        itlist = argv.gi_code.co_varnames
                    localdict = argv.gi_frame.f_locals
                    for i in itlist:
                        if i != '.0':
                            keynames += (i,)
                    for i in keynames:
                        keyrefs += (localdict[i],)
                    iv[keyrefs] = arg
                self._impvars.append(iv)
            elif type(argv) == sasoptpy.components.Expression and\
                 argv._abstract:
                iv[''] = argv
                iv['']._objorder = iv._objorder
                self._impvars.append(iv)
                return iv['']
            else:
                iv = argv

        return iv

    def add_statement(self, statement):
        if isinstance(statement, sasoptpy.components.Expression):
            self._statements.append(sasoptpy.data.Statement(str(statement)))

    def read_data(self, table, keyset, option='', key=[], params=[]):
        '''
        Reads a CASTable into PROC OPTMODEL sets
        '''

        # Reading key
        if keyset is not None:
            if key != []:
                for i, k in enumerate(keyset):
                    k._colname = str(key[i])

        # Reading parameters
        for p in params:
            p.setdefault('column', None)
            p.setdefault('index', None)
            p['param']._set_loop(table, keyset, p['column'], p['index'])

        if type(table).__name__ == 'CASTable':
            s = 'read data {}'.format(table.name)
        elif type(table).__name__ == 'SASdata':
            s = 'read data {}'.format(table.table)
        else:
            s = 'read data {}'.format(table)
        if option:
            s += ' {}'.format(option)
        s += ' into '
        if len(keyset) == 1:
            k = keyset[0]
            if isinstance(k._colname, str):
                s += '{}=[{}] '.format(k._name, k._colname)
            elif isinstance(k._colname, list):
                s += '{}=[{}] '.format(k._name, ' '.join(k._colname))
        else:
            s += '['
            for k in keyset:
                s += k._colname + ' '
            s = s[:-1]
            s += '] '
        parlist = []
        for p in params:
            parlist.append(p['param']._to_read_data())
        s += ' '.join(parlist)
        s += ';'
        self._statements.append(sasoptpy.data.Statement(s))

    def read_table(self, table, key=['_N_'], columns=[],
                   key_type='num', upload=False):
        '''
        Reads a CAS Table or pandas DataFrame into the model

        Parameters
        ----------
        table : :class:`swat.cas.table.CASTable` or :class:`pandas.DataFrame`\
                object
            CASTable or DataFrame object to read the data from
        key : list, optional
            List of key columns (for CASTable) or index columns (for DataFrame)
        columns : list, optional
            List of columns to read into parameters
        key_type : string, optional
            Type of the key columns, 'num' or 'str' or their comma separated\
            combinations
        upload : boolean, optional
            Option for uploading a local data to CAS server first

        Returns
        -------
        tuple
            A tuple where first element is the key (index) and second element\
            is a list of requested columns

        Notes
        -----

        - If the model is running in saspy or MPS mode, then the data is read
          to client from the CAS server.
        - If the model is running in OPTMODEL mode, then this method generates
          the corresponding optmodel code.
        - When table is a CASTable object, since the actual data is stored
          on the CAS server, some of the functionalities may be limited.
        - For the local data, `upload` argument can be passed for performance
          improvement.

        Examples
        --------

        >>> info = pd.DataFrame([
                ['clock', 6, 15, 1],
                ['pc', 3, 14, 5],
                ['headphone', 2, 9, 3],
                ['mug', 2, 4, 1],
                ['book', 5, 1, 3],
                ['pen', 1, 1, 4]
                ], columns=['item', 'weight', 'value', 'limit'])
        >>> ITEMS, [weight, value, limit] = m.read_table(
                info, key=['item'], columns=['weight', 'value', 'limit'],
                key_stype='str', upload=False)

        See also
        --------
        :func:`Model.read_data`
        :func:`Model.add_parameter`
        :func:`Model.add_set`

        '''

        if upload and type(table).__name__ != 'CASTable' and\
           self.test_session() == 'CAS':
            table = self._session.upload_frame(table)
        elif upload and type(table).__name__ == 'DataFrame' and\
             self.test_session() == 'SAS':
            table = self._session.df2sd(table)

        if type(table).__name__ == 'CASTable':
            if not key or key == [None]:
                key = ['_N_']
            keyset = self.add_set(
                name='set_' + ('_'.join([str(i) for i in key])
                               if key != ['_N_'] else table.name + '_N'),
                settype=key_type
                )
            pars = []
            for col in columns:
                pars.append(self.add_parameter(keyset, name=col))

            self.read_data(table, keyset=[keyset], key=key, params=[
                {'param': i} for i in pars])
        elif type(table).__name__ == 'SASdata':
            if not key or key == [None]:
                key = ['_N_']
            keyset = self.add_set(
                name='set_' + ('_'.join([str(i) for i in key])
                               if key != ['_N_'] else table.table + '_N'),
                settype=key_type
                )
            pars = []
            for col in columns:
                pars.append(self.add_parameter(keyset, name=col))

            self.read_data(table, keyset=[keyset], key=key, params=[
                {'param': i} for i in pars])
        elif type(table).__name__ == 'DataFrame':
            if key and key != [None] and key != ['_N_']:
                table = table.set_index(key)
            keyset = table.index.tolist()
            pars = []
            for col in columns:
                pars.append(table[col])
        else:
            print('ERROR: Data type is not recognized in read_table: {} ({})'
                  .format(table, type(table)))
            return None
        if pars:
            return (keyset, pars)
        else:
            return keyset

    def drop_variable(self, variable):
        '''
        Drops a variable from the model

        Parameters
        ----------
        variable : :class:`Variable` object
            The variable to be dropped from the model

        Examples
        --------

        >>> x = m.add_variable(name='x')
        >>> y = m.add_variable(name='y')
        >>> print(m.get_variable('x'))
         x
        >>> m.drop_variable(x)
        >>> print(m.get_variable('x'))
        None

        See also
        --------
        :func:`Model.drop_variables`
        :func:`Model.drop_constraint`
        :func:`Model.drop_constraints`

        '''
        for i, v in enumerate(self._variables):
            if id(variable) == id(v):
                del self._variables[i]
                return

    def drop_constraint(self, constraint):
        '''
        Drops a constraint from the model

        Parameters
        ----------
        constraint : :class:`Constraint` object
            The constraint to be dropped from the model

        Examples
        --------

        >>> c1 = m.add_constraint(2 * x + y <= 15, name='c1')
        >>> print(m.get_constraint('c1'))
          2.0 * x  +  y  <=  15
        >>> m.drop_constraint(c1)
        >>> print(m.get_constraint('c1'))
        None

        See also
        --------
        :func:`Model.drop_constraints`
        :func:`Model.drop_variable`
        :func:`Model.drop_variables`

        '''
        try:
            del self._constraintDict[constraint._name]
            for i, c in enumerate(self._constraints):
                if c._name == constraint._name:
                    del self._constraints[i]
        except KeyError:
            pass
        except AttributeError:
            pass

    def drop_variables(self, variables):
        '''
        Drops a variable group from the model

        Parameters
        ----------
        variables : :class:`VariableGroup` object
            The variable group to be dropped from the model

        Examples
        --------

        >>> x = m.add_variables(3, name='x')
        >>> print(m.get_variables())
        [sasoptpy.Variable(name='x_0',  vartype='CONT'),
         sasoptpy.Variable(name='x_1',  vartype='CONT')]
        >>> m.drop_variables(x)
        >>> print(m.get_variables())
        []

        See also
        --------
        :func:`Model.drop_variable`
        :func:`Model.drop_constraint`
        :func:`Model.drop_constraints`

        '''
        for v in variables:
            self.drop_variable(v)

    def drop_constraints(self, constraints):
        '''
        Drops a constraint group from the model

        Parameters
        ----------
        constraints : :class:`ConstraintGroup` object
            The constraint group to be dropped from the model

        Examples
        --------

        >>> c1 = m.add_constraints((x[i] + y <= 15 for i in [0, 1]), name='c1')
        >>> print(m.get_constraints())
        [sasoptpy.Constraint( x[0]  +  y  <=  15, name='c1_0'),
         sasoptpy.Constraint( x[1]  +  y  <=  15, name='c1_1')]
        >>> m.drop_constraints(c1)
        >>> print(m.get_constraints())
        []

        See also
        --------
        :func:`Model.drop_constraints`
        :func:`Model.drop_variable`
        :func:`Model.drop_variables`

        '''
        for c in constraints:
            self.drop_constraint(c)

    def include(self, *argv):
        '''
        Adds existing variables and constraints to a model

        Parameters
        ----------
        argv : :class:`Model`, :class:`Variable`, :class:`Constraint`,
            :class:`VariableGroup`, :class:`ConstraintGroup`
            Objects to be included in the model

        Examples
        --------

        Adding an existing variable

        >>> x = so.Variable(name='x', vartype=so.CONT)
        >>> m.include(x)

        Adding an existing constraint

        >>> c1 = so.Constraint(x + y <= 5, name='c1')
        >>> m.include(c1)

        Adding an existing set of variables

        >>> z = so.VariableGroup(3, 5, name='z', ub=10)
        >>> m.include(z)

        Adding an existing set of constraints

        >>> c2 = so.ConstraintGroup((x + 2 * z[i, j] >= 2 for i in range(3)
                                    for j in range(5)), name='c2')
        >>> m.include(c2)

        Adding an existing model (including its elements)

        >>> new_model = so.Model(name='new_model')
        >>> new_model.include(m)

        Notes
        -----
        * This method is essentially a wrapper for two methods,
          :func:`Model.add_variable` and
          :func:`Model.add_constraint`.
        * Including a model causes all variables and constraints inside the
          original model to be included.
        '''
        for i, c in enumerate(argv):
            if isinstance(c, sasoptpy.components.Variable):
                self.add_variable(var=c)
            elif isinstance(c, sasoptpy.components.VariableGroup):
                self.add_variables(vg=c)
            elif isinstance(c, sasoptpy.components.Constraint):
                self.add_constraint(c)
            elif isinstance(c, sasoptpy.components.ConstraintGroup):
                self.add_constraints(argv=None, cg=c)
            elif isinstance(c, Model):
                for v in c._variables:
                    self.add_variable(v)
                for cn in c._constraints:
                    self.add_constraint(cn)
                self._objective = c._objective
            else:
                print('WARNING: Cannot include argument {} {} {}'.format(
                    i, c, type(c)))

    def set_objective(self, expression, sense, name=None):
        '''
        Sets the objective function for the model

        Parameters
        ----------
        expression : :class:`Expression` object
            The objective function as an Expression
        sense : string
            Objective value direction, 'MIN' or 'MAX'
        name : string, optional
            Name of the objective value

        Returns
        -------
        :class:`Expression`
            Objective function as an :class:`Expression` object

        Examples
        --------

        >>> profit = so.Expression(5 * sales - 2 * material, name='profit')
        >>> m.set_objective(profit, so.MAX)
        >>> print(m.get_objective())
         -  2.0 * material  +  5.0 * sales

        >>> m.set_objective(4 * x - 5 * y, name='obj')
        >>> print(repr(m.get_objective()))
        sasoptpy.Expression(exp =  4.0 * x  -  5.0 * y , name='obj')

        '''
        self._linCoef = {}
        if isinstance(expression, sasoptpy.components.Expression):
            if name is not None:
                obj = expression.copy()
            else:
                obj = expression
        else:
            obj = sasoptpy.components.Expression(expression)
        self._objective = obj
        if self._objective._name is None:
            name = sasoptpy.utils.check_name(name, 'obj')
            self._objective._objorder = sasoptpy.utils.register_name(
                name, self._objective)
            self._objective._name = name
        self._sense = sense
        self._objective._temp = False
        return self._objective

    def get_objective(self):
        '''
        Returns the objective function as an :class:`Expression` object

        Returns
        -------
        :class:`Expression` object
            Objective function

        Examples
        --------

        >>> m.set_objective(4 * x - 5 * y, name='obj')
        >>> print(repr(m.get_objective()))
        sasoptpy.Expression(exp =  4.0 * x  -  5.0 * y , name='obj')

        '''
        return self._objective

    def get_objective_value(self):
        '''
        Returns the optimal objective value, if it exists

        Returns
        -------
        float : Objective value at current solution

        Examples
        --------

        >>> m.solve()
        >>> print(m.get_objective_value())
        42.0

        '''
        return self._objective.get_value()

    def get_constraint(self, name):
        '''
        Returns the reference to a constraint in the model

        Parameters
        ----------
        name : string
            Name of the constraint requested

        Returns
        -------
        :class:`Constraint` object

        Examples
        --------

        >>> m.add_constraint(2 * x + y <= 15, name='c1')
        >>> print(m.get_constraint('c1'))
        2.0 * x  +  y  <=  15

        '''
        return self._constraintDict.get(name)

    def get_constraints(self):
        '''
        Returns a list of constraints in the model

        Returns
        -------
        list : A list of :class:`Constraint` objects

        Examples
        --------

        >>> m.add_constraint(x[0] + y <= 15, name='c1')
        >>> m.add_constraints((2 * x[i] - y >= 1 for i in [0, 1]), name='c2')
        >>> print(m.get_constraints())
        [sasoptpy.Constraint( x[0]  +  y  <=  15, name='c1'),
         sasoptpy.Constraint( 2.0 * x[0]  -  y  >=  1, name='c2_0'),
         sasoptpy.Constraint( 2.0 * x[1]  -  y  >=  1, name='c2_1')]

        '''
        return self._constraints

    def get_variable(self, name):
        '''
        Returns the reference to a variable in the model

        Parameters
        ----------
        name : string
            Name or key of the variable requested

        Returns
        -------
        :class:`Variable` object

        Examples
        --------

        >>> m.add_variable(name='x', vartype=so.INT, lb=3, ub=5)
        >>> var1 = m.get_variable('x')
        >>> print(repr(var1))
        sasoptpy.Variable(name='x', lb=3, ub=5, vartype='INT')

        '''
        for v in self._variables:
            if v._name == name:
                return v
        return None

    def get_variables(self):
        '''
        Returns a list of variables

        Returns
        -------
        list : A list of :class:`Variable` objects

        Examples
        --------

        >>> x = m.add_variables(2, name='x')
        >>> y = m.add_variable(name='y')
        >>> print(m.get_variables())
        [sasoptpy.Variable(name='x_0',  vartype='CONT'),
         sasoptpy.Variable(name='x_1',  vartype='CONT'),
         sasoptpy.Variable(name='y',  vartype='CONT')]

        '''
        return self._variables

    def get_variable_coef(self, var):
        '''
        Returns the objective value coefficient of a variable

        Parameters
        ----------
        var : :class:`Variable` object or string
            Variable whose objective value is requested or its name

        Returns
        -------
        float
            Objective value coefficient of the given variable

        Examples
        --------

        >>> x = m.add_variable(name='x')
        >>> y = m.add_variable(name='y')
        >>> m.set_objective(4 * x - 5 * y, name='obj', sense=so.MAX)
        >>> print(m.get_variable_coef(x))
        4.0
        >>> print(m.get_variable_coef('y'))
        -5.0

        '''
        if isinstance(var, sasoptpy.components.Variable):
            varname = var._name
        else:
            varname = var
        if varname in self._objective._linCoef:
            return self._objective._linCoef[varname]['val']
        else:
            return 0

    def get_variable_value(self, var=None, name=None):
        '''
        Returns the value of a variable.

        Parameters
        ----------
        var : :class:`Variable` object, optional
            Variable object
        name : string, optional
            Name of the variable

        Notes
        -----
        - It is possible to get a variable's value using
          :func:`Variable.get_value` method, if the variable is not abstract.
        - This method is a wrapper around :func:`Variable.get_value` and an
          overlook function for model components
        '''
        if var and not name:
            if var._shadow:
                name = str(var).replace(' ', '')
            else:
                name = var._name
        elif not var and not name:
            return None

        if name in self._variableDict:
            return self._variableDict[name].get_value()
        else:
            if self._primalSolution is not None:
                for _, row in self._primalSolution.iterrows():
                    if row['var'] == name:
                        return row['value']
        return None

    def get_problem_summary(self):
        '''
        Returns the problem summary table to the user

        Returns
        -------
        :class:`swat.dataframe.SASDataFrame` object
            Problem summary obtained after :func:`Model.solve`

        Examples
        --------

        >>> m.solve()
        >>> ps = m.get_problem_summary()
        >>> print(type(ps))
        <class 'swat.dataframe.SASDataFrame'>

        >>> print(ps)
        Problem Summary
                                        Value
        Label
        Problem Name                   model1
        Objective Sense          Maximization
        Objective Function                obj
        RHS                               RHS
        Number of Variables                 2
        Bounded Above                       0
        Bounded Below                       2
        Bounded Above and Below             0
        Free                                0
        Fixed                               0
        Number of Constraints               2
        LE (<=)                             1
        EQ (=)                              0
        GE (>=)                             1
        Range                               0
        Constraint Coefficients             4

        >>> print(ps.index)
        Index(['Problem Name', 'Objective Sense', 'Objective Function', 'RHS',
        '', 'Number of Variables', 'Bounded Above', 'Bounded Below',
        'Bounded Above and Below', 'Free', 'Fixed', '',
        'Number of Constraints', 'LE (<=)', 'EQ (=)', 'GE (>=)', 'Range', '',
        'Constraint Coefficients'],
        dtype='object', name='Label')

        >>> print(ps.loc['Number of Variables'])
        Value               2
        Name: Number of Variables, dtype: object

        >>> print(ps.loc['Constraint Coefficients', 'Value'])
        4

        '''
        return self._problemSummary

    def get_solution_summary(self):
        '''
        Returns the solution summary table to the user

        Returns
        -------
        :class:`swat.dataframe.SASDataFrame` object
            Solution summary obtained after solve

        Examples
        --------

        >>> m.solve()
        >>> soln = m.get_solution_summary()
        >>> print(type(soln))
        <class 'swat.dataframe.SASDataFrame'>

        >>> print(soln)
        Solution Summary
                                       Value
        Label
        Solver                            LP
        Algorithm               Dual Simplex
        Objective Function               obj
        Solution Status              Optimal
        Objective Value                   10
        Primal Infeasibility               0
        Dual Infeasibility                 0
        Bound Infeasibility                0
        Iterations                         2
        Presolve Time                   0.00
        Solution Time                   0.01

        >>> print(soln.index)
        Index(['Solver', 'Algorithm', 'Objective Function', 'Solution Status',
               'Objective Value', '', 'Primal Infeasibility',
               'Dual Infeasibility', 'Bound Infeasibility', '', 'Iterations',
               'Presolve Time', 'Solution Time'],
              dtype='object', name='Label')

        >>> print(soln.loc['Solution Status', 'Value'])
        Optimal

        '''
        return self._solutionSummary

    def get_solution(self, vtype='Primal'):
        '''
        Returns the solution details associated with the primal or dual
        solution

        Parameters
        ----------
        vtype : string, optional
            'Primal' or 'Dual'

        Returns
        -------
        :class:`pandas.DataFrame` object
            Primal or dual solution table returned from the CAS Action

        Examples
        --------

        >>> m.solve()
        >>> print(m.get_solution('Primal'))
              _OBJ_ID_ _RHS_ID_               _VAR_ _TYPE_  _OBJCOEF_  _LBOUND_
        0  totalProfit      RHS      production_cap      I      -10.0       0.0
        1  totalProfit      RHS  production_Period1      I       10.0       5.0
        2  totalProfit      RHS  production_Period2      I       10.0       5.0
        3  totalProfit      RHS  production_Period3      I       10.0       0.0
             _UBOUND_  _VALUE_
        1.797693e+308     25.0
        1.797693e+308     25.0
        1.797693e+308     15.0
        1.797693e+308     25.0

        >>> print(m.get_solution('Dual'))
              _OBJ_ID_ _RHS_ID_       _ROW_ _TYPE_  _RHS_  _L_RHS_  _U_RHS_
        0  totalProfit      RHS  capacity_0      L    0.0      NaN      NaN
        1  totalProfit      RHS  capacity_1      L    0.0      NaN      NaN
        2  totalProfit      RHS  capacity_2      L    0.0      NaN      NaN
        3  totalProfit      RHS    demand_0      L   30.0      NaN      NaN
        4  totalProfit      RHS    demand_1      L   15.0      NaN      NaN
        5  totalProfit      RHS    demand_2      L   25.0      NaN      NaN
        _ACTIVITY_
               0.0
             -10.0
               0.0
              25.0
              15.0
              25.0

        '''
        if vtype == 'Primal' or vtype == 'primal':
            return self._primalSolution
        elif vtype == 'Dual' or vtype == 'dual':
            return self._dualSolution
        else:
            return None

    def set_session(self, session):
        '''
        Sets the CAS session for model

        Parameters
        ----------
        session : :class:`swat.cas.connection.CAS` or \
:class:`saspy.SASsession` objects
            CAS or SAS Session object

        Notes
        -----

        * Session of a model can be set at initialization.
          See :class:`Model`.

        '''
        self._session = session

    def set_coef(self, var, con, value):
        '''
        Updates the coefficient of a variable inside constraints

        Parameters
        ----------
        var : :class:`Variable` object
            Variable whose coefficient will be updated
        con : :class:`Constraint` object
            Constraint where the coefficient will be updated
        value : float
            The new value for the coefficient of the variable

        Examples
        --------

        >>> c1 = m.add_constraint(x + y >= 1, name='c1')
        >>> print(c1)
        y  +  x  >=  1
        >>> m.set_coef(x, c1, 3)
        >>> print(c1)
        y  +  3.0 * x  >=  1

        Notes
        -----
        Variable coefficient inside the constraint is replaced in-place.

        See also
        --------
        :func:`Constraint.update_var_coef`

        '''
        con.update_var_coef(var=var, value=value)

    def print_solution(self):
        '''
        Prints the current values of the variables

        Examples
        --------

        >>> m.solve()
        >>> m.print_solution()
        x: 2.0
        y: 0.0

        See also
        --------
        :func:`Model.get_solution`

        '''
        for v in self._variables:
            print('{}: {}'.format(v._name, v._value))

    def _append_row(self, row):
        '''
        Appends a new row to the model representation

        Parameters
        ----------
        row : list
            A new row to be added to the model representation for MPS format

        Returns
        -------
        int
            Current number for the ID column
        '''
        self._datarows.append(row + [str(self._id)])
        rowid = self._id
        self._id = self._id+1
        return rowid

    def to_frame(self):
        '''
        Converts the Python model into a DataFrame object in MPS format

        Returns
        -------
        :class:`pandas.DataFrame` object
            Problem in strict MPS format

        Examples
        --------

        >>> df = m.to_frame()
        >>> print(df)
             Field1 Field2  Field3 Field4 Field5 Field6 _id_
        0      NAME         model1      0             0    1
        1      ROWS                                        2
        2       MAX    obj                                 3
        3         L     c1                                 4
        4   COLUMNS                                        5
        5                x     obj      4                  6
        6                x      c1      3                  7
        7                y     obj     -5                  8
        8                y      c1      1                  9
        9       RHS                                       10
        10             RHS      c1      6                 11
        11   RANGES                                       12
        12   BOUNDS                                       13
        13   ENDATA                     0             0   14

        Notes
        -----
        * This method is called inside :func:`Model.solve`.
        '''
        self._id = 1
        if(len(self._datarows) > 0):  # For future reference
            # take a copy?
            self._mpsmode = 1
            self._datarows = []
        else:
            self._datarows = []
        # Create a dictionary of variables with constraint names
        var_con = {}
        for c in self._constraints:
            for v in c._linCoef:
                var_con.setdefault(v, []).append(c._name)
        # Check if objective has a constant field
        if self._objective._linCoef['CONST']['val'] != 0:
            obj_constant = self.add_variable(name=sasoptpy.utils.check_name(
                'obj_constant', 'var'))
            constant_value = self._objective._linCoef['CONST']['val']
            obj_constant.set_bounds(lb=constant_value, ub=constant_value)
            obj_constant._value = constant_value
            obj_name = self._objective._name + '_constant'
            self._objective = self._objective - constant_value + obj_constant
            self._objective._name = obj_name
            print('WARNING: The objective function contains a constant term.' +
                  ' An auxiliary variable is added.')
        # self._append_row(['*','SAS-Viya-Opt','MPS-Free Format','0','0','0'])
        self._append_row(['NAME', '', self._name, 0, '', 0])
        self._append_row(['ROWS', '', '', '', '', ''])
        if self._objective._name is not None:
            self._append_row([self._sense, self._objective._name,
                             '', '', '', ''])

        for c in self._constraints:
            self._append_row([c._direction, c._name, '', '', '', ''])
        self._append_row(['COLUMNS', '', '', '', '', ''])
        curtype = sasoptpy.utils.CONT
        for v in self._variables:
            f5 = 0
            self._vcid[v._name] = {}
            if v._type is sasoptpy.utils.INT and\
                    curtype is sasoptpy.utils.CONT:
                self._append_row(['', 'MARK0000', '\'MARKER\'', '',
                                 '\'INTORG\'', ''])
                curtype = sasoptpy.utils.INT
            if v._type is not sasoptpy.utils.INT\
                    and curtype is sasoptpy.utils.INT:
                self._append_row(['', 'MARK0001', '\'MARKER\'', '',
                                 '\'INTEND\'', ''])
                curtype = sasoptpy.utils.CONT
            if v._name in self._objective._linCoef:
                cv = self._objective._linCoef[v._name]
                current_row = ['', v._name, self._objective._name, cv['val']]
                f5 = 1
            elif v._name not in var_con:
                current_row = ['', v._name, self._objective._name, 0.0]
                f5 = 1
                var_con[v._name] = []
            for cn in var_con.get(v._name, []):
                if cn in self._constraintDict:
                    c = self._constraintDict[cn]
                    if v._name in c._linCoef:
                        if f5 == 0:
                            current_row = ['', v._name, c._name,
                                           c._linCoef[v._name]['val']]
                            f5 = 1
                        else:
                            current_row.append(c._name)
                            current_row.append(c._linCoef[v._name]['val'])
                            ID = self._append_row(current_row)
                            self._vcid[v._name][current_row[2]] = ID
                            self._vcid[v._name][current_row[4]] = ID
                            f5 = 0
            if f5 == 1:
                current_row.append('')
                current_row.append('')
                ID = self._append_row(current_row)
                self._vcid[v._name][current_row[2]] = ID
        if curtype is sasoptpy.utils.INT:
            self._append_row(['', 'MARK0001', '\'MARKER\'', '', '\'INTEND\'',
                             ''])
        self._append_row(['RHS', '', '', '', '', ''])
        f5 = 0
        for c in self._constraints:
            if c._direction == 'L' and c._linCoef['CONST']['val'] == -inf:
                continue
            if c._direction == 'G' and c._linCoef['CONST']['val'] == 0:
                continue
            rhs = - c._linCoef['CONST']['val']
            if rhs != 0:
                if f5 == 0:
                    current_row = ['', 'RHS', c._name, rhs]
                    f5 = 1
                else:
                    current_row.append(c._name)
                    current_row.append(rhs)
                    # self._append_row(['', 'RHS', c._name, rhs, '', ''])
                    f5 = 0
                    self._append_row(current_row)
        if f5 == 1:
            current_row.append('')
            current_row.append('')
            self._append_row(current_row)
        self._append_row(['RANGES', '', '', '', '', ''])
        for c in self._constraints:
            if c._range != 0:
                self._append_row(['', 'rng', c._name, c._range, '', ''])
        self._append_row(['BOUNDS', '', '', '', '', ''])
        for v in self._variables:
            if self._vcid[v._name] == {}:
                continue
            if v._lb == v._ub:
                self._append_row(['FX', 'BND', v._name, v._ub, '', ''])
            if v._lb is not None and v._type is not sasoptpy.utils.BIN:
                if v._ub == inf and v._lb == -inf:
                    self._append_row(['FR', 'BND', v._name, '', '', ''])
                elif not v._ub == v._lb:
                    if v._type == sasoptpy.utils.INT and\
                       v._lb == 0 and v._ub == inf:
                        self._append_row(['PL', 'BND', v._name, '', '', ''])
                    elif not(v._type == sasoptpy.utils.CONT and v._lb == 0):
                        self._append_row(['LO', 'BND', v._name, v._lb, '', ''])
            if v._ub != inf and v._ub is not None and not\
               (v._type is sasoptpy.utils.BIN and v._ub == 1) and\
               v._lb != v._ub:
                self._append_row(['UP', 'BND', v._name, v._ub, '', ''])
            if v._type is sasoptpy.utils.BIN:
                self._append_row(['BV', 'BND', v._name, '1.0', '', ''])
        self._append_row(['ENDATA', '', '', 0.0, '', 0.0])
        mpsdata = pd.DataFrame(data=self._datarows,
                               columns=['Field1', 'Field2', 'Field3', 'Field4',
                                        'Field5', 'Field6', '_id_'])
        self._datarows = []
        return mpsdata

    def to_optmodel(self, header=True, expand=False, ordered=False,
                    options={}):
        '''
        Generates the equivalent PROC OPTMODEL code for the model.

        Parameters
        ----------
        header : boolean, optional
            Option to include PROC headers
        expand : boolean, optional
            Option to include 'expand' command to OPTMODEL code
        ordered : boolean, optional
            Option to generate OPTMODEL code in a specific order (True) or\
            in creation order (False)
        options : dict, optional
            Solver options for the OPTMODEL solve command

        Returns
        -------
        string
            PROC OPTMODEL representation of the model

        Examples
        --------

        >>> print(m.to_optmodel())

        '''

        if ordered:
            s = ''

            if header:
                s = 'proc optmodel;\n'

            tab = '   '

            s += tab + '/* Sets */\n'
            for i in self._sets:
                s += tab + i._defn() + '\n'

            s += '\n' + tab + '/* Parameters */\n'
            for i in self._parameters:
                s += i._defn(tab) + '\n'

            s += '\n' + tab + '/* Statements */\n'
            for i in self._statements:
                s += tab + i._defn() + '\n'

            s += '\n' + tab + '/* Variables */\n'
            for i in self._vargroups:
                s += i._defn(tabs=tab) + '\n'

            for v in self._variables:
                if v._parent is None:
                    s += tab + v._defn() + '\n'

            s += '\n' + tab + '/* Implicit variables */\n'
            for v in self._impvars:
                s += tab + v._defn() + '\n'

            s += '\n' + tab + '/* Constraints */\n'
            for c in self._congroups:
                s += c._defn(tabs=tab) + '\n'

            for c in self._constraints:
                if c._parent is None:
                    s += tab + c._defn() + '\n'

            s += '\n' + tab + '/* Objective */\n'
            if self._objective is not None:
                s += tab + '{} {} = '.format(self._sense.lower(),
                                             self._objective._name)
                s += self._objective._defn() + '; \n'

            s += '\n' + tab + '/* Solver call */\n'
            if expand:
                s += tab + 'expand;\n'

            s += tab + 'solve'
            if options.get('with', None):
                s += ' with ' + options['with']
            if options.get('relaxint', False):
                s += ' relaxint'
            if options:
                optstring = ''
                for key, value in options.items():
                    if key not in ('with', 'relaxint'):
                        optstring += ' {}={}'.format(key, value)
                if optstring:
                    s += ' /' + optstring
            s += ';\n'

            s += tab + 'ods output PrintTable=primal_out;\n'
            s += tab + 'print _var_.name _var_.lb _var_.ub _var_ _var_.rc;\n'
            s += tab + 'ods output PrintTable=dual_out;\n'
            s += tab + 'print _con_.name _con_.body _con_.dual;\n'

            if header:
                s += 'quit;\n'
        else:
            # Based on creation order
            s = ''
            if header:
                s = 'proc optmodel;\n'
            s += '/*Compact unordered format*/\n'
            allcomp = (
                self._sets +
                self._parameters +
                self._statements +
                self._vargroups +
                self._variables +
                self._impvars +
                self._congroups +
                self._constraints +
                [self._objective]
                )
            sorted_comp = sorted(allcomp, key=lambda i: i._objorder)
            for cm in sorted_comp:
                if id(cm) == id(self._objective):
                    s += '{} {} = '.format(self._sense.lower(),
                                           self._objective._name)
                    s += self._objective._defn() + '; \n'
                elif (cm._objorder > 0 and
                      not (hasattr(cm, '_shadow') and cm._shadow) and
                      not (hasattr(cm, '_parent') and cm._parent)):
                    s += cm._defn() + '\n'
            if expand:
                s += 'expand;\n'

            # Solve block
            s += 'solve'
            if options.get('with', None):
                s += ' with ' + options['with']
            if options.get('relaxint', False):
                s += ' relaxint'
            if options:
                optstring = ''
                for key, value in options.items():
                    if key not in ('with', 'relaxint'):
                        optstring += ' {}={}'.format(key, value)
                if optstring:
                    s += ' /' + optstring
            s += ';\n'
            # Output ODS tables
            s += 'ods output PrintTable=primal_out;\n'
            s += 'print _var_.name _var_.lb _var_.ub _var_ _var_.rc;\n'
            s += 'ods output PrintTable=dual_out;\n'
            s += 'print _con_.name _con_.body _con_.dual;\n'
            if header:
                s += 'quit;\n'
        return(s)

    def __str__(self):
        s = 'Model: [\n'
        s += '  Name: {}\n'.format(self._name)
        if self._session is not None:
            s += '  Session: {}:{}\n'.format(self._session._hostname,
                                             self._session._port)
        s += '  Objective: {} [{}]\n'.format(self._sense,
                                             self._objective)
        s += '  Variables ({}): [\n'.format(len(self._variables))
        for i in self._variables:
            s += '    {}\n'.format(i)
        s += '  ]\n'
        s += '  Constraints ({}): [\n'.format(len(self._constraints))
        for i in self._constraints:
            s += '    {}\n'.format(i)
        s += '  ]\n'
        s += ']'
        return s

    def __repr__(self):
        s = 'sasoptpy.Model(name=\'{}\', session={})'.format(self._name,
                                                             self._session)
        return s

    def _defn(self):
        s = 'problem {} include '.format(self._name)
        s += ' '.join([s._name for s in self._congroups])
        s += ' '.join([s._name for s in self._constraints])
        s += ' '.join([s._name for s in self._vargroups])
        s += ' '.join([s._name for s in self._variables])
        s += ';'
        return s

    def _expr(self):
        return self._to_optmodel()

    def _is_linear(self):
        '''
        Checks if the model can be written as a linear model (in MPS format)

        Returns
        -------
        boolean
            True if model does not have any nonlinear components or abstract\
            operations, False otherwise
        '''
        for c in self._constraints:
            if not c._is_linear():
                return False
        if not self._objective._is_linear():
            return False
        return True

    def upload_user_blocks(self):
        '''
        Uploads user-defined decomposition blocks to the CAS server

        Returns
        -------
        string
            CAS table name of the user-defined decomposition blocks

        Examples
        --------

        >>> userblocks = m.upload_user_blocks()
        >>> m.solve(milp={'decomp': {'blocks': userblocks}})

        '''
        sess = self._session
        blocks_dict = {}
        block_counter = 0
        if sess is None:
            print('ERROR: CAS Session is not defined for model {}.'.format(
                self._name))
            return None
        decomp_table = []
        for c in self._constraints:
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

    def test_session(self):
        '''
        Tests if the model session is defined and still active

        Returns
        -------
        string
            'CAS' for CAS sessions, 'SAS' for SAS sessions, None otherwise

        '''
        # Check if session is defined
        sess = self._session
        if sess is None:
            print('ERROR: No session is not defined for model {}.'.format(
                self._name))
            return None
        else:
            sess_type = type(sess).__name__
            if sess_type == 'CAS':
                return 'CAS'
            elif sess_type == 'SASsession':
                return 'SAS'
            else:
                print('ERROR: Unrecognized session type: {}'.format(sess_type))
                return None

    def upload_model(self, name=None, replace=True):
        '''
        Converts internal model to MPS table and upload to CAS session

        Parameters
        ----------
        name : string, optional
            Desired name of the MPS table on the server
        replace : boolean, optional
            Option to replace the existing MPS table

        Returns
        -------
        :class:`swat.cas.table.CASTable` object
            Reference to the uploaded CAS Table

        Notes
        -----

        - This method returns None if the model session is not valid.
        - Name of the table is randomly assigned if name argument is None
          or not given.
        - This method should not be used if :func:`Model.solve` is going
          to be used. :func:`Model.solve` calls this method internally.

        '''
        if self.test_session():
            # Conversion and upload
            df = self.to_frame()
            print('NOTE: Uploading the problem DataFrame to the server.')
            if name is not None:
                return self._session.upload_frame(
                    data=df, casout={'name': name, 'replace': replace})
            else:
                return self._session.upload_frame(
                    data=df, casout={'replace': replace})
        else:
            return None

    def solve(self, options={}, submit=True, name=None,
              frame=False, drop=False, replace=True, primalin=False,
              milp={}, lp={}):
        '''
        Solves the model by calling CAS or SAS optimization solvers

        Parameters
        ----------
        options : dict, optional
            A dictionary solver options
        submit : boolean, optional
            Switch for calling the solver instantly
        name : string, optional
            Name of the table name
        frame : boolean, optional
            Switch for uploading problem as a MPS DataFrame format
        drop : boolean, optional
            Switch for dropping the MPS table after solve (only CAS)
        replace : boolean, optional
            Switch for replacing an existing MPS table (only CAS and MPS)
        primalin : boolean, optional
            Switch for using initial values (only MILP)

        Returns
        -------
        :class:`pandas.DataFrame` object
            Solution of the optimization model

        Examples
        --------

        >>> m.solve()
        NOTE: Initialized model food_manufacture_1
        NOTE: Converting model food_manufacture_1 to DataFrame
        NOTE: Added action set 'optimization'.
        ...
        NOTE: Optimal.
        NOTE: Objective = 107842.59259.
        NOTE: The Dual Simplex solve time is 0.01 seconds.

        >>> m.solve(options={'maxtime': 600})

        >>> m.solve(options={'algorithm': 'ipm'})

        Notes
        -----
        * This method takes two optional arguments (milp and lp).
        * These arguments pass options to the solveLp and solveMilp CAS
          actions.
        * These arguments are not passed if the model has a SAS session.
        * Both milp and lp should be defined as dictionaries, where keys are
          option names. For example, ``m.solve(options={'maxtime': 600})`` limits
          solution time to 600 seconds.
        * See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvelp_syntax.htm&locale=en
          for a list of LP options.
        * See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvemilp_syntax.htm&locale=en
          for a list of MILP options.

        See also
        --------
        :func:`Model.solve_local`

        '''

        # Check if session is defined
        session_type = self.test_session()
        solver_func = None
        if session_type == 'CAS':
            sess = self._session
            # Check if dataframe format, if it is, pass relevant parameters
            solver_func = self.solve_on_cas
        elif session_type == 'SAS':
            sess = self._session
            solver_func = self.solve_on_mva
        else:
            return None

        # Check backward compatibility for options
        if milp:
            warnings.warn(
                'WARNING: Solve method arguments `milp` and `lp` will be '
                'deprecated, use `options` instead', DeprecationWarning)
            options.update(milp)
        if lp:
            warnings.warn(
                'WARNING: Solve method arguments `milp` and `lp` will be '
                'deprecated, use `options` instead', DeprecationWarning)
            options.update(lp)

        # Call solver based on session type
        return solver_func(
            sess, options=options, submit=submit, name=name,
            drop=drop, frame=frame, replace=replace, primalin=primalin)

    def solve_on_cas(self, session, options, submit, name,
                     frame, drop, replace, primalin):

        # Check which method will be used for solve
        session.loadactionset(actionset='optimization')

        if frame or not hasattr(session.optimization, 'runoptmodel'):
            frame = True

        # If some of the data is on the server, force using optmodel mode
        if frame and (self._sets or self._parameters):
            print('INFO: Model {} has data on server,'.format(self._name),
                  'switching to optmodel mode.')
            if hasattr(session.optimization, 'runoptmodel'):
                frame = False
            else:
                print('ERROR: Model {} has data on server'.format(self._name),
                      ' but runoptmodel action is not available.')
                return None

        if frame:
            print('NOTE: Converting model {} to DataFrame.'.format(self._name))
            # Pre-upload argument parse

            # Find problem type and initial values
            ptype = 1  # LP
            for v in self._variables:
                if v._type != sasoptpy.utils.CONT:
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
                    for v in self._variables:
                        if v._init is not None:
                            var_names.append(v._name)
                            init_values.append(v._init)
                    if (len(init_values) > 0 and
                       options.get('primalin', 1) is not None):
                        primalinTable = pd.DataFrame(
                            data={'_VAR_': var_names, '_VALUE_': init_values})
                        session.upload_frame(
                            primalinTable, casout={
                                'name': 'PRIMALINTABLE', 'replace': True})
                        options['primalin'] = 'PRIMALINTABLE'

            mps_table = self.upload_model(name, replace=replace)

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
                    dualOut={'caslib': 'CASUSER', 'name': 'dual', 'replace': True},
                    objSense=self._sense)
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
                    objSense=self._sense)

            # Parse solution
            if(response.get_tables('status')[0] == 'OK'):
                self._primalSolution = session.CASTable(
                    'primal', caslib='CASUSER').to_frame()
                self._dualSolution = session.CASTable(
                    'dual', caslib='CASUSER').to_frame()
                # Bring solution to variables
                for _, row in self._primalSolution.iterrows():
                    self._variableDict[row['_VAR_']]._value = row['_VALUE_']

                # Capturing dual values for LP problems
                if ptype == 1:
                    self._primalSolution = self._primalSolution[
                        ['_VAR_', '_VALUE_', '_R_COST_']]
                    self._primalSolution.columns = ['var', 'lb', 'ub',
                                                    'value', 'rc']
                    self._dualSolution = self._dualSolution[
                        ['_ROW_', '_ACTIVITY_', '_VALUE_']]
                    self._dualSolution.columns = ['con', 'value', 'dual']
                    for _, row in self._primalSolution.iterrows():
                        self._variableDict[row['var']]._dual = row['rc']
                    for _, row in self._dualSolution.iterrows():
                        self._constraintDict[row['con']]._dual = row['dual']
                elif ptype == 2:
                    self._primalSolution = self._primalSolution[
                        ['_VAR_', '_LBOUND_', '_UBOUND_', '_VALUE_']]
                    self._primalSolution.columns = ['var', 'lb', 'ub', 'value']
                    self._dualSolution = self._dualSolution[
                        ['_ROW_', '_ACTIVITY_']]
                    self._dualSolution.columns = ['con', 'value']

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
                self._problemSummary = response.ProblemSummary[['Label1',
                                                                'cValue1']]
                self._solutionSummary = response.SolutionSummary[['Label1',
                                                                  'cValue1']]
                self._problemSummary.set_index(['Label1'], inplace=True)
                self._problemSummary.columns = ['Value']
                self._problemSummary.index.names = ['Label']
                self._solutionSummary.set_index(['Label1'], inplace=True)
                self._solutionSummary.columns = ['Value']
                self._solutionSummary.index.names = ['Label']
                # Record status and time
                self._status = response.solutionStatus
                self._soltime = response.solutionTime
                if('OPTIMAL' in response.solutionStatus):
                    self._objval = response.objective
                    # Replace initial values with current values
                    for v in self._variables:
                        v._init = v._value
                    return self._primalSolution
                else:
                    print('NOTE: Response {}'.format(response.solutionStatus))
                    self._objval = 0
                    return None
            else:
                print('ERROR: {}'.format(response.get_tables('status')[0]))
                return None
        else:  # OPTMODEL variant

            # Find problem type and initial values
            ptype = 1  # LP
            for v in self._variables:
                if v._type != sasoptpy.utils.CONT:
                    ptype = 2
                    break

            print('NOTE: Converting model {} to OPTMODEL.'.format(self._name))
            optmodel_string = self.to_optmodel(header=False, options=options)
            if not submit:
                return optmodel_string
            print('NOTE: Submitting OPTMODEL codes to CAS server.')
            response = session.runOptmodel(
                optmodel_string,
                outputTables={
                    'names': {'solutionSummary': 'solutionSummary',
                              'problemSummary': 'problemSummary',
                              'Print1.PrintTable': 'primal',
                              'Print2.PrintTable': 'dual'}
                    }
                )

            # Parse solution
            if(response.get_tables('status')[0] == 'OK'):
                self._primalSolution = session.CASTable('primal').to_frame()
                self._primalSolution = self._primalSolution[
                    ['_VAR__NAME', '_VAR__LB', '_VAR__UB', '_VAR_', '_VAR__RC']]
                self._primalSolution.columns = ['var', 'lb', 'ub', 'value', 'rc']
                self._dualSolution = session.CASTable('dual').to_frame()
                self._dualSolution = self._dualSolution[
                    ['_CON__NAME', '_CON__BODY', '_CON__DUAL']]
                self._dualSolution.columns = ['con', 'value', 'dual']
                # Bring solution to variables
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

            self._solutionSummary = session.CASTable('solutionSummary').\
                to_sparse()[['Label1', 'cValue1']].set_index(['Label1'])
            self._problemSummary = session.CASTable('problemSummary').\
                to_sparse()[['Label1', 'cValue1']].set_index(['Label1'])

            self._solutionSummary.index.names = ['Label']
            self._solutionSummary.columns = ['Value']

            self._problemSummary.index.names = ['Label']
            self._problemSummary.columns = ['Value']

            self._status = response.solutionStatus
            self._soltime = response.solutionTime

    def solve_on_mva(self, session, options, submit, name,
                     frame, drop, replace, primalin):
        '''
        Solves the model by calling SAS 9.4 solvers

        Parameters
        ----------

        name : string, optional
            Name of the MPS table

        Examples
        --------

        >>> import saspy
        >>> import sasoptpy as so
        >>> sas = saspy.SASsession(cfgname='winlocal')
        >>> m = so.Model(name='demo', session=sas)
        >>> choco = m.add_variable(lb=0, ub=20, name='choco', vartype=so.INT)
        >>> toffee = m.add_variable(lb=0, ub=30, name='toffee')
        >>> m.set_objective(0.25*choco + 0.75*toffee, sense=so.MAX, name='profit')
        >>> m.add_constraint(15*choco + 40*toffee <= 27000, name='process1')
        >>> m.add_constraint(56.25*toffee <= 27000, name='process2')
        >>> m.add_constraint(18.75*choco <= 27000, name='process3')
        >>> m.add_constraint(12*choco + 50*toffee <= 27000, name='process4')
        >>> 
        >>> m.solve_local()
        >>> # or m.solve()
        SAS Connection established. Subprocess id is 18192
        NOTE: Initialized model demo.
        NOTE: Converting model demo to DataFrame.
        NOTE: Writing HTML5(SASPY_INTERNAL) Body file: _TOMODS1
        NOTE: The problem demo has 2 variables (0 binary, 1 integer, 0 free, 0 fixed).
        NOTE: The problem has 4 constraints (4 LE, 0 EQ, 0 GE, 0 range).
        NOTE: The problem has 6 constraint coefficients.
        NOTE: The initial MILP heuristics are applied.
        NOTE: Optimal.
        NOTE: Objective = 27.5.
        NOTE: The data set WORK.PROB_SUMMARY has 21 observations and 3 variables.
        NOTE: The data set WORK.SOL_SUMMARY has 17 observations and 3 variables.
        NOTE: There were 23 observations read from the data set WORK.MPS.
        NOTE: The data set WORK.PRIMAL_OUT has 2 observations and 8 variables.
        NOTE: The data set WORK.DUAL_OUT has 4 observations and 8 variables.
        NOTE: PROCEDURE OPTMILP used (Total process time):
        real time           0.07 seconds
        cpu time            0.04 seconds
        SAS Connection terminated. Subprocess id was 18192

        Notes
        -----

        - If the session of a model is a :class:`saspy.SASsession` object,
          then :func:`Model.solve` calls this method internally.
        - To use this method, you need to have saspy installed on your
          Python environment.
        - This function is experimental.
        - Unlike :func:`Model.solve`, this method does not accept LP and MILP
          options yet.

        See also
        --------
        :func:`Model.solve`

        '''

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

        if frame:

            # Get the MPS data
            df = self.to_frame()

            # Prepare for the upload
            for f in ['Field4', 'Field6']:
                df[f] = df[f].replace('', np.nan)
            df['_id_'] = df['_id_'].astype('int')
            df[['Field4', 'Field6']] = df[['Field4', 'Field6']].astype(float)

            # Upload MPS table
            try:
                session.df2sd(df, table=name, keep_outer_quotes=True)
            except:
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
                if v._type != sasoptpy.utils.CONT:
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
            self._problemSummary = self._problemSummary[['Label1', 'cValue1']]
            self._problemSummary.set_index(['Label1'], inplace=True)
            self._problemSummary.columns = ['Value']
            self._problemSummary.index.names = ['Label']

            # Get Solution Summary
            self._solutionSummary = session.sd2df('SOL_SUMMARY')
            self._solutionSummary.replace(np.nan, '', inplace=True)
            self._solutionSummary = self._solutionSummary[['Label1', 'cValue1']]
            self._solutionSummary.set_index(['Label1'], inplace=True)
            self._solutionSummary.columns = ['Value']
            self._solutionSummary.index.names = ['Label']

            # Parse solutions
            for _, row in self._primalSolution.iterrows():
                self._variableDict[row['_VAR_']]._value = row['_VALUE_']

            return self._primalSolution

        else: # OPTMODEL version

            # Find problem type and initial values
            ptype = 1  # LP
            for v in self._variables:
                if v._type != sasoptpy.utils.CONT:
                    ptype = 2
                    break

            print('NOTE: Converting model {} to OPTMODEL.'.format(self._name))
            optmodel_string = self.to_optmodel(header=True, options=options)
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
