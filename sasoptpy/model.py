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

"""
Model includes :class:`Model` class, the main structure of an opt. model

"""


import inspect
from math import inf
from types import GeneratorType
import warnings

import numpy as np
import pandas as pd

import sasoptpy.components
import sasoptpy.utils


class Model:
    """
    Creates an optimization model

    Parameters
    ----------
    name : string
        Name of the model
    session : :class:`swat.cas.connection.CAS` or \
:class:`saspy.SASsession`, optional
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
    """

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
        self._objval = None
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
        self._objorder = sasoptpy.utils.register_name(name, self)
        self.response = None
        print('NOTE: Initialized model {}.'.format(name))

    def __eq__(self, other):
        if not isinstance(other, sasoptpy.Model):
            warnings.warn('Cannot compare Model object with {}'.
                          format(type(other)), RuntimeWarning, stacklevel=2)
            return False
        return super().__eq__(other)

    def add_variable(self, var=None, vartype=sasoptpy.utils.CONT, name=None,
                     lb=-inf, ub=inf, init=None):
        """
        Adds a new variable to the model

        New variables can be created via this method or existing variables
        can be added to the model.

        Parameters
        ----------
        var : Variable, optional
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
        var : Variable
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
        :class:`Variable`, :func:`Model.include`
        """
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
        """
        Adds a group of variables to the model

        Parameters
        ----------
        argv : list, dict, :class:`pandas.Index`
            Loop index for variable group
        vg : VariableGroup, optional
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
        :class:`VariableGroup`, :meth:`Model.include`

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

        """
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
        """
        Adds a single constraint to the model

        Parameters
        ----------
        c : Constraint
            Constraint to be added to the model
        name : string, optional
            Name of the constraint

        Returns
        -------
        c : Constraint
            Reference to the constraint

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

        See also
        --------
        :class:`Constraint`, :meth:`Model.include`

        """
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
        """
        Adds a set of constraints to the model

        Parameters
        ----------
        argv : Generator-type object
            List of constraints as a Generator-type object
        cg : ConstraintGroup, optional
            An existing list of constraints if an existing group is being added
        name : string, optional
            Name for the constraint group and individual constraint prefix

        Returns
        -------
        cg : ConstraintGroup
            Reference to the ConstraintGroup

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

        See also
        --------
        :class:`ConstraintGroup`, :meth:`Model.include`

        """
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

    def add_set(self, name, init=None, value=None, settype=['num']):
        """
        Adds a set to the model

        Parameters
        ----------
        name : string, optional
            Name of the set
        init : :class:`Set`, optional
            Initial value of the set
        value : list, float, optional
            Exact value of the set
        settype : list, optional
            Types of the set, a list consists of 'num' and 'str' values

        Examples
        --------

        >>> I = m.add_set(name='I')
        >>> print(I._defn())
        set I;

        >>> J = m.add_set(name='J', settype=['str'])
        >>> print(J._defn())
        set <str> J;

        >>> N = m.add_parameter(name='N', init=4)
        >>> K = m.add_set(name='K', init=so.exp_range(1, N))
        >>> print(K._defn())
        set K = 1..N;

        """
        newset = sasoptpy.data.Set(name, init=init, value=value, settype=settype)
        self._sets.append(newset)
        return newset

    def add_parameter(self, *argv, name=None, init=None, value=None, p_type=None):
        """
        Adds a parameter to the model

        Parameters
        ----------
        argv : :class:`Set`, optional
            Key set of the parameter
        name : string, optional
            Name of the parameter
        init : float or expression, optional
            Initial value of the parameter
        p_type : string, optional
            Type of the parameter, 'num' for floats or 'str' for strings

        Examples
        --------

        >>> I = m.add_set(name='I')
        >>> a = m.add_parameter(I, name='a', init=5)
        >>> print(a._defn())
        num a {I} init 5 ;

        """
        if len(argv) == 0:
            p = sasoptpy.data.Parameter(
                name, keys=(), init=init, value=value, p_type=p_type)
            self._parameters.append(p)
            return p['']
        else:
            keylist = list(argv)
            p = sasoptpy.data.Parameter(
                name, keys=keylist, init=init, value=value, p_type=p_type)
            self._parameters.append(p)
            return p

    def add_implicit_variable(self, argv=None, name=None):
        """
        Adds an implicit variable to the model

        Parameters
        ----------
        argv : Generator-type object
            Generator object where each item is an entry
        name : string, optional
            Name of the implicit variable

        Examples
        --------

        >>> x = m.add_variables(range(5), name='x')
        >>> y = m.add_implicit_variable((
        >>>     x[i] + 2 * x[i+1] for i in range(4)), name='y')
        >>> print(y[2])
        x[2] + 2 * x[3]

        >>> I = m.add_set(name='I')
        >>> z = m.add_implicit_variable((x[i] * 2 + 2 for i in I), name='z')
        >>> print(z._defn())
        impvar z {i_1 in I} = 2 * x[i_1] + 2;


        Notes
        -----

        - Based on whether generated by a regular expression or an abstract
          one, implicit variables may appear in generated OPTMODEL codes.

        """
        iv = sasoptpy.data.ImplicitVar(argv=argv, name=name)
        self._impvars.append(iv)
        return iv

    def add_statement(self, statement, after_solve=False):
        """
        Adds a PROC OPTMODEL statement to the model

        Parameters
        ----------
        statement : Expression or string
            Statement object
        after_solve : boolean, optional
            Option for putting the statement after 'solve' declaration

        Examples
        --------

        >>> I = m.add_set(name='I')
        >>> x = m.add_variables(I, name='x', vartype=so.INT)
        >>> a = m.add_parameter(I, name='a')
        >>> c = m.add_constraints((x[i] <= 2 * a[i] for i in I), name='c')
        >>> m.add_statement('print x;', after_solve=True)
        >>> print(m.to_optmodel())
        proc optmodel;
        min m_obj = 0;
        set I;
        var x {I} integer >= 0;
        num a {I};
        con c {i_1 in I} : x[i_1] - 2.0 * a[i_1] <= 0;
        solve;
        print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
        print _con_.name _con_.body _con_.dual;
        print x;
        quit;


        Notes
        -----

        - If the statement string includes 'print', then it is automatically
          placed after solve.
        - The first parameter, `statement` could be a Statement object when internally used.

        """
        if isinstance(statement, sasoptpy.data.Statement):
            self._statements.append(statement)
        elif isinstance(statement, sasoptpy.components.Expression):
            self._statements.append(
                sasoptpy.data.Statement(
                    str(statement), after_solve=after_solve))
        elif isinstance(statement, str):
            if 'print' in statement and not after_solve:
                print('WARNING: Moving print statement after solve.')
                after_solve = True
            self._statements.append(
                sasoptpy.data.Statement(statement, after_solve=after_solve))

    def read_data(self, table, key_set, key_cols=None, option='', params=None):
        """
        Reads a CASTable into PROC OPTMODEL and adds it to the model

        Parameters
        ----------
        table : :class:`swat.cas.table.CASTable`
            The CAS table to be read to sets and parameters
        key_set : :class:`Set`
            Set object to be read as the key (index)
        key_cols : list or string, optional
            Column names of the key columns
        option : string, optional
            Additional options for read data command
        params : list, optional
            A list of dictionaries where each dictionary represent parameters

        Notes
        -----

        - This function is intended to be used internally.
        - It imitates the ``read data`` statement of PROC OPTMODEL.
        - This function is still under development and subject to change.
        - `key_cols` parameters should be a list. When passing
          a single item, string type can be used instead.
        - Values inside each dictionary in ``params`` list should be as follows:
          
          - **param** : :class:`Parameter`

            Paramter object, whose index is the same as table key

          - **column** : string, optional

            Column name to be read

          - **index** : list, optional

            List of sets if the parameter has to be read in a loop


        See also
        --------
        :func:`sasoptpy.utils.read_data`

        Examples
        --------

        >>> table = session.upload_frame(df, casout='df')
        >>> item = m.add_set(name='set_item')
        >>> value = m.add_parameter(item, name='value')
        >>> m.read_data(table, key_set=item, key_cols=['items'],\
params=[{'param': value, 'column': 'value'}])
        >>> print(m.to_optmodel())
        proc optmodel;
        min m_obj = 0;
        set set_item;
        num value {set_item};
        read data df into set_item=[items] value;
        solve;
        print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
        print _con_.name _con_.body _con_.dual;
        quit;

        """

        if key_cols is None:
            key_cols = []
        if params is None:
            params = []

        s = sasoptpy.utils.read_data(
            table=table, key_set=key_set, key_cols=key_cols, option=option,
            params=params)
        self._statements.append(s)

    def read_table(self, table, key=['_N_'], key_type=['num'], key_name=None,
                   columns=None, col_types=None, col_names=None,
                   upload=False, casout=None):
        """
        Reads a CAS Table or pandas DataFrame into the model

        Parameters
        ----------
        table : :class:`swat.cas.table.CASTable`, :class:`pandas.DataFrame`\
                or string
            Pointer to CAS Table (server data, CASTable),\
            DataFrame (local data) or\
            the name of the table at execution (server data, string)
        key : list, optional
            List of key columns (for CASTable) or index columns (for DataFrame)
        key_type : list or string, optional
            A list of column types consists of 'num' or 'str' values
        key_name : string, optional
            Name of the key set
        columns : list, optional
            List of columns to read into parameters
        col_types : dict, optional
            Dictionary of column types
        col_names : dict, optional
            Dictionary of column names
        upload : boolean, optional
            Option for uploading a local data to CAS server first
        casout : string or dict, optional
            Casout options if data is uploaded

        Returns
        -------
        objs : tuple
            A tuple where first element is the key (index) and second element\
            is a list of requested columns

        Notes
        -----

        - This method can take either a :class:`swat.cas.table.CASTable`,
          a :class:`pandas.DataFrame` or name of the data set as a string as
          the first argument.
        - If the model is running in saspy or MPS mode, then the data is read
          to client from the CAS server.
        - If the model is running in OPTMODEL mode, then this method generates
          the corresponding optmodel code.
        - When table is a CASTable object, since the actual data is stored
          on the CAS server, some of the functionalities may be limited.
        - For the local data, ``upload`` argument can be passed for performance
          improvement.
        - See :meth:`swat.CAS.upload_frame` and ``table.loadtable`` CAS action
          for ``casout`` options.

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

        """

        objs = sasoptpy.utils.read_table(
            table=table, session=self._session,
            key=key, key_type=key_type, key_name=key_name,
            columns=columns, col_types=col_types, col_names=col_names,
            upload=upload, casout=casout, ref=True)

        if isinstance(objs[0], sasoptpy.data.Set):
            self._sets.append(objs[0])
        for i in objs[1]:
            if isinstance(i, sasoptpy.data.Parameter):
                self._parameters.append(i)
        if objs[2] is not None and isinstance(objs[2],
                                              sasoptpy.data.Statement):
                self._statements.append(objs[2])

        if objs[1]:
            return (objs[0], objs[1])
        else:
            return objs[0]

    def drop_variable(self, variable):
        """
        Drops a variable from the model

        Parameters
        ----------
        variable : Variable
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

        """
        for i, v in enumerate(self._variables):
            if id(variable) == id(v):
                del self._variables[i]
                return

    def drop_constraint(self, constraint):
        """
        Drops a constraint from the model

        Parameters
        ----------
        constraint : Constraint
            The constraint to be dropped from the model

        Examples
        --------

        >>> c1 = m.add_constraint(2 * x + y <= 15, name='c1')
        >>> print(m.get_constraint('c1'))
        2 * x  +  y  <=  15
        >>> m.drop_constraint(c1)
        >>> print(m.get_constraint('c1'))
        None

        See also
        --------
        :func:`Model.drop_constraints`
        :func:`Model.drop_variable`
        :func:`Model.drop_variables`

        """
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
        """
        Drops a variable group from the model

        Parameters
        ----------
        variables : VariableGroup
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

        """
        for v in variables:
            self.drop_variable(v)
        if variables in self._vargroups:
            self._vargroups.remove(variables)

    def drop_constraints(self, constraints):
        """
        Drops a constraint group from the model

        Parameters
        ----------
        constraints : ConstraintGroup
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

        """
        for c in constraints:
            self.drop_constraint(c)
        if constraints in self._congroups:
            self._congroups.remove(constraints)

    def include(self, *argv):
        """
        Adds existing variables and constraints to a model

        Parameters
        ----------
        argv : :class:`Model`, :class:`Variable`, :class:`Constraint`,\
            :class:`VariableGroup`, :class:`ConstraintGroup`,\
            :class:`Set`, :class:`Parameter`, :class:`Statement`,\
            :class:`ImplicitVar`
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

        Adding an existing model (including all of its elements)

        >>> new_model = so.Model(name='new_model')
        >>> new_model.include(m)

        Notes
        -----
        * Including a model causes all variables and constraints inside the
          original model to be included.

        """
        for _, c in enumerate(argv):
            if c is None or type(c) == pd.DataFrame or type(c) == pd.Series:
                continue
            elif isinstance(c, sasoptpy.components.Variable):
                self.add_variable(var=c)
            elif isinstance(c, sasoptpy.components.VariableGroup):
                self.add_variables(vg=c)
            elif isinstance(c, sasoptpy.components.Constraint):
                self.add_constraint(c)
            elif isinstance(c, sasoptpy.components.ConstraintGroup):
                self.add_constraints(argv=None, cg=c)
            elif isinstance(c, sasoptpy.data.Set):
                self._sets.append(c)
            elif isinstance(c, sasoptpy.data.Parameter):
                self._parameters.append(c)
            elif isinstance(c, sasoptpy.data.Statement):
                self._statements.append(c)
            elif isinstance(c, sasoptpy.data.ExpressionDict):
                self._impvars.append(c)
            elif isinstance(c, list):
                for s in c:
                    self.include(s)
            elif isinstance(c, Model):
                self._sets.extend(s for s in c._sets)
                self._parameters.extend(s for s in c._parameters)
                self._statements.extend(s for s in c._statements)
                self._impvars.extend(s for s in c._impvars)
                for s in c._vargroups:
                    self._vargroups.append(s)
                    for subvar in s:
                        self._variables.append(subvar)
                for s in c._variables:
                    self._variables.append(s)
                for s in c._congroups:
                    self._congroups.append(s)
                for s in c._constraints:
                    self._constraints.append(s)
                self._objective = c._objective

    def set_objective(self, expression, sense=None, name=None, multiobj=False):
        """
        Sets the objective function for the model

        Parameters
        ----------
        expression : Expression
            The objective function as an Expression
        sense : string, optional
            Objective value direction, 'MIN' or 'MAX'
        name : string, optional
            Name of the objective value
        multiobj : boolean, optional
            Option for keeping the objective function when working with multiple objectives

        Returns
        -------
        objective : Expression
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

        >>> m.set_objective(2 * x + y, sense=so.MIN, name='f1', multiobj=True)
        >>> m.set_objective( (x - y) ** 2, sense=so.MIN, name='f2', multiobj=True)
        >>> print(m.to_optmodel(options={'with': 'lso', 'obj': (f1, f2)}))
        proc optmodel;
        var x;
        var y;
        min f1 = 2 * x + y;
        min f2 = (x - y) ^ (2);
        solve with lso obj (f1 f2);
        print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
        print _con_.name _con_.body _con_.dual;
        quit;

        Notes
        -----
        - Default objective sense is minimization (MIN)
        - This method replaces the existing objective of the model. When working with multiple objectives, use the
          `multiobj` parameter and use 'obj' option in :meth:`Model.solve` and :meth:`Model.to_optmodel` methods.

        """
        if sense is None:
            sense = sasoptpy.utils.MIN

        self._linCoef = {}
        if isinstance(expression, sasoptpy.components.Expression):
            if name is not None:
                obj = expression.copy()
            else:
                obj = sasoptpy.utils.get_mutable(expression)
        else:
            obj = sasoptpy.components.Expression(expression)

        if self._objective is not None and self._objective._keep:
            st = '{} {} = '.format(self._sense.lower(), self._objective._name)
            st += self._objective._defn() + ';'
            self.add_statement(st)

        if multiobj:
            obj._keep = True


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
        """
        Returns the objective function as an :class:`Expression` object

        Returns
        -------
        objective : Expression
            Objective function

        Examples
        --------

        >>> m.set_objective(4 * x - 5 * y, name='obj')
        >>> print(repr(m.get_objective()))
        sasoptpy.Expression(exp =  4.0 * x  -  5.0 * y , name='obj')

        """
        return self._objective

    def get_objective_value(self):
        """
        Returns the optimal objective value, if it exists

        Returns
        -------
        objective_value : float
            Objective value at current solution

        Examples
        --------

        >>> m.solve()
        >>> print(m.get_objective_value())
        42.0

        Notes
        -----

        - This method should be used for getting the objective value after
          solve. Using :code:`m.get_objective().get_value()` actually evaluates
          the expression using optimal variable values. This may not be
          available for nonlinear expressions.

        """
        if self._objval:
            return round(self._objval, 6)
        elif self.response:
            return round(self.response.objective, 6)
        else:
            try:
                return self._objective.get_value()
            except TypeError:
                print('ERROR: Cannot evaluate function at this time.')
                return 0

    def get_constraint(self, name):
        """
        Returns the reference to a constraint in the model

        Parameters
        ----------
        name : string
            Name of the constraint requested

        Returns
        -------
        constraint : Constraint
            Reference to the constraint

        Examples
        --------

        >>> m.add_constraint(2 * x + y <= 15, name='c1')
        >>> print(m.get_constraint('c1'))
        2.0 * x  +  y  <=  15

        """
        return self._constraintDict.get(name)

    def get_constraints(self):
        """
        Returns a list of constraints in the model

        Returns
        -------
        constraints : list
            A list of Constraint objects

        Examples
        --------

        >>> m.add_constraint(x[0] + y <= 15, name='c1')
        >>> m.add_constraints((2 * x[i] - y >= 1 for i in [0, 1]), name='c2')
        >>> print(m.get_constraints())
        [sasoptpy.Constraint( x[0]  +  y  <=  15, name='c1'),
         sasoptpy.Constraint( 2.0 * x[0]  -  y  >=  1, name='c2_0'),
         sasoptpy.Constraint( 2.0 * x[1]  -  y  >=  1, name='c2_1')]

        """
        return self._constraints

    def get_variable(self, name):
        """
        Returns the reference to a variable in the model

        Parameters
        ----------
        name : string
            Name or key of the variable requested

        Returns
        -------
        variable : Variable
            Reference to the variable

        Examples
        --------

        >>> m.add_variable(name='x', vartype=so.INT, lb=3, ub=5)
        >>> var1 = m.get_variable('x')
        >>> print(repr(var1))
        sasoptpy.Variable(name='x', lb=3, ub=5, vartype='INT')

        """
        for v in self._variables:
            if v._name == name:
                return v
        return None

    def get_variables(self):
        """
        Returns a list of variables

        Returns
        -------
        variables : list
            List of variables in the model

        Examples
        --------

        >>> x = m.add_variables(2, name='x')
        >>> y = m.add_variable(name='y')
        >>> print(m.get_variables())
        [sasoptpy.Variable(name='x_0',  vartype='CONT'),
         sasoptpy.Variable(name='x_1',  vartype='CONT'),
         sasoptpy.Variable(name='y',  vartype='CONT')]

        """
        return self._variables

    def get_variable_coef(self, var):
        """
        Returns the objective value coefficient of a variable

        Parameters
        ----------
        var : Variable or string
            Variable whose objective value is requested or its name

        Returns
        -------
        coef : float
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

        """
        if isinstance(var, sasoptpy.components.Variable):
            varname = var._name
        else:
            varname = var
        if varname in self._objective._linCoef:
            return self._objective._linCoef[varname]['val']
        else:
            return 0

    def get_variable_value(self, var=None, name=None):
        """
        Returns the value of a variable.

        Parameters
        ----------
        var : :Variable, optional
            Variable object
        name : string, optional
            Name of the variable

        Notes
        -----
        - It is possible to get a variable's value using
          :func:`Variable.get_value` method, if the variable is not abstract.
        - This method is a wrapper around :func:`Variable.get_value` and an
          overlook function for model components
        """
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
                    if (row['var'] == name and
                            ('solution' in self._primalSolution and
                             row['solution'] == 1) or
                            'solution' not in self._primalSolution):
                        return row['value']
        return None

    def get_problem_summary(self):
        """
        Returns the problem summary table to the user

        Returns
        -------
        ps : :class:`swat.dataframe.SASDataFrame`
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

        """
        return self._problemSummary

    def get_solution_summary(self):
        """
        Returns the solution summary table to the user

        Returns
        -------
        ss : :class:`swat.dataframe.SASDataFrame`
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

        """
        return self._solutionSummary

    def get_solution(self, vtype='Primal', solution=None, pivot=False):
        """
        Returns the solution details associated with the primal or dual
        solution

        Parameters
        ----------
        vtype : string, optional
            'Primal' or 'Dual'
        solution : integer, optional
            Solution number to be returned (for MILP)
        pivot : boolean, optional
            Switch for returning multiple solutions in columns as a pivot table

        Returns
        -------
        solution : :class:`pandas.DataFrame`
            Primal or dual solution table returned from the CAS Action

        Examples
        --------

        >>> m.solve()
        >>> print(m.get_solution('Primal'))
                     var   lb             ub  value  solution
        0       x[clock]  0.0  1.797693e+308    0.0       1.0
        1          x[pc]  0.0  1.797693e+308    5.0       1.0
        2   x[headphone]  0.0  1.797693e+308    2.0       1.0
        3         x[mug]  0.0  1.797693e+308    0.0       1.0
        4        x[book]  0.0  1.797693e+308    0.0       1.0
        5         x[pen]  0.0  1.797693e+308    1.0       1.0
        6       x[clock]  0.0  1.797693e+308    0.0       2.0
        7          x[pc]  0.0  1.797693e+308    5.0       2.0
        8   x[headphone]  0.0  1.797693e+308    2.0       2.0
        9         x[mug]  0.0  1.797693e+308    0.0       2.0
        10       x[book]  0.0  1.797693e+308    0.0       2.0
        11        x[pen]  0.0  1.797693e+308    0.0       2.0
        12      x[clock]  0.0  1.797693e+308    1.0       3.0
        13         x[pc]  0.0  1.797693e+308    4.0       3.0
        ...

        >>> print(m.get_solution('Primal', solution=2))
                     var   lb             ub  value  solution
        6       x[clock]  0.0  1.797693e+308    0.0       2.0
        7          x[pc]  0.0  1.797693e+308    5.0       2.0
        8   x[headphone]  0.0  1.797693e+308    2.0       2.0
        9         x[mug]  0.0  1.797693e+308    0.0       2.0
        10       x[book]  0.0  1.797693e+308    0.0       2.0
        11        x[pen]  0.0  1.797693e+308    0.0       2.0

        >>> print(m.get_solution(pivot=True))
        solution      1.0  2.0  3.0  4.0  5.0
        var
        x[book]       0.0  0.0  0.0  1.0  0.0
        x[clock]      0.0  0.0  1.0  1.0  0.0
        x[headphone]  2.0  2.0  1.0  1.0  0.0
        x[mug]        0.0  0.0  0.0  1.0  0.0
        x[pc]         5.0  5.0  4.0  1.0  0.0
        x[pen]        1.0  0.0  0.0  1.0  0.0

        >>> print(m.get_solution('Dual'))
                             con  value  solution
        0             weight_con   20.0       1.0
        1       limit_con[clock]    0.0       1.0
        2          limit_con[pc]    5.0       1.0
        3   limit_con[headphone]    2.0       1.0
        4         limit_con[mug]    0.0       1.0
        5        limit_con[book]    0.0       1.0
        6         limit_con[pen]    1.0       1.0
        7             weight_con   19.0       2.0
        8       limit_con[clock]    0.0       2.0
        9          limit_con[pc]    5.0       2.0
        10  limit_con[headphone]    2.0       2.0
        11        limit_con[mug]    0.0       2.0
        12       limit_con[book]    0.0       2.0
        13        limit_con[pen]    0.0       2.0
        ...

        >>> print(m.get_solution('dual', pivot=True))
        solution               1.0   2.0   3.0   4.0  5.0
        con
        limit_con[book]        0.0   0.0   0.0   1.0  0.0
        limit_con[clock]       0.0   0.0   1.0   1.0  0.0
        limit_con[headphone]   2.0   2.0   1.0   1.0  0.0
        limit_con[mug]         0.0   0.0   0.0   1.0  0.0
        limit_con[pc]          5.0   5.0   4.0   1.0  0.0
        limit_con[pen]         1.0   0.0   0.0   1.0  0.0
        weight_con            20.0  19.0  20.0  19.0  0.0

        Notes
        -----

        - If :meth:`Model.solve` method is used with :code:`frame=True` option,
          MILP solver returns multiple solutions. You can obtain different
          results using :code:`solution` parameter.

        """
        if vtype == 'Primal' or vtype == 'primal':
            if pivot:
                return self._primalSolution.pivot_table(
                    index=['var'], columns=['solution'], values='value')
            elif solution and 'solution' in self._primalSolution:
                return self._primalSolution.loc[
                    self._primalSolution['solution'] == solution]
            else:
                return self._primalSolution
        elif vtype == 'Dual' or vtype == 'dual':
            if pivot:
                return self._dualSolution.pivot_table(
                    index=['con'], columns=['solution'], values='value')
            elif solution and 'solution' in self._dualSolution:
                return self._dualSolution.loc[
                    self._dualSolution['solution'] == solution]
            else:
                return self._dualSolution
        else:
            return None

    def set_session(self, session):
        """
        Sets the CAS session for model

        Parameters
        ----------
        session : :class:`swat.cas.connection.CAS` or \
:class:`saspy.SASsession`
            CAS or SAS Session object

        Notes
        -----

        * Session of a model can be set at initialization.
          See :class:`Model`.

        """
        self._session = session

    def set_coef(self, var, con, value):
        """
        Updates the coefficient of a variable inside constraints

        Parameters
        ----------
        var : Variable
            Variable whose coefficient will be updated
        con : Constraint
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

        """
        con.update_var_coef(var=var, value=value)

    def print_solution(self):
        """
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

        Notes
        -----

        - This function may not work for abstract variables and nonlinear
          models.

        """
        for v in self._variables:
            print('{}: {}'.format(v._name, v._value))

    def _append_row(self, row):
        """
        Appends a new row to the model representation

        Parameters
        ----------
        row : list
            A new row to be added to the model representation for MPS format

        Returns
        -------
        rowid : int
            Current number for the ID column
        """
        self._datarows.append(row + [str(self._id)])
        rowid = self._id
        self._id = self._id+1
        return rowid

    def to_frame(self, constant=False):
        """
        Converts the Python model into a DataFrame object in MPS format

        Parameters
        ----------
        constant : boolean, optional
            Switching for using objConstant argument for solveMilp, solveLp. \
            Adds the constant as an auxiliary variable if value is True.

        Returns
        -------
        mpsdata : :class:`pandas.DataFrame`
            Problem representation in strict MPS format

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
        * This method is called inside :meth:`Model.solve`.
        """
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
        if constant and self._objective._linCoef['CONST']['val'] != 0:
            obj_constant = self.add_variable(name=sasoptpy.utils.check_name(
                'obj_constant', 'var'))
            constant_value = self._objective._linCoef['CONST']['val']
            obj_constant.set_bounds(lb=constant_value, ub=constant_value)
            obj_constant._value = constant_value
            obj_name = self._objective._name + '_constant'
            self._objective = self._objective - constant_value + obj_constant
            self._objective._name = obj_name
            print('WARNING: The objective function contains a constant term,' +
                  ' an auxiliary variable is added.')
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

        df = mpsdata
        for f in ['Field4', 'Field6']:
            df[f] = df[f].replace('', np.nan)
        df['_id_'] = df['_id_'].astype('int')
        df[['Field4', 'Field6']] = df[['Field4', 'Field6']].astype(float)

        return mpsdata

    def to_optmodel(self, header=True, expand=False, ordered=False,
                    ods=False, solve=True, options={}, primalin=False):
        """
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
        ods : boolean, optional
            Option for converting printed tables into ODS tables
        solve : boolean, optional
            Option to append solve command at the end
        options : dict, optional
            Solver options for the OPTMODEL solve command

        Returns
        -------
        s : string
            PROC OPTMODEL representation of the model

        Examples
        --------

        >>> print(m.to_optmodel())
        proc optmodel;
        var get {{'clock','mug','headphone','book','pen'}} integer >= 0;
        get['clock'] = 3.0;
        get['mug'] = 4.0;
        get['headphone'] = 2.0;
        get['book'] = -0.0;
        get['pen'] = 5.0;
        con limit_con_clock : get['clock'] <= 3;
        con limit_con_mug : get['mug'] <= 5;
        con limit_con_headphone : get['headphone'] <= 2;
        con limit_con_book : get['book'] <= 10;
        con limit_con_pen : get['pen'] <= 15;
        con weight_con : 4 * get['clock'] + 6 * get['mug'] + \
7 * get['headphone'] + 12 * get['book'] + get['pen'] <= 55;
        max total_value = 8 * get['clock'] + 10 * get['mug'] + \
15 * get['headphone'] + 20 * get['book'] + get['pen'];
        solve;
        print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
        print _con_.name _con_.body _con_.dual;
        quit;


        Notes
        -----
        * This method is called inside :func:`Model.solve`.

        """
        solve_option_keys = ('with', 'obj', 'objective', 'noobj', 'noobjective', 'relaxint', 'primalin')

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

            if solve:
                s += tab + 'solve'
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
                    if primalin and primalin_set is False and options['with'] is 'milp':
                        optstring += ' primalin'
                    if optstring:
                        s += ' /' + optstring
                s += ';\n'

            if ods:
                s += tab + 'ods output PrintTable=primal_out;\n'
            s += tab + 'print _var_.name _var_.lb _var_.ub _var_ _var_.rc;\n'
            if ods:
                s += tab + 'ods output PrintTable=dual_out;\n'
            s += tab + 'print _con_.name _con_.body _con_.dual;\n'

            if header:
                s += 'quit;\n'
        else:
            # Based on creation order
            s = ''
            if header:
                s = 'proc optmodel;\n'
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
                    if not hasattr(cm, '_after') or not cm._after:
                        s += cm._defn() + '\n'
            if expand:
                s += 'expand;\n'

            # Solve block
            if solve:
                s += 'solve'
                pre_opts = ''
                pos_opts = ''

                if options:
                    primalin_set = False
                    for key, value in options.items():
                        if key in solve_option_keys:
                            if key == 'with':
                                pre_opts += ' with ' + options['with']
                            elif key == 'relaxint' and options[key] is True:
                                pre_opts += ' relaxint '
                            elif key == 'obj' or key == 'objectives':
                                pre_opts += ' obj ({})'.format(' '.join(i._name for i in options[key]))
                            elif key == 'primalin' and options[key] is True:
                                pos_opts += ' primalin'
                                primalin_set = True
                        else:
                            if type(value) is dict:
                                pos_opts += ' {}=('.format(key) + ','.join(
                                    '{}={}'.format(i, j)
                                    for i, j in value.items()) + ')'
                            else:
                                pos_opts += ' {}={}'.format(key, value)

                    if primalin and primalin_set is False and options['with'] is 'milp':
                        pos_opts += ' primalin'
                    if pre_opts != '':
                        s += pre_opts
                    if pos_opts != '':
                        s += ' /' + pos_opts
                s += ';\n'

            # Output ODS tables
            if ods:
                s += 'ods output PrintTable=primal_out;\n'
            s += 'print _var_.name _var_.lb _var_.ub _var_ _var_.rc;\n'
            if ods:
                s += 'ods output PrintTable=dual_out;\n'
            s += 'print _con_.name _con_.body _con_.dual;\n'

            # After-solve statements
            for i in self._statements:
                if i._after:
                    s += i._defn() + '\n'

            if header:
                s += 'quit;\n'
        return(s)

    def __str__(self):
        """
        Returns a string representation of the Model object.

        Examples
        --------

        >>> print(m)
        Model: [
          Name: knapsack
          Session: cashost:casport
          Objective: MAX [8 * get[clock] + 10 * get[mug] + 15 * get[headphone]\
 + 20 * get[book] + get[pen]]
          Variables (5): [
            get[clock]
            get[mug]
            get[headphone]
            get[book]
            get[pen]
          ]
          Constraints (6): [
            get[clock] <=  3
            get[mug] <=  5
            get[headphone] <=  2
            get[book] <=  10
            get[pen] <=  15
            4 * get[clock] + 6 * get[mug] + 7 * get[headphone] + \
12 * get[book] + get[pen] <=  55
          ]
        ]

        """
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
        """
        Returns a representation of the Model object.

        Examples
        --------

        >>> print(repr(m))
        sasoptpy.Model(name='model1', session=CAS('cashost', 12345,
            'username', protocol='cas', name='py-session-1',
            session='594ad8d5-6a7b-3443-a155-be59177e8d23'))

        """
        if self._session is not None:
            stype = self.test_session()
            if stype == 'SAS':
                s = ('sasoptpy.Model(name=\'{}\', ',
                     'session=saspy.SASsession(cfgname=\'{}\'))').format(
                         self._name, self._session.sascfg.name)
            elif stype == 'CAS':
                s = 'sasoptpy.Model(name=\'{}\', session={})'.format(
                    self._name, self._session)
        else:
            s = 'sasoptpy.Model(name=\'{}\')'.format(self._name)
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
        """
        Checks if the model can be written as a linear model (in MPS format)

        Returns
        -------
        is_linear : boolean
            True if model does not have any nonlinear components or abstract\
            operations, False otherwise
        """
        for c in self._constraints:
            if not c._is_linear():
                return False
        if not self._objective._is_linear():
            return False
        return True

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
        """
        Tests if the model session is defined and still active

        Returns
        -------
        session : string
            'CAS' for CAS sessions, 'SAS' for SAS sessions, None otherwise

        """
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

    def upload_model(self, name=None, replace=True, constant=False):
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
        if self.test_session():
            # Conversion and upload
            df = self.to_frame(constant=constant)

            print('NOTE: Uploading the problem DataFrame to the server.')
            if name is not None:
                return self._session.upload_frame(
                    data=df, casout={'name': name, 'replace': replace})
            else:
                return self._session.upload_frame(
                    data=df, casout={'replace': replace})
        else:
            return None

    def solve(self, options=None, submit=True, name=None,
              frame=False, drop=False, replace=True, primalin=False,
              milp=None, lp=None, verbose=False):
        """
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
        verbose : boolean, optional (experimental)
            Switch for printing generated OPTMODEL code

        Returns
        -------
        solution : :class:`pandas.DataFrame`
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

        * This method is essentially a wrapper for two other methods.
        * Some of the options listed under ``options`` argument may not be
          passed based on which CAS Action is being used.
        * The ``option`` argument should be a dictionary, where keys are
          option names. For example, ``m.solve(options={'maxtime': 600})``
          limits the solution time to 600 seconds.
        * See :ref:`solver-options` for a list of solver options.

        See also
        --------
        :meth:`Model.solve_on_cas`, :meth:`Model.solve_on_mva`

        """
        if options is None:
            options = {}

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
        if milp is not None:
            warnings.warn(
                'WARNING: Solve method arguments `milp` and `lp` will be '
                'deprecated, use `options` instead', DeprecationWarning)
            options.update(milp)
            options['with'] = 'milp'
        if lp is not None:
            warnings.warn(
                'WARNING: Solve method arguments `milp` and `lp` will be '
                'deprecated, use `options` instead', DeprecationWarning)
            options.update(lp)
            options['with'] = 'lp'

        # Check if multiple solution table is needed
        if options.get('obj', None):
            self.add_statement(
                'create data allsols from [s]=(1.._NVAR_) ' +
                'name=_VAR_[s].name {j in 1.._NSOL_} <col(\'sol_\'||j)=_VAR_[s].sol[j]>;', after_solve=True)

        # Call solver based on session type
        return solver_func(
            sess, options=options, submit=submit, name=name,
            drop=drop, frame=frame, replace=replace, primalin=primalin,
            verbose=verbose)

    def solve_on_cas(self, session, options, submit, name,
                     frame, drop, replace, primalin, verbose):
        """
        Solves the optimization problem on CAS Servers

        Notes
        -----

        - This function should not be called directly. Instead, use :meth:`Model.solve`.

        See also
        --------
        :func:`Model.solve`

        """

        # Check which method will be used for solve
        session.loadactionset(actionset='optimization')

        if frame or not hasattr(session.optimization, 'runoptmodel'):
            frame = True

        # OPTMODEL variant does not accept decomp blocks yet
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
                print('INFO: Model {} includes nonlinear or abstract'.format(self._name),
                      'components, switching to OPTMODEL mode.')
                switch = True

            if switch and hasattr(session.optimization, 'runoptmodel'):
                frame = False
            elif switch:
                print('ERROR: Switching to OPTMODEL mode is failed,',
                      'runOptmodel action is not available in CAS Server.')
                return None

        if frame:  # MPS
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

            # Check if objective constant workaround is needed
            sfunc = session.solveLp if ptype == 1 else session.solveMilp
            has_arg = 'objconstant' in inspect.signature(sfunc).parameters
            if has_arg and 'objconstant' not in options:
                objconstant = self._objective._linCoef['CONST']['val']
                options['objconstant'] = objconstant

            # Upload the problem
            mps_table = self.upload_model(name, replace=replace,
                                          constant=not has_arg)

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

            self.response = response

            # Parse solution
            if(response.get_tables('status')[0] == 'OK'):
                self._primalSolution = session.CASTable(
                    'primal', caslib='CASUSER').to_frame()
                self._dualSolution = session.CASTable(
                    'dual', caslib='CASUSER').to_frame()
                # Bring solution to variables
                for _, row in self._primalSolution.iterrows():
                    if ('_SOL_' in self._primalSolution and row['_SOL_'] == 1)\
                         or '_SOL_' not in self._primalSolution:
                        self._variableDict[row['_VAR_']]._value =\
                            row['_VALUE_']

                # Capturing dual values for LP problems
                if ptype == 1:
                    self._primalSolution = self._primalSolution[
                        ['_VAR_', '_LBOUND_', '_UBOUND_', '_VALUE_',
                         '_R_COST_']]
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
                    try:
                        self._primalSolution = self._primalSolution[
                            ['_VAR_', '_LBOUND_', '_UBOUND_', '_VALUE_',
                             '_SOL_']]
                        self._primalSolution.columns = ['var', 'lb', 'ub',
                                                        'value', 'solution']
                        self._dualSolution = self._dualSolution[
                            ['_ROW_', '_ACTIVITY_', '_SOL_']]
                        self._dualSolution.columns = ['con', 'value',
                                                      'solution']
                    except:
                        self._primalSolution = self._primalSolution[
                            ['_VAR_', '_LBOUND_', '_UBOUND_', '_VALUE_']]
                        self._primalSolution.columns = ['var', 'lb', 'ub',
                                                        'value']
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
        else:  # OPTMODEL

            # Find problem type and initial values
            ptype = 1  # LP
            for v in self._variables:
                if v._type != sasoptpy.utils.CONT:
                    ptype = 2
                    break

            print('NOTE: Converting model {} to OPTMODEL.'.format(self._name))
            optmodel_string = self.to_optmodel(header=False, options=options,
                                               ods=False, primalin=primalin)
            if verbose:
                print(optmodel_string)
            if not submit:
                return optmodel_string
            print('NOTE: Submitting OPTMODEL code to CAS server.')
            response = session.runOptmodel(
                optmodel_string,
                outputTables={
                    'names': {'solutionSummary': 'solutionSummary',
                              'problemSummary': 'problemSummary',
                              'Print1.PrintTable': 'primal',
                              'Print2.PrintTable': 'dual'}
                    }
                )

            self.response = response

            # Parse solution
            #if(response.get_tables('status')[0] == 'OK'):
            if response['status'] == 'OK':

                self._primalSolution = response['Print1.PrintTable']
                self._primalSolution = self._primalSolution[
                    ['_VAR__NAME', '_VAR__LB', '_VAR__UB', '_VAR_',
                     '_VAR__RC']]
                self._primalSolution.columns = ['var', 'lb', 'ub', 'value',
                                                'rc']
                self._dualSolution = response['Print2.PrintTable']
                self._dualSolution = self._dualSolution[
                    ['_CON__NAME', '_CON__BODY', '_CON__DUAL']]
                self._dualSolution.columns = ['con', 'value', 'dual']
                # Bring solution to variables
                for _, row in self._primalSolution.iterrows():

                    if row['var'] in self._variableDict:
                        self._variableDict[row['var']]._value = row['value']
                    else:
                        # OPTMODEL strings may have spaces in it
                        str_safe = row['var'].replace(' ', '_').replace('\'', '')
                        if str_safe in self._variableDict:
                            self._variableDict[str_safe]._value = row['value']
                        else:
                            # Search in vargroups for the original name
                            sasoptpy.utils._set_abstract_values(row)

                # Capturing dual values for LP problems
                if ptype == 1:
                    for _, row in self._primalSolution.iterrows():
                        if row['var'] in self._variableDict:
                            self._variableDict[row['var']]._dual = row['rc']
                    for _, row in self._dualSolution.iterrows():
                        if row['con'] in self._constraintDict:
                            self._constraintDict[row['con']]._dual =\
                                row['dual']

                self._solutionSummary = response['Solve1.SolutionSummary']\
                    [['Label1', 'cValue1']].set_index(['Label1'])
                self._problemSummary = response['Solve1.ProblemSummary']\
                    [['Label1', 'cValue1']].set_index(['Label1'])

                self._solutionSummary.index.names = ['Label']
                self._solutionSummary.columns = ['Value']

                self._problemSummary.index.names = ['Label']
                self._problemSummary.columns = ['Value']

                self._status = response.solutionStatus
                self._soltime = response.solutionTime

                if('OPTIMAL' in response.solutionStatus or 'ABSFCONV' in response.solutionStatus):
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

    def solve_on_mva(self, session, options, submit, name,
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
                if v._type != sasoptpy.utils.CONT:
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
