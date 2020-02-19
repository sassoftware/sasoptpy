
.. currentmodule:: sasoptpy

.. _components:

Model components
=================

.. ipython:: python
   :suppress:
   
   import os
   cas_host = os.getenv('CASHOST')
   cas_port = os.getenv('CASPORT')
   cas_username = os.getenv('CASUSERNAME')
   cas_password = None
   from swat import CAS
   s = CAS(cas_host, port=cas_port)
   import sasoptpy
   sasoptpy.reset_globals()

In this section, several model components are discussed with examples.
See :ref:`examples` to learn more about how you can use these components to define optimization models.

.. ipython:: python
   :suppress:

   import sasoptpy as so
   from swat import CAS
   s = CAS(hostname=cas_host, username=cas_username, password=cas_password, port=cas_port)
   m = so.Model(name='demo', session=s)

Expressions
-----------

:class:`Expression` objects represent linear and nonlinear mathematical
expressions in *sasoptpy*.

Creating expressions
~~~~~~~~~~~~~~~~~~~~

You can create an :class:`Expression` object as follows:

.. ipython:: python
   :suppress:

   sales = m.add_variable(name='sales')
   material = m.add_variable(name='material')

.. ipython:: python

   profit = so.Expression(5 * sales - 3 * material, name='profit')
   print(repr(profit))


Nonlinear expressions
~~~~~~~~~~~~~~~~~~~~~

:class:`Expression` objects are linear by default. It is possible to create
nonlinear expressions, but there are some limitations.

.. ipython:: python

   nonexp = sales ** 2 + (1 / material) ** 3
   print(nonexp)


Currently, it is not possible to get or print values of nonlinear expressions.
Moreover, if your model includes a nonlinear expression, you need to use
SAS Viya 3.4 or later or any SAS version for solving your problem.

To use mathematical operations, you need to import `sasoptpy.math`
functions.

Mathematical expressions
~~~~~~~~~~~~~~~~~~~~~~~~

*sasoptpy* provides mathematical functions for generating mathematical
expressions to be used in optimization models.

You need to import `sasoptpy.math` to your code to start by using these functions.
Available mathematical functions are listed in :ref:`math-functions`.

.. ipython:: python

   import sasoptpy.math as sm
   newexp = sm.max(sales, 10) ** 2
   print(newexp._expr())

.. ipython:: python

   import sasoptpy.math as sm
   angle = so.Variable(name='angle')
   newexp = sm.sin(angle) ** 2 + sm.cos(angle) ** 2
   print(newexp._expr())


Operations
~~~~~~~~~~

**Getting the current value**

After the solve is completed, you can obtain the current value of an expression by using the
:func:`Expression.get_value` method:

>>> print(profit.get_value())
42.0

**Getting the dual value**

You can retrieve the dual values of :class:`Expression` objects by using
:func:`Variable.get_dual` and :func:`Constraint.get_dual` methods.

>>> m.solve()
>>> ...
>>> print(x.get_dual())
1.0


**Addition**

There are two ways to add elements to an expression.
The first and simpler way creates a new expression at the end:

.. ipython:: python
   
   tax = 0.5
   profit_after_tax = profit - tax

.. ipython:: python
   
   print(repr(profit_after_tax))


The second way, :func:`Expression.add` method, takes two arguments:
the element to be added and the sign (1 or -1):

.. ipython:: python
   
   profit_after_tax = profit.add(tax, sign=-1)
   
.. ipython:: python

   print(profit_after_tax)

.. ipython:: python
   
   print(repr(profit_after_tax))

If the expression is a temporary one, the addition is performed in place.


**Multiplication**

You can multiply expressions with scalar values:

.. ipython:: python

   investment = profit.mult(0.2)
   print(investment)

**Summation**

For faster summations compared to Python's native :code:`sum` function,
*sasoptpy* provides :func:`sasoptpy.quick_sum`.

.. ipython:: python

   import time
   x = m.add_variables(1000, name='x')

.. ipython:: python

   t0 = time.time()
   e = so.quick_sum(2 * x[i] for i in range(1000))
   print(time.time()-t0)

.. ipython:: python

   t0 = time.time()
   f = sum(2 * x[i] for i in range(1000))
   print(time.time()-t0)

Renaming an expression
~~~~~~~~~~~~~~~~~~~~~~

You can rename expressions by using the :func:`Expression.set_name` method:

.. ipython:: python

   e = so.Expression(x[5] + 2 * x[6], name='e1')
   print(repr(e))

.. ipython:: python
   
   e.set_name('e2');
   print(repr(e))


Copying an expression
~~~~~~~~~~~~~~~~~~~~~

You can copy an :class:`Expression` by using the :func:`Expression.copy` method:

.. ipython:: python

   copy_profit = profit.copy(name='copy_profit')
   print(repr(copy_profit))


Objective Functions
-------------------


Setting and getting an objective function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use any valid :class:`Expression` as the objective function of a model.
You can also use an existing expression as an objective function by using
the :func:`Model.set_objective` method. The objective function of a model can
be obtained by using the :func:`Model.get_objective` method.

>>> profit = so.Expression(5 * sales - 2 * material, name='profit')
>>> m.set_objective(profit, so.MAX)
>>> print(m.get_objective())
 -  2.0 * material  +  5.0 * sales


