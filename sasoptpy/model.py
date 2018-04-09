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
    session : :class:`swat.cas.connection.CAS` object, optional
        CAS Session object

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

    def __init__(self, name, session=None, abstract=False):
        self._name = sasoptpy.utils.check_name(name, 'model')
        self._session = session
        self._abstract = abstract
        self._variables = []
        self._constraints = []
        self._vargroups = []
        self._congroups = []
        self._objective = sasoptpy.components.Expression()
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
        self._impliedvars = []
        self._statements = []
        # self._events = [] 
        sasoptpy.utils.register_name(name, self)
        print('NOTE: Initialized model {}'.format(name))

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
        :func:`sasoptpy.Model.include`
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
                sasoptpy.utils.register_name(name, c)
            self._constraintDict[c._name] = c
            for v in c._linCoef:
                if v != 'CONST':
                    for vi in list(c._linCoef[v]['ref']):
                        if isinstance(vi, sasoptpy.components.Variable):
                            vi._tag_constraint(c)
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
            name = sasoptpy.utils.check_name(name, 'param')
            p = sasoptpy.data.Parameter(name, keys=(), init=init)
            self._parameters.append(p)
            return p['']
        else:
            keylist = list(argv)
            name = sasoptpy.utils.check_name(name, 'param')
            p = sasoptpy.data.Parameter(name, keys=keylist, init=init)
            self._parameters.append(p)
            return p

    def add_implied_variable(self, argv=None, name=None):
        '''
        Adds an implied variable to the model
        '''
        iv = sasoptpy.data.ExpressionDict(name=name)
        if argv:
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

        self._impliedvars.append(iv)
        return iv

    def read_data(self, table, option='', keyset=None, key=[], params=[]):
        '''
        Reads a CASTable into PROC OPTMODEL sets
        '''

        # Reading key
        if keyset is not None:
            if key != []:
                for i, k in enumerate(keyset):
                    k._colname = key[i]

        # Reading parameters
        for p in params:
            p.setdefault('column', None)
            p.setdefault('index', None)
            p['param']._set_loop(table, keyset, p['column'], p['index'])

        s = 'read data {} {} into '.format(table.name, option)
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
        for p in params:
            s += p['param']._to_read_data()
        s += ';'
        self._statements.append(s)

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
        :func:`sasoptpy.Model.drop_variables`
        :func:`sasoptpy.Model.drop_constraint`
        :func:`sasoptpy.Model.drop_constraints`

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
        :func:`sasoptpy.Model.drop_constraints`
        :func:`sasoptpy.Model.drop_variable`
        :func:`sasoptpy.Model.drop_variables`

        '''
        try:
            del self._constraintDict[constraint._name]
            for i, c in enumerate(self._constraints):
                if c._name == constraint._name:
                    del self._constraints[i]
        except KeyError:
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
        :func:`sasoptpy.Model.drop_variable`
        :func:`sasoptpy.Model.drop_constraint`
        :func:`sasoptpy.Model.drop_constraints`

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
        :func:`sasoptpy.Model.drop_constraints`
        :func:`sasoptpy.Model.drop_variable`
        :func:`sasoptpy.Model.drop_variables`

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
          :func:`sasoptpy.Model.add_variable` and
          :func:`sasoptpy.Model.add_constraint`.
        * Including a model causes all variables and constraints inside the
          original model to be included.
        '''
        for i, c in enumerate(argv):
            if isinstance(c, sasoptpy.components.Variable):
                self.add_variable(var=c)
            elif isinstance(c, sasoptpy.components.VariableGroup):
                for v in c._vardict:
                    self.add_variable(var=c._vardict[v])
            elif isinstance(c, sasoptpy.components.Constraint):
                self.add_constraint(c)
            elif isinstance(c, sasoptpy.components.ConstraintGroup):
                for cn in c._condict:
                    self.add_constraint(c._condict[cn])
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
            sasoptpy.utils.register_name(name, self._objective)
            self._objective._name = name
        self._sense = sense
        self._objective._temp = False
        return self._objective

    def get_objective(self):
        '''
        Returns the objective function as an :class:`Expression` object

        Returns
        -------
        :class:`Expression` : Objective function

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
        list : A list of :class:`sasoptpy.components.Constraint` objects

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

    def get_variables(self):
        '''
        Returns a list of variables

        Returns
        -------
        list : A list of :class:`sasoptpy.components.Variable` objects

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

    def get_problem_summary(self):
        '''
        Returns the problem summary table to the user

        Returns
        -------
        :class:`swat.dataframe.SASDataFrame` object
            Problem summary obtained after :func:`sasoptpy.Model.solve`

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
        if vtype == 'Primal':
            return self._primalSolution
        elif vtype == 'Dual':
            return self._dualSolution
        else:
            return None

    def set_session(self, session):
        '''
        Sets the CAS session for model

        Parameters
        ----------
        session : :class:`swat.cas.connection.CAS`
            CAS Session
        '''
        from swat import CAS
        if type(session) == CAS:
            self._session = session
        else:
            print('WARNING: Session is not added, not a CAS object.')

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
        :func:`sasoptpy.Constraint.update_var_coef`

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
        :func:`sasoptpy.Model.get_solution`

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
        * This method is called inside :func:`sasoptpy.Model.solve`.
        '''
        print('NOTE: Converting model {} to DataFrame'.format(self._name))
        self._id = 1
        if(len(self._datarows) > 0):  # For future reference
            # take a copy?
            self._mpsmode = 1
            self._datarows = []
        else:
            self._datarows = []
        # Check if objective has a constant field, if so hack using a variable
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
            else:
                current_row = ['', v._name, self._objective._name, 0.0]
                f5 = 1
            for cn in v._cons:
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
            if v._lb is not 0 and v._lb is not None:
                if v._ub == inf and v._lb == -inf:
                    self._append_row(['FR', 'BND', v._name, '', '', ''])
                else:
                    self._append_row(['LO', 'BND', v._name, v._lb, '', ''])
            if v._ub != inf and v._ub is not None and not\
               (v._type is sasoptpy.utils.BIN and v._ub == 1):
                self._append_row(['UP', 'BND', v._name, v._ub, '', ''])
            if v._type is sasoptpy.utils.BIN:
                self._append_row(['BV', 'BND', v._name, '1.0', '', ''])
            if v._lb is 0 and v._type is sasoptpy.utils.INT:
                self._append_row(['LO', 'BND', v._name, v._lb, '', ''])
        self._append_row(['ENDATA', '', '', float(0), '', float(0)])
        mpsdata = pd.DataFrame(data=self._datarows,
                               columns=['Field1', 'Field2', 'Field3', 'Field4',
                                        'Field5', 'Field6', '_id_'])
        return mpsdata

    def _to_optmodel(self, header=True, expand=False):

        if not self._abstract:
            print('ERROR: Model is not abstract, can\'t produce OPTMODEL code')
            return ''

        s = ''

        if header:
            s = 'proc optmodel;\n'

        tab = '   '

        s += tab + '/* Sets */\n'
        for i in self._sets:
            s += tab + i._to_optmodel() + '\n'

        s += '\n' + tab + '/* Parameters */\n'
        for i in self._parameters:
            s += i._to_optmodel(tab) + '\n'

        s += '\n' + tab + '/* Statements */\n'
        for i in self._statements:
            s += tab + i + '\n'

        s += '\n' + tab + '/* Variables */\n'
        for i in self._vargroups:
            s += i._to_optmodel(tabs=tab) + '\n'

        for v in self._variables:
            if v._parent is None:
                s += tab + v._to_optmodel() + '\n'

        s += '\n' + tab + '/* Implied variables */\n'
        for v in self._impliedvars:
            s += tab + v._to_optmodel() + '\n'

        s += '\n' + tab + '/* Constraints */\n'
        for c in self._congroups:
            s += tab + c._to_optmodel() + '\n'

        for c in self._constraints:
            if c._parent is None:
                s += tab + c._to_optmodel() + '\n'

        s += '\n' + tab + '/* Objective */\n'
        if self._objective is not None:
            s += tab + '{} {} = '.format(self._sense, self._objective._name)
            s += self._objective._to_optmodel() + '; \n'

        s += '\n' + tab + '/* Solver call */\n'
        if expand:
            s += tab + 'expand;\n'
        s += tab + 'solve;\n'

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
        # Check if session is defined
        sess = self._session
        if sess is None:
            print('ERROR: CAS Session is not defined for model {}.'.format(
                self._name))
            return False
        else:
            return True

    def upload_model(self, name=None, replace=True):
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

    def remote_solve(self):
        # Check if session is defined
        if self.test_session():
            sess = self._session
        else:
            return None
        sess.loadactionset(actionset='optimization')
        optmodel_string = self._to_optmodel(0)
        sess.runOptmodel(optmodel_string)

    def local_solve(self, session, name='MPS'):
        '''
        **Experimental** Solves the model by calling SAS 9.4 solvers

        Parameters
        ----------
        session : :class:`saspy.SASsession` object
            SAS session
        name : string, optional
            Name of the MPS table

        Notes
        -----

        - To use this function, you need to have saspy installed on your
          Python environment
        - This function is experimental and may not work reliable

        '''

        try:
            import saspy as sp
        except ImportError:
            print('ERROR: saspy cannot be imported.')
            return False

        if not isinstance(session, sp.SASsession):
            print('ERROR: session= argument is not a valid SAS session.')
            return False

        # Get the MPS data
        df = self.to_frame()

        # Prepare for the upload
        for f in ['Field1', 'Field2', 'Field3', 'Field5']:
            df[f] = df[f].replace('', '.')
        for f in ['Field4', 'Field6']:
            df[f] = df[f].replace('', np.nan)
        df['_id_'].astype('int')

        # Upload MPS table
        session.df2sd(df, table=name)

        # Find problem type and initial values
        ptype = 1  # LP
        for v in self._variables:
            if v._type != sasoptpy.utils.CONT:
                ptype = 2
                break

        if ptype == 1:
            c = session.submit("""
            proc optlp data = {}
               primalout  = primal_out
               dualout    = dual_out;
            run;
            """.format(name))
        else:
            c = session.submit("""
            proc optmilp data = {}
               primalout  = primal_out
               dualout    = dual_out;
            run;
            """.format(name))

        self._primalSolution = session.sd2df('PRIMAL_OUT')
        self._dualSolution = session.sd2df('DUAL_OUT')
        print(c['LOG'])

        # Parse solutions
        for _, row in self._primalSolution.iterrows():
            self._variableDict[row['_VAR_']]._value = row['_VALUE_']

        return True

    def solve(self, milp={}, lp={}, name=None, drop=True, replace=True,
              primalin=False):
        '''
        Solves the model by calling CAS optimization solvers

        Parameters
        ----------
        milp : dict, optional
            A dictionary of MILP options for the solveMilp CAS Action
        lp : dict, optional
            A dictionary of LP options for the solveLp CAS Action
        name : string, optional
            Name of the table name on CAS Server
        drop : boolean, optional
            Switch for dropping the MPS table on CAS Server after solve
        replace : boolean, optional
            Switch for replacing an existing MPS table on CAS Server
        primalin : boolean, optional
            Switch for using initial values (for MIP only)

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
        NOTE: Data length = 419 rows
        NOTE: Conversion to MPS =   0.0010 secs
        NOTE: Upload to CAS time =  0.1420 secs
        NOTE: Solution parse time = 0.2500 secs
        NOTE: Server solve time =   0.1168 secs

        >>> m.solve(milp={'maxtime': 600})

        >>> m.solve(lp={'algorithm': 'ipm'})

        Notes
        -----
        * This method takes two optional arguments (milp and lp).
        * These arguments pass options to the solveLp and solveMilp CAS
          actions.
        * Both milp and lp should be defined as dictionaries, where keys are
          option names. For example, ``m.solve(milp={'maxtime': 600})`` limits
          solution time to 600 seconds.
        * See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvelp_syntax.htm&locale=en
          for a list of LP options.
        * See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvemilp_syntax.htm&locale=en
          for a list of MILP options.

        '''

        if self._abstract:
            self.remote_solve()
            return None

        # Check if session is defined
        if self.test_session():
            sess = self._session
        else:
            return None

        # Pre-upload argument parse
        opt_args = lp
        if bool(lp):
            self._lp_opts = lp
        if bool(milp):
            self._milp_opts = milp
            opt_args = milp

        # Decomp check
        user_blocks = None
        if 'decomp' in opt_args:
            if 'method' in opt_args['decomp']:
                if opt_args['decomp']['method'] == 'user':
                    user_blocks = self.upload_user_blocks()
                    opt_args['decomp'] = {'blocks': user_blocks}

        # Find problem type and initial values
        ptype = 1  # LP
        for v in self._variables:
            if v._type != sasoptpy.utils.CONT:
                ptype = 2
                break

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
                   opt_args.get('primalin', 1) is not None):
                    primalinTable = pd.DataFrame(data={'_VAR_': var_names,
                                                       '_VALUE_': init_values})
                    sess.upload_frame(primalinTable,
                                      casout={'name': 'PRIMALINTABLE',
                                              'replace': True})
                    opt_args['primalin'] = 'PRIMALINTABLE'

        mps_table = self.upload_model(name, replace=replace)
        sess.loadactionset(actionset='optimization')

        if ptype == 1:
            response = sess.solveLp(data=mps_table.name,
                                    **self._lp_opts,
                                    primalOut={'caslib': 'CASUSER',
                                               'name': 'primal',
                                               'replace': True},
                                    dualOut={'caslib': 'CASUSER',
                                             'name': 'dual', 'replace': True},
                                    objSense=self._sense)
        elif ptype == 2:
            response = sess.solveMilp(data=mps_table.name,
                                      **self._milp_opts,
                                      primalOut={'caslib': 'CASUSER',
                                                 'name': 'primal',
                                                 'replace': True},
                                      dualOut={'caslib': 'CASUSER',
                                               'name': 'dual',
                                               'replace': True},
                                      objSense=self._sense)

        # Parse solution
        if(response.get_tables('status')[0] == 'OK'):
            self._primalSolution = sess.CASTable('primal',
                                                 caslib='CASUSER').to_frame()
            self._dualSolution = sess.CASTable('dual',
                                               caslib='CASUSER').to_frame()
            # Bring solution to variables
            for _, row in self._primalSolution.iterrows():
                self._variableDict[row['_VAR_']]._value = row['_VALUE_']

            # Capturing dual values for LP problems
            if ptype == 1:
                for _, row in self._primalSolution.iterrows():
                    self._variableDict[row['_VAR_']]._dual = row['_R_COST_']
                for _, row in self._dualSolution.iterrows():
                    self._constraintDict[row['_ROW_']]._dual = row['_VALUE_']

        # Drop tables
        if drop:
            sess.table.droptable(table=mps_table.name)
            if user_blocks is not None:
                sess.table.droptable(table=user_blocks)
            if primalin:
                sess.table.droptable(table='PRIMALINTABLE')

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
