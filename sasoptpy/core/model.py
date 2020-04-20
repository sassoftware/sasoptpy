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


from collections import OrderedDict
import inspect
from math import inf
from types import GeneratorType
import warnings

import numpy as np
import pandas as pd

import sasoptpy
import sasoptpy.util
from sasoptpy.core import (Expression, Objective, Variable, VariableGroup,
                           Constraint, ConstraintGroup)


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

    @sasoptpy.class_containable
    def __init__(self, name=None, session=None):
        self._name = name
        self._objorder = sasoptpy.util.get_creation_id()
        self._session = session

        self._members = {}

        self._variableDict = OrderedDict()
        self._constraintDict = OrderedDict()
        self._objectiveDict = OrderedDict()

        self._setDict = OrderedDict()
        self._parameterDict = OrderedDict()
        self._impvarDict = OrderedDict()
        self._statementDict = OrderedDict()
        self._postSolveDict = OrderedDict()

        self._soltime = 0
        self._objval = None
        self._status = ''
        self._castablename = None
        self._mpsmode = 0
        self._problemSummary = None
        self._solutionSummary = None
        self._primalSolution = None
        self._dualSolution = None
        self._tunerResults = None
        self._milp_opts = {}
        self._lp_opts = {}
        self.response = None

        self._droppedCons = OrderedDict()
        self._droppedVars = OrderedDict()

        self._objective = Objective(0, name=name + '_obj', default=True,
                                    internal=True)

        print('NOTE: Initialized model {}.'.format(name))

    def __eq__(self, other):
        if not isinstance(other, sasoptpy.Model):
            warnings.warn('Cannot compare Model object with {}'.
                          format(type(other)), RuntimeWarning, stacklevel=2)
            return False
        return super().__eq__(other)

    def get_name(self):
        """
        Returns model name
        """
        return self._name

    def add(self, object):
        self.include(object)

    def add_variable(self, name, vartype=None,
                     lb=None, ub=None, init=None):
        """
        Adds a new variable to the model

        New variables can be created via this method or existing variables
        can be added to the model.

        Parameters
        ----------
        name : string
            Name of the variable to be created
        vartype : string, optional
            Type of the variable, either `sasoptpy.BIN`, `sasoptpy.INT` or
            `sasoptpy.CONT`
        lb : float, optional
            Lower bound of the variable
        ub : float, optional
            Upper bound of the variable
        init : float, optional
            Initial value of the variable

        Returns
        -------
        var : :class:`Variable`
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
        >>> m.include(y)

        Notes
        -----

        * `name` is a mandatory field for this method.

        See also
        --------
        :class:`Variable`, :func:`Model.include`
        """

        var = Variable(name, vartype, lb, ub, init)
        self.include(var)
        return var

    def add_variables(self, *argv, name,
                      vartype=None,
                      lb=None, ub=None, init=None):
        """
        Adds a group of variables to the model

        Parameters
        ----------
        argv : list, dict, :class:`pandas.Index`
            Loop index for variable group
        name : string
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

        vg = VariableGroup(*argv, name=name, vartype=vartype, lb=lb, ub=ub,
                           init=init)
        self.include(vg)
        return vg

    @sasoptpy.containable
    def add_constraint(self, c, name):
        """
        Adds a single constraint to the model

        Parameters
        ----------
        c : :class:`Constraint`
            Constraint to be added to the model
        name : string
            Name of the constraint

        Returns
        -------
        c : :class:`Constraint`
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

        if ((c._direction == 'L' and c._linCoef['CONST']['val'] == -inf) or
           (c._direction == 'G' and c._linCoef['CONST']['val'] == inf)):
            raise ValueError("Invalid constant value for the constraint type")

        if c._name is None:
            c.set_name(name)
            c.set_permanent()

        self.include(c)
        return c

    def add_constraints(self, argv, name):
        """
        Adds a set of constraints to the model

        Parameters
        ----------
        argv : Generator-type object
            List of constraints as a generator-type Python object
        name : string
            Name for the constraint group and individual constraint prefix

        Returns
        -------
        cg : :class:`ConstraintGroup`
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

        if type(argv) == list or type(argv) == GeneratorType:
            cg = ConstraintGroup(argv, name=name)
            self.include(cg)
            return cg
        elif sasoptpy.core.util.is_constraint(argv):
            warnings.warn(
                'Use add_constraint method for adding single constraints',
                UserWarning)
            c = self.add_constraint(argv, name=name)
            return c

    def add_set(self, name, init=None, value=None, settype=None):
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
            Types of the set as a list

            The list can have one more `num` (for float) and `str` (for string)
            values. You can use `sasoptpy.NUM` and `sasoptpy.STR` for floats and
            strings, respectively.

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

        >>> m.add_set(name='W', settype=[so.STR, so.NUM])
        >>> print(W._defn())
        set <str, num> W;

        """
        new_set = sasoptpy.abstract.Set(name, init=init, value=value,
                                        settype=settype)
        self.include(new_set)
        return new_set

    def add_parameter(self, *argv, name, init=None, value=None, p_type=None):
        """
        Adds a :class:`abstract.Parameter` object to the model

        Parameters
        ----------
        argv : :class:`Set`, optional
            Index or indices of the parameter
        name : string
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

        >>> I = m.add_set(name='I')
        >>> J = m.add_set(name='J')
        >>> p = m.add_parameter(I, J, name='p')
        >>> print(p._defn())
        num p {{I,J}};

        Returns
        -------

        p : :class:`abstract.Parameter` or :class:`abstract.ParameterGroup`
            A single parameter or a parameter group

        """
        if len(argv) == 0:
            p = sasoptpy.abstract.Parameter(
                name, init=init, value=value, ptype=p_type)
            self.include(p)
            return p
        else:
            keylist = list(argv)
            p = sasoptpy.abstract.ParameterGroup(keylist, name=name, init=init,
                                                 value=value, ptype=p_type)
            self.include(p)
            return p

    def add_implicit_variable(self, argv=None, name=None):
        """
        Adds an implicit variable to the model

        Parameters
        ----------
        argv : Generator-type object
            Generator object where each item is an entry
        name : string
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

        - Based on whether the implicit variables  are generated by a regular
          or abstract expression, they can appear in generated OPTMODEL codes.

        """
        if name is None:
            name = sasoptpy.util.get_next_name()
        iv = sasoptpy.abstract.ImplicitVar(argv=argv, name=name)
        self.include(iv)
        return iv

    def add_statement(self, statement, after_solve=None):
        """
        Adds a PROC OPTMODEL statement to the model

        Parameters
        ----------
        statement : :class:`Expression` or string
            Statement object
        after_solve : boolean
            Switch for appending the statement after the problem solution

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

        - If the statement string includes 'print', then the statement is
          automatically placed after the solve even if `after_solve` is `False`.

        """
        if isinstance(statement, sasoptpy.abstract.Statement):
            self._save_statement(statement, after_solve)
        elif isinstance(statement, str):
            s = sasoptpy.abstract.LiteralStatement(statement)
            self._save_statement(s, after_solve)

    def add_postsolve_statement(self, statement):
        if isinstance(statement, sasoptpy.abstract.Statement):
            self._save_statement(statement, after_solve=True)
        elif isinstance(statement, str):
            s = sasoptpy.abstract.LiteralStatement(statement)
            self._save_statement(s, after_solve=True)

    def _save_statement(self, st, after_solve=None):
        if after_solve is None or after_solve is False:
            self._statementDict[id(st)] = st
        else:
            self._postSolveDict[id(st)] = st

    def drop_variable(self, variable):
        """
        Drops a variable from the model

        Parameters
        ----------
        variable : :class:`Variable`
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
        vname = variable.get_name()
        if self._variableDict.pop(vname, None) is None:
            self._droppedVars[vname] = True

    def restore_variable(self, variable):
        vname = variable.get_name()
        if variable.get_parent_reference()[0] is not None:
            self._droppedVars.pop(vname, None)
        else:
            self.include(variable)

    @sasoptpy.containable
    def drop_constraint(self, constraint):
        """
        Drops a constraint from the model

        Parameters
        ----------
        constraint : :class:`Constraint`
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

        cname = constraint.get_name()
        if self._constraintDict.pop(cname, None) is None:
            self._droppedCons[constraint._get_optmodel_name()] = True

    def restore_constraint(self, constraint):
        cname = constraint.get_name()
        if constraint.get_parent_reference()[0] is not None:
            self._droppedCons.pop(constraint._get_optmodel_name(), None)
        else:
            self.include(constraint)

    def drop_variables(self, *variables):
        """
        Drops a variable group from the model

        Parameters
        ----------
        variables : :class:`VariableGroup`
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

    def drop_constraints(self, *constraints):
        """
        Drops a constraint group from the model

        Parameters
        ----------
        constraints : :class:`Constraint` or :class:`ConstraintGroup`
            Arbitrary number of constraints to be dropped

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

    def include(self, *argv):
        """
        Adds existing variables and constraints to a model

        Parameters
        ----------
        argv :
            Objects to be included in the model

        Notes
        -----
        * Valid object types for `argv` parameter:

          - :class:`Model`

            Including a model causes all variables and constraints inside the
            original model to be included.

          - :class:`Variable`
          - :class:`Constraint`
          - :class:`VariableGroup`
          - :class:`ConstraintGroup`
          - :class:`Objective`
          - :class:`Set`
          - :class:`Parameter`
          - :class:`ParameterGroup`
          - :class:`Statement` and all subclasses
          - :class:`ImplicitVar`


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

        """

        include_methods = {
            Variable: self._include_variable,
            VariableGroup: self._include_vargroup,
            Constraint: self._include_constraint,
            ConstraintGroup: self._include_congroup,
            Objective: self._set_objective,
            sasoptpy.Set: self._include_set,
            sasoptpy.Parameter: self._include_parameter,
            sasoptpy.ParameterGroup: self._include_parameter_group,
            sasoptpy.abstract.LiteralStatement: self._include_statement,
            sasoptpy.ImplicitVar: self._include_expdict,
            sasoptpy.abstract.ReadDataStatement: self._include_statement,
            sasoptpy.abstract.DropStatement: self._include_statement,
            list: self.include,
            Model: self._include_model
        }

        for c in argv:
            meth = include_methods.get(type(c))
            if any(isinstance(c, i) for i in [Variable, VariableGroup, Constraint, ConstraintGroup, Objective]):
                if sasoptpy.container is not None:
                    if c._objorder > self._objorder:
                        raise ReferenceError('Object {} should be defined before Model {} inside a Workspace'.format(
                            c._expr(), self.get_name()
                    ))
            if meth is not None:
                meth(c)

    def _include_variable(self, var):
        vname = var.get_name()
        if vname in self._variableDict:
            warnings.warn(f"Variable name {vname} exists in the model."
                          "New declaration will override the existing value.",
                          UserWarning)
        self._variableDict[vname] = var

    def _include_vargroup(self, vg):
        self._variableDict[vg.get_name()] = vg

    def _include_constraint(self, con):
        if sasoptpy.core.util.has_parent(con):
            return
        name = con.get_name()
        if con.get_name() in self._constraintDict:
            warnings.warn(f"Constraint name {name} exists in the model."
                          "New declaration will override the existing value.",
                          UserWarning)
        self._constraintDict[con.get_name()] = con

    def _include_congroup(self, cg):
        self._constraintDict[cg.get_name()] = cg

    def _set_objective(self, ob):
        self._objective = ob

    def _include_set(self, st):
        self._setDict[id(st)] = st

    def _include_parameter(self, p):
        self._parameterDict[p.get_name()] = p

    def _include_parameter_group(self, pg):
        self._parameterDict[pg.get_name()] = pg

    def _include_statement(self, os):
        self._save_statement(os)

    def _include_expdict(self, ed):
        self._impvarDict[ed.get_name()] = ed

    def _include_model(self, model):
        self._setDict.update(model._setDict)
        self._parameterDict.update(model._parameterDict)
        self._statementDict.update(model._statementDict)
        self._postSolveDict.update(model._postSolveDict)
        self._impvarDict.update(model._impvarDict)
        for s in model.get_grouped_variables().values():
            self._include_variable(s)
        for s in model.get_grouped_constraints().values():
            self._include_constraint(s)
        self._objective = model._objective

    def drop(self, obj):
        if isinstance(obj, sasoptpy.VariableGroup):
            self.drop_variables(obj)
        elif isinstance(obj, sasoptpy.Variable):
            self.drop_variable(obj)
        elif isinstance(obj, sasoptpy.ConstraintGroup):
            self.drop_constraints(obj)
        elif isinstance(obj, sasoptpy.Constraint):
            self.drop_constraint(obj)
        elif isinstance(obj, sasoptpy.Set):
            self._setDict.pop(id(obj), None)
        elif isinstance(obj, sasoptpy.Parameter) or\
             isinstance(obj, sasoptpy.ParameterGroup):
            self._parameterDict.pop(obj.get_name(), None)
        elif isinstance(obj, sasoptpy.abstract.Statement):
            self._statementDict.pop(id(obj), None)

    def set_objective(self, expression, name, sense=None):
        """
        Specifies the objective function for the model

        Parameters
        ----------
        expression : :class:`Expression`
            The objective function as an Expression
        name : string
            Name of the objective value
        sense : string, optional
            Objective value direction, `sasoptpy.MIN` or `sasoptpy.MAX`

        Returns
        -------
        objective : :class:`Expression`
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

        >>> f1 = m.set_objective(2 * x + y, sense=so.MIN, name='f1')
        >>> f2 = m.append_objective( (x - y) ** 2, sense=so.MIN, name='f2')
        >>> print(m.to_optmodel(options={'with': 'blackbox', 'obj': (f1, f2)}))
        proc optmodel;
        var x;
        var y;
        min f1 = 2 * x + y;
        min f2 = (x - y) ^ (2);
        solve with blackbox obj (f1 f2);
        print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
        print _con_.name _con_.body _con_.dual;
        quit;

        Notes
        -----
        - Default objective sense is minimization `MIN`.
        - This method replaces the existing objective of the model.
          When working with multiple objectives, use the
          :meth:`Model.append_objective` method.

        See also
        --------
        :meth:`Model.append_objective`

        """

        obj = Objective(expression, sense=sense, name=name)
        self._objective = obj
        return self._objective

    def append_objective(self, expression, name, sense=None):
        """
        Appends a new objective to the model

        Parameters
        ----------
        expression : :class:`Expression`
            The objective function as an Expression
        name : string
            Name of the objective value
        sense : string, optional
            Objective value direction, `sasoptpy.MIN` or `sasoptpy.MAX`

        Returns
        -------
        objective : :class:`Expression`
            Objective function as an :class:`Expression` object

        Examples
        --------

        >>> f1 = m.set_objective(2 * x + y, sense=so.MIN, name='f1')
        >>> f2 = m.append_objective( (x - y) ** 2, sense=so.MIN, name='f2')
        >>> print(m.to_optmodel(options={'with': 'blackbox', 'obj': (f1, f2)}))
        proc optmodel;
        var x;
        var y;
        min f1 = 2 * x + y;
        min f2 = (x - y) ^ (2);
        solve with blackbox obj (f1 f2);
        print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
        print _con_.name _con_.body _con_.dual;
        quit;

        Notes
        -----
        - Default objective sense is minimization `MIN`.

        See also
        --------
        :meth:`Model.set_objective`

        """
        obj = Objective(expression, name=name, sense=sense)
        self._objectiveDict[id(obj)] = obj
        return obj

    def get_objective(self):
        """
        Returns the objective function as an :class:`Expression` object

        Returns
        -------
        objective : :class:`Expression`
            Objective function

        Examples
        --------

        >>> m.set_objective(4 * x - 5 * y, name='obj')
        >>> print(repr(m.get_objective()))
        sasoptpy.Expression(exp =  4.0 * x  -  5.0 * y , name='obj')

        """
        return self._objective

    def get_all_objectives(self):
        """
        Returns a list of objectives in the model

        Returns
        -------
        all_objectives : list
           A list of :class:`Objective` objects

        Examples
        --------

        >>> m = so.Model(name='test_set_get_objective')
        >>> x = m.add_variable(name='x')
        >>> obj1 = m.set_objective(2 * x, sense=so.MIN, name='obj1')
        >>> obj2 = m.set_objective(5 * x, sense=so.MIN, name='obj2') # Overrides obj1
        >>> obj3 = m.append_objective(10 * x, sense=so.MIN, name='obj3')
        >>> assertEqual(m.get_all_objectives(), [obj2, obj3])
        True

        """
        all_objs = list(self._objectiveDict.values())
        all_objs.append(self._objective)
        return sorted(all_objs, key=lambda i: i._objorder)

    def get_objective_value(self):
        """
        Returns the optimal objective value

        Returns
        -------
        objective_value : float
            Optimal objective value at current solution

        Examples
        --------

        >>> m.solve()
        >>> print(m.get_objective_value())
        42.0

        Notes
        -----

        - This method should be used for getting the objective value after
          solve.
        - In order to get the current value of the objective after changing
          variable values, you can use :code:`m.get_objective().get_value()`.

        """
        if self._objval is not None:
            return sasoptpy.util.get_in_digit_format(self._objval)
        else:
            return self.get_objective().get_value()

    def set_objective_value(self, value):
        self._objval = value

    def get_constraint(self, name):
        """
        Returns the reference to a constraint in the model

        Parameters
        ----------
        name : string
            Name of the constraint requested

        Returns
        -------
        constraint : :class:`Constraint`
            Requested object

        Examples
        --------

        >>> m.add_constraint(2 * x + y <= 15, name='c1')
        >>> print(m.get_constraint('c1'))
        2.0 * x  +  y  <=  15

        """
        # return self._constraintDict.get(name, None)
        constraints = self.get_constraints_dict()
        safe_name = name.replace('\'', '')
        if name in constraints:
            return constraints[name]
        elif safe_name in constraints:
            return constraints[safe_name]
        elif '[' in name:
            first_part = name.split('[')[0]
            if constraints.get(first_part, None) is not None:
                vg = constraints.get(first_part)
                return vg.get_member_by_name(name)
        else:
            return None

    def loop_constraints(self):
        for i in self._constraintDict.values():
            if isinstance(i, sasoptpy.Constraint):
                yield i
            elif isinstance(i, sasoptpy.ConstraintGroup):
                for j in i.get_members().values():
                    yield j

    def _get_all_constraints(self):
        all_cons = OrderedDict()
        for c in self._constraintDict.values():
            if isinstance(c, sasoptpy.Constraint):
                all_cons[c.get_name()] = c
            elif isinstance(c, sasoptpy.ConstraintGroup):
                for sc in c.get_members().values():
                    all_cons[sc.get_name()] = sc
        return all_cons

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
        return list(self.loop_constraints())

    def get_constraints_dict(self):
        return self._constraintDict

    def get_grouped_constraints(self):
        """
        Returns an ordered dictionary of constraints

        Returns
        -------
        grouped_cons : OrderedDict
           Dictionary of constraints and constraint groups in the model

        Examples
        --------

        >>> m1 = so.Model(name='test_copy_model_1')
        >>> x = m1.add_variable(name='x')
        >>> y = m1.add_variables(2, name='y')
        >>> c1 = m1.add_constraint(x + y[0] >= 2, name='c1')
        >>> c2 = m1.add_constraints((x - y[i] <= 10 for i in range(2)), name='c2')
        >>> cons = OrderedDict([('c1', c1), ('c2', c2)])
        >>> self.assertEqual(m1.get_grouped_constraints(), cons)
        True

        See also
        --------
        :meth:`Model.get_constraints`, :meth:`Model.get_grouped_variables`

        """
        return self.get_constraints_dict()

    def get_variable(self, name):
        """
        Returns the reference to a variable in the model

        Parameters
        ----------
        name : string
            Name or key of the variable requested

        Returns
        -------
        variable : :class:`Variable`
            Reference to the variable

        Examples
        --------

        >>> m.add_variable(name='x', vartype=so.INT, lb=3, ub=5)
        >>> var1 = m.get_variable('x')
        >>> print(repr(var1))
        sasoptpy.Variable(name='x', lb=3, ub=5, vartype='INT')

        """
        variables = self.get_variable_dict()
        safe_name = name.replace('\'', '')
        if name in variables:
            return variables[name]
        elif safe_name in variables:
            return variables[safe_name]
        elif '[' in name:
            first_part = name.split('[')[0]
            if variables.get(first_part, None) is not None:
                vg = variables.get(first_part)
                return vg.get_member_by_name(name)
        else:
            return None

    def loop_variables(self):
        for i in self._variableDict.values():
            if isinstance(i, sasoptpy.Variable):
                yield i
            elif isinstance(i, sasoptpy.VariableGroup):
                for j in i.get_members().values():
                    yield j

    def _get_all_variables(self):
        all_vars = OrderedDict()
        for v in self._variableDict.values():
            if isinstance(v, sasoptpy.Variable):
                all_vars[v.get_name()] = v
            elif isinstance(v, sasoptpy.VariableGroup):
                for sc in v.get_members().values():
                    all_vars[sc.get_name()] = sc
        return all_vars

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
        return list(self.loop_variables())

    def get_variable_dict(self):
        return self._variableDict

    def get_grouped_variables(self):
        """
        Returns an ordered dictionary of variables

        Returns
        -------
        grouped_vars : OrderedDict
           Dictionary of variables and variable groups in the model

        Examples
        --------

        >>> m1 = so.Model(name='test_copy_model_1')
        >>> x = m1.add_variable(name='x')
        >>> y = m1.add_variables(2, name='y')
        >>> vars = OrderedDict([('x', x), ('y', y)])
        >>> self.assertEqual(m1.get_grouped_variables(), vars)
        True

        See also
        --------
        :meth:`Model.get_variables`, :meth:`Model.get_grouped_constraints`

        """
        return self.get_variable_dict()

    def get_variable_coef(self, var):
        """
        Returns the objective value coefficient of a variable

        Parameters
        ----------
        var : :class:`Variable` or string
            Variable whose objective value is requested. It can be either the
            variable object itself, or the name of the variable.

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
        if isinstance(var, sasoptpy.core.Variable):
            varname = var.get_name()
        else:
            varname = var
        if varname in self._objective._linCoef:
            return self._objective._linCoef[varname]['val']
        else:
            if self.get_objective()._is_linear():
                if varname in self._variableDict:
                    return 0
                else:
                    raise RuntimeError('Variable is not a member of the model')
            else:
                warnings.warn('Objective is not linear', RuntimeWarning)

    def set_variable_coef(self, var, coef):
        varname = var.get_name()
        if varname in self._objective._linCoef:
            self._objective._linCoef[varname]['val'] = coef
        else:
            self._objective += coef*var

    def set_variable_value(self, name, value):

        variable = self.get_variable(name)
        if variable is not None:
            variable.set_value(value)
        else:
            self._set_abstract_values(name, value)

    def set_dual_value(self, name, value):
        variable = self.get_variable(name)
        if variable is not None:
            variable.set_dual(value)

    def get_variable_value(self, var):
        """
        Returns the value of a variable

        Parameters
        ----------
        var : :class:`Variable` or string
            Variable reference

        Notes
        -----
        - It is possible to get a variable's value by using the
          :func:`Variable.get_value` method, as long as the variable is not
          abstract.
        - This method is a wrapper around :func:`Variable.get_value` and an
          overlook function for model components.
        """

        if sasoptpy.core.util.is_variable(var):
            varname = var.get_name()
        else:
            varname = var

        if varname in self._variableDict:
            return self._variableDict[varname].get_value()
        else:
            return self._get_variable_solution(varname)

    def _get_variable_solution(self, name):
        if self._primalSolution is not None:
            for row in self._primalSolution.itertuples():
                if row.var == name:
                    return row.value
        else:
            raise RuntimeError('No primal solution is available')

        warnings.warn('Variable could not be found')
        return None

    def get_problem_summary(self):
        """
        Returns the problem summary table to the user

        Returns
        -------
        ps : :class:`swat.dataframe.SASDataFrame`
            Problem summary table, that is obtained after :meth:`Model.solve`

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
            Solution summary table, that is obtained after :meth:`Model.solve`

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
        Returns the primal and dual problem solutions

        Parameters
        ----------
        vtype : string, optional
            `Primal` or `Dual`
        solution : integer, optional
            Solution number to be returned (for the MILP solver)
        pivot : boolean, optional
            When set to `True`, returns multiple solutions in columns as a pivot
            table

        Returns
        -------
        solution : :class:`pandas.DataFrame`
            Primal or dual solution table returned from the CAS action

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

        - If the :meth:`Model.solve` method is used with :code:`frame=True`
          parameter, the MILP solver returns multiple solutions.
          You can retreive different results by using the :code:`solution`
          parameter.

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
            raise ValueError('Solution type should be \'primal\' or \'dual\'')

    def get_tuner_results(self):
        """
        Returns the tuning results

        Examples
        --------

        >>> m.tune_parameters(tunerParameters={'maxConfigs': 10})
        >>> results = m.get_tuner_reults()

        Returns
        -------
        tunerResults : dict
           Returns tuner results as a dictionary.

           Its members are

           - Performance Information
           - Tuner Information
           - Tuner Summary
           - Tuner Results

        See also
        --------
        :meth:`Model.tune_parameters`

        """
        return self._tunerResults

    def set_session(self, session):
        """
        Sets the session of model

        Parameters
        ----------
        session : :class:`swat.cas.connection.CAS` or \
:class:`saspy.SASsession`
            CAS or SAS Session object

        Notes
        -----

        * You can use CAS sessions (via SWAT package) or SAS sessions (via SASPy package)
        * Session of a model can be set at initialization.
          See :class:`Model`.

        """
        self._session = session

    def get_session(self):
        """
        Returns the session of the model

        Returns
        -------
        session : :class:`swat.cas.connection.CAS` or \
:class:`saspy.SASsession`
            Session of the model, or None
        """
        return self._session

    def get_sets(self):
        """
        Returns a list of :class:`Set` objects in the model

        Returns
        -------
        set_list : list
            List of sets in the model

        Examples
        --------

        >>> m.get_sets()
        [sasoptpy.abstract.Set(name=W, settype=['str', 'num']), sasoptpy.abstract.Set(name=I, settype=['num']), sasoptpy.abstract.Set(name=J, settype=['num'])]

        """
        return list(self._setDict.values())

    def get_parameters(self):
        """
        Returns a list of :class:`abstract.Parameter` and
        :class:`abstract.ParameterGroup` objects in the model

        Returns
        -------
        param_list : list
            List of parameters in the model

        Examples
        --------

        >>> for i in m.get_parameters():
        ...     print(i.get_name(), type(i))
        p <class 'sasoptpy.abstract.parameter_group.ParameterGroup'>
        r <class 'sasoptpy.abstract.parameter.Parameter'>

        """
        return list(self._parameterDict.values())

    def get_statements(self):
        """
        Returns a list of all statements inside the model

        Returns
        -------
        st_list : list
            List of all statement objects

        Examples
        --------

        >>> m.add_statement(so.abstract.LiteralStatement("expand;"))
        >>> m.get_statements()
        [<sasoptpy.abstract.statement.literal.LiteralStatement object at 0x7fe0202fc358>]
        >>> print(m.to_optmodel())
        proc optmodel;
        var x;
        min obj1 = x * x;
        expand;
        solve;
        quit;

        """
        return list(self._statementDict.values())

    def get_implicit_variables(self):
        """
        Returns a list of implicit variables

        Returns
        -------
        implicit_variables : list
            List of implicit variables in the model

        Examples
        --------

        >>> m = so.Model(name='test_add_impvar')
        >>> x = m.add_variables(5, name='x')
        >>> y = m.add_implicit_variable((i * x[i] + x[i] ** 2 for i in range(5)),
                                    name='y')
        >>> assertEqual([y], m.get_implicit_variables())
        True

        """
        return list(self._impvarDict.values())

    def _get_dropped_cons(self):
        return self._droppedCons

    def _get_dropped_vars(self):
        return self._droppedVars

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

        - This function might not work for abstract variables and nonlinear
          models.

        """
        for v in self.loop_variables():
            print('{}: {}'.format(v.get_name(), v._value))

    def to_frame(self, **kwargs):
        warnings.warn('Use to_mps for obtaining problem in MPS format',
                      DeprecationWarning)
        self.to_mps(**kwargs)

    def to_mps(self, **kwargs):
        """
        Returns the problem in MPS format

        Examples
        --------

        >>> print(n.to_mps())
            Field1 Field2 Field3  Field4 Field5  Field6  _id_
        0     NAME             n     0.0            0.0     1
        1     ROWS                   NaN            NaN     2
        2      MIN  myobj            NaN            NaN     3
        3  COLUMNS                   NaN            NaN     4
        4               y  myobj     2.0            NaN     5
        5      RHS                   NaN            NaN     6
        6   RANGES                   NaN            NaN     7
        7   BOUNDS                   NaN            NaN     8
        8       FR    BND      y     NaN            NaN     9
        9   ENDATA                   0.0            0.0    10

        """
        return sasoptpy.interface.to_mps(self, **kwargs)

    def to_optmodel(self, **kwargs):
        """
        Returns the model in OPTMODEL format

        Examples
        --------

        >>> print(n.to_optmodel())
        proc optmodel;
        var y init 2;
        min myobj = 2 * y;
        solve;
        quit;

        """
        return sasoptpy.interface.to_optmodel(self, **kwargs)

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
        s += '  Name: {}\n'.format(self.get_name())
        if self._session is not None:
            s += '  Session: {}:{}\n'.format(self._session._hostname,
                                             self._session._port)
        s += '  Objective: {} [{}]\n'.format(self.get_objective().get_sense(),
                                             self.get_objective())
        s += '  Variables ({}): [\n'.format(len(self.get_variables()))
        for i in self.loop_variables():
            s += '    {}\n'.format(i)
        s += '  ]\n'
        s += '  Constraints ({}): [\n'.format(len(self.get_constraints()))
        for i in self.loop_constraints():
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
            stype = self.get_session_type()
            if stype == 'SAS':
                s = "sasoptpy.Model(name='{}', session=saspy.SASsession(cfgname='{}'))".format(
                         self.get_name(), self._session.sascfg.name)
            elif stype == 'CAS':
                s = 'sasoptpy.Model(name=\'{}\', session={})'.format(
                    self.get_name(), self._session)
            else:
                raise TypeError('Invalid session type: {}'.format(type(self.get_session())))
        else:
            s = 'sasoptpy.Model(name=\'{}\')'.format(self.get_name())
        return s

    def _defn(self):
        s = 'problem {}'.format(self.get_name())
        vars = [s.get_name() for s in self.get_grouped_variables().values()]
        cons = [s.get_name() for s in self.get_grouped_constraints().values()]
        obj = self.get_objective()
        objs = []
        if not obj.is_default():
            objs.append(obj.get_name())
        elements = ' '.join(vars + cons + objs)
        if elements != '':
            s += ' include ' + elements
        s += ';'
        return s

    def _expr(self):
        return self.to_optmodel()

    def _is_linear(self):
        """
        Checks whether the model can be written as a linear model (in MPS format)

        Returns
        -------
        is_linear : boolean
            True if model does not have any nonlinear components or abstract\
            operations, False otherwise
        """
        for c in self.loop_constraints():
            if not c._is_linear():
                return False
        if not self._objective._is_linear():
            return False
        return True

    def _has_integer_vars(self):
        for v in self._variableDict.values():
            if v._type != sasoptpy.CONT:
                return True
        return False

    def get_session_type(self):
        """
        Tests whether the model session is defined and still active

        Returns
        -------
        session : string
            'CAS' for CAS sessions, 'SAS' for SAS sessions

        """
        # Check if session is defined
        return sasoptpy.util.get_session_type(self._session)

    @sasoptpy.containable
    def solve(self, **kwargs):
        """
        Solves the model by calling CAS or SAS optimization solvers

        Parameters
        ----------
        options : dict, optional
            Solver options as a dictionary object
        submit : boolean, optional
            When set to `True`, calls the solver
        name : string, optional
            Name of the table
        frame : boolean, optional
            When set to `True`, uploads the problem as a DataFrame in MPS format
        drop : boolean, optional
            When set to `True`, drops the MPS table after solve (only CAS)
        replace : boolean, optional
            When set to `True`, replaces an existing MPS table (only CAS and MPS)
        primalin : boolean, optional
            When set to `True`, uses initial values (only MILP)
        verbose : boolean, optional (experimental)
            When set to `True`, prints the generated OPTMODEL code

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

        * Some of the options listed under the ``options`` argument might not be
          passed, depending on which CAS action is being used.
        * The ``option`` argument should be a dictionary, where keys are
          option names. For example, ``m.solve(options={'maxtime': 600})``
          limits the solution time to 600 seconds.
        * See :ref:`solver-options` for a list of solver options.


        """

        return sasoptpy.util.submit_for_solve(self, **kwargs)

    def tune_parameters(self, **kwargs):
        """
        Tunes the model to find ideal solver parameters

        Parameters
        ----------
        kwargs :
           Keyword arguments as defined in the optimization.tuner action.

           Acceptable values are:

           - `milpParameters <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=cas-optimization-tuner.htm&docsetVersion=8.5&locale=en#PYTHON.cas-optimization-tuner-milpparameters>`_:
             Parameters for the solveMilp action, such as
             `maxTime`, `heuristics`, `feasTol`
           - `tunerParameters <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=cas-optimization-tuner.htm&docsetVersion=8.5&locale=en#PYTHON.cas-optimization-tuner-tunerparameters>`_:
             Parameters for the tuner itself, such as
             `maxConfigs`, `printLevel`, `logFreq`
           - `tuningParameters <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=cas-optimization-tuner.htm&docsetVersion=8.5&locale=en#PYTHON.cas-optimization-tuner-tuningparameters>`_:
             List of parameters to be tuned, such as
             `cutStrategy`, `presolver`, `restarts`

        Returns
        -------
        tunerResults : :class:`swat.dataframe.SASDataFrame`
           Tuning results as a table

        Examples
        --------

        >>> m = so.Model(name='model1')
        >>> ...
        >>> results = m.tune_parameters(tunerParameters={'maxConfigs': 10})
        NOTE: Initialized model knapsack_with_tuner.
        NOTE: Added action set 'optimization'.
        NOTE: Uploading the problem DataFrame to the server.
        NOTE: Cloud Analytic Services made the uploaded file available as table KNAPSACK_WITH_TUNER in caslib CASUSER(casuser).
        NOTE: The table KNAPSACK_WITH_TUNER has been created in caslib CASUSER(casuser) from binary data uploaded to Cloud Analytic Services.
        NOTE: Start to tune the MILP
                 SolveCalls  Configurations    BestTime        Time
                          1               1        0.21        0.26
                          2               2        0.19        0.50
                          3               3        0.19        0.72
                          4               4        0.19        0.95
                          5               5        0.19        1.17
                          6               6        0.19        1.56
                          7               7        0.18        1.76
                          8               8        0.17        1.96
                          9               9        0.17        2.16
                         10              10        0.17        2.35
        NOTE: Configuration limit reached.
        NOTE: The tuning time is 2.35 seconds.
        >>> print(results)
           Configuration conflictSearch  ... Sum of Run Times Percentage Successful
        0            0.0      automatic  ...             0.20                 100.0
        1            1.0           none  ...             0.17                 100.0
        2            2.0           none  ...             0.17                 100.0
        3            3.0       moderate  ...             0.17                 100.0
        4            4.0           none  ...             0.18                 100.0
        5            5.0           none  ...             0.18                 100.0
        6            6.0     aggressive  ...             0.18                 100.0
        7            7.0       moderate  ...             0.18                 100.0
        8            8.0     aggressive  ...             0.19                 100.0
        9            9.0      automatic  ...             0.36                 100.0


        >>> results = m.tune_parameters(
               milpParameters={'maxtime': 10},
               tunerParameters={'maxConfigs': 20, 'logfreq': 5},
               tuningParameters=[
                  {'option': 'presolver', 'initial': 'none', 'values': ['basic', 'aggressive', 'none']},
                  {'option': 'cutStrategy'},
                  {'option': 'strongIter', 'initial': -1, 'values': [-1, 100, 1000]}
               ])
        NOTE: Added action set 'optimization'.
        NOTE: Uploading the problem DataFrame to the server.
        NOTE: Cloud Analytic Services made the uploaded file available as table KNAPSACK_WITH_TUNER in caslib CASUSER(casuser).
        NOTE: The table KNAPSACK_WITH_TUNER has been created in caslib CASUSER(casuser) from binary data uploaded to Cloud Analytic Services.
        NOTE: Start to tune the MILP
                 SolveCalls  Configurations    BestTime        Time
                          5               5        0.17        1.01
                         10              10        0.17        2.00
                         15              15        0.17        2.98
                         20              20        0.17        3.95
        NOTE: Configuration limit reached.
        NOTE: The tuning time is 3.95 seconds.
        >>> print(results)
            Configuration conflictSearch  ... Sum of Run Times Percentage Successful
        0             0.0      automatic  ...             0.17                 100.0
        1             1.0           none  ...             0.16                 100.0
        2             2.0           none  ...             0.16                 100.0
        3             3.0           none  ...             0.16                 100.0
        4             4.0           none  ...             0.16                 100.0
        5             5.0           none  ...             0.17                 100.0
        6             6.0           none  ...             0.17                 100.0
        7             7.0           none  ...             0.17                 100.0
        8             8.0           none  ...             0.17                 100.0
        9             9.0           none  ...             0.17                 100.0
        10           10.0           none  ...             0.17                 100.0
        11           11.0     aggressive  ...             0.17                 100.0
        12           12.0           none  ...             0.17                 100.0
        13           13.0     aggressive  ...             0.17                 100.0
        14           14.0      automatic  ...             0.17                 100.0
        15           15.0           none  ...             0.17                 100.0
        16           16.0           none  ...             0.17                 100.0
        17           17.0       moderate  ...             0.17                 100.0
        18           18.0       moderate  ...             0.17                 100.0
        19           19.0           none  ...             0.17                 100.0

        Notes
        -----
        - See `SAS Optimization documentation
          <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=cas-optimization-tuner.htm&docsetVersion=8.5&locale=en#PYTHON.cas-optimization-tuner-tunerparameters>`_
          for a full list of tunable parameters.
        - See `Optimization Action Set documentation
          <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=casactmopt_optimization_details35.htm&docsetVersion=8.5&locale=en>`_.

        See also
        --------
        :meth:`Model.get_tuner_results`
        """
        return sasoptpy.util.submit_for_tune(self, **kwargs)

    def _set_abstract_values(self, name, value):
        """
        Searches for the missing/abstract variable names and set their values
        """
        original_name = sasoptpy.util.get_group_name(name)
        group = self.get_variable(original_name)
        if group is not None:
            v = group.get_member_by_name(name)
            v.set_value(value)

    def clear_solution(self):
        """
        Clears the cached solution of the model

        Notes
        -----
        - This method cleans the optimal objective value and solution time
          parameters of the model.
        """
        self._objval = None
        self.response = None
        self._soltime = 0