Getting the value
~~~~~~~~~~~~~~~~~

After a solve, you can retrieve the objective value by using the
:func:`Model.get_objective_value` method.

>>> m.solve()
>>> print(m.get_objective_value())
42.0


Variables
---------

Creating variables
~~~~~~~~~~~~~~~~~~

You can create variables either standalone or inside a model.

**Creating a variable outside a model**

The first way to create a variable uses the default constructor.

>>> x = so.Variable(vartype=so.INT, ub=5, name='x')

When created separately, a variable needs to be included (or added) inside the
model:

>>> y = so.Variable(name='y', lb=5)
>>> m.add_variable(y)

Equivalently, you could do this in one step:

>>> y = m.add_variable(name='y', lb=5) 

**Creating a variable inside a model**

The second way is to use :func:`Model.add_variable`. This method creates
a :class:`Variable` object and returns a pointer.

>>> x = m.add_variable(vartype=so.INT, ub=5, name='x')

Arguments
~~~~~~~~~

There are three types of variables: continuous variables, integer variables,
and binary variables.
Continuous variables are the default type and
you can specify it by using the ``vartype=so.CONT`` argument.
You can create Integer variables and binary
variables by using the ``vartype=so.INT`` and ``vartype=so.BIN``
arguments, respectively.

The default lower bound for variables is 0, and the upper bound is infinity.
Name is a required argument.

Changing bounds
~~~~~~~~~~~~~~~

The :func:`Variable.set_bounds` method changes the bounds of a variable.

>>> x = so.Variable(name='x', lb=0, ub=20)
>>> print(repr(x))
sasoptpy.Variable(name='x', lb=0, ub=20, vartype='CONT')
>>> x.set_bounds(lb=5, ub=15)
>>> print(repr(x))
sasoptpy.Variable(name='x', lb=5, ub=15, vartype='CONT')

Setting initial values
~~~~~~~~~~~~~~~~~~~~~~

You can pass the initial values of variables to the solvers for certain problems.
The :func:`Variable.set_init` method changes the initial value for variables.
You can set this value at the creation of the variable as well.

>>> x.set_init(5)
>>> print(repr(x))
sasoptpy.Variable(name='x', ub=20, init=5,  vartype='CONT')

Working with a set of variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create a set of variables by using single or multiple indices.
Valid index sets include list, dict, and :class:`pandas.Index` objects. 
See :ref:`input-data` for more information about allowed index types.

**Creating a set of variables outside a model**

>>> production = VariableGroup(PERIODS, vartype=so.INT, name='production',
                               lb=min_production)
>>> print(repr(production))
sasoptpy.VariableGroup(['Period1', 'Period2', 'Period3'], name='production')
>>> m.include(production)


**Creating a set of variables inside a model**

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


Constraints
-----------

Creating constraints
~~~~~~~~~~~~~~~~~~~~

Similar to :class:`Variable` objects, you can create :class:`Constraint` objects inside or outside optimization models.

**Creating a constraint outside a model**

>>> c1 = so.Constraint(3 * x - 5 * y <= 10, name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

**Creating a constraint inside a model**

>>> c1 = m.add_constraint(3 * x - 5 * y <= 10, name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')


Modifying variable coefficients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can update the coefficient of a variable inside a constraint by using the
:func:`Constraint.update_var_coef` method:

>>> c1 = so.Constraint(exp=3 * x - 5 * y <= 10, name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')
>>> c1.update_var_coef(x, -1)
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  -  x  <=  10, name='c1')


Working with a set of constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add a set of constraints by using single or multiple indices.
Valid index sets include list, dict, and :class:`pandas.Index` objects. 
See :ref:`input-data` for more information about allowed index types.

**Creating a set of constraints outside a model**

>>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
>>> cg = so.ConstraintGroup((2 * z[i, j] + 3 * z[i-1, j] >= 2 for i in
                             [1] for j in ['a', 'b', 'c']), name='cg')
>>> print(cg)
Constraint Group (cg) [
  [(1, 'a'):  3.0 * z[0, 'a']  +  2.0 * z[1, 'a']  >=  2]
  [(1, 'b'):  3.0 * z[0, 'b']  +  2.0 * z[1, 'b']  >=  2]
  [(1, 'c'):  2.0 * z[1, 'c']  +  3.0 * z[0, 'c']  >=  2]
]


**Creating a set of constraints inside a model**

>>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
>>> cg2 = m.add_constraints((2 * z[i, j] + 3 * z[i-1, j] >= 2 for i in
                              [1] for j in ['a', 'b', 'c']), name='cg2')
>>> print(cg2)
Constraint Group (cg2) [
  [(1, 'a'):  2.0 * z[1, 'a']  +  3.0 * z[0, 'a']  >=  2]
  [(1, 'b'):  3.0 * z[0, 'b']  +  2.0 * z[1, 'b']  >=  2]
  [(1, 'c'):  2.0 * z[1, 'c']  +  3.0 * z[0, 'c']  >=  2]
]

Range constraints
~~~~~~~~~~~~~~~~~

You can give a range for an expression by using a list of two value (lower and
upper bound) with an `==` sign:

>>> x = m.add_variable(name='x')
>>> y = m.add_variable(name='y')
>>> c1 = m.add_constraint(x + 2*y == [2,9], name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( x + 2.0 * y  ==  [2, 9], name='c1')
