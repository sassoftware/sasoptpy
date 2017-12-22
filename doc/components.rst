
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

In this part, several model components are discussed with examples. 
See :ref:`examples` to learn more about how these components can be used to
define optimization models.

.. ipython:: python
   :suppress:

   import sasoptpy as so
   from swat import CAS
   s = CAS(hostname=cas_host, username=cas_username, password=cas_password, port=cas_port)
   m = so.Model(name='demo', session=s)

Expressions
-----------

:class:`Expression` objects represent linear expressions in **sasoptpy**.

Creating expressions
~~~~~~~~~~~~~~~~~~~~

An :class:`Expression` can be created as follows:

.. ipython:: python
   :suppress:

   sales = m.add_variable(name='sales')
   material = m.add_variable(name='material')

.. ipython:: python

   profit = so.Expression(5 * sales - 3 * material, name='profit')
   print(repr(profit))

Operations
~~~~~~~~~~

**Getting the current value**

After the solve is completed, the current value of an expression can be
obtained using the :func:`Expression.get_value` function:

>>> print(profit.get_value())
42.0

**Addition**

There are two ways to add elements to an expression.
The first and simpler way creates a new expression at the end:

.. ipython:: python
   
   tax = 0.5
   profit_after_tax = profit - tax

.. ipython:: python
   
   print(repr(profit_after_tax))


The second way, :func:`Expression.add` function, takes two arguments:
the element to be added and the sign (1 or -1):

.. ipython:: python
   
   profit_after_tax = profit.add(tax, sign=-1)
   
.. ipython:: python

   print(profit_after_tax)

.. ipython:: python
   
   print(repr(profit_after_tax))

If the expression is a temporary one, then the addition is performed in place.


**Multiplication**

You can only multiply a number with an existing :class:`Expression` object:

.. ipython:: python

   investment = profit.mult(0.2)
   print(investment)

Copying an expression
~~~~~~~~~~~~~~~~~~~~~

An :class:`Expression` can be copied using :func:`Expression.copy`.

.. ipython:: python

   copy_profit = profit.copy(name='copy_profit')
   print(repr(copy_profit))

Temporary expressions
~~~~~~~~~~~~~~~~~~~~~

An :class:`Expression` object can be defined as temporary, which enables 
faster :func:`Expression.sum` and :func:`Expression.mult` operations.

.. ipython:: python

   new_profit = so.Expression(10 * sales - 2 * material, temp=True)
   print(repr(new_profit))

The expression can be modified inside a function:

.. ipython:: python

   new_profit + 5

.. ipython:: python

   print(repr(new_profit))

As you can see, the value of ``new_profit`` is changed due to an in-place addition.
To prevent the change, such expressions can be converted to permanent expressions
using the :func:`Expression.set_permanent` function or constructor:

.. ipython:: python

   new_profit = so.Expression(10 * sales - 2 * material, temp=True)
   new_profit.set_permanent()
   tmp = new_profit + 5
   print(repr(new_profit))


Objective Functions
-------------------


Setting and getting an objective function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any valid :class:`Expression` can be used as the objective function of a model.
An existing expression can be used as an objective function using
the :func:`Model.set_objective` function. The objective function of a model can
be obtained using the :func:`Model.get_objective` function.

>>> profit = so.Expression(5 * sales - 2 * material, name='profit')
>>> m.set_objective(profit, so.MAX)
>>> print(m.get_objective())
 -  2.0 * material  +  5.0 * sales


Getting the value
~~~~~~~~~~~~~~~~~

After a solve, the objective value can be checked using the
:func:`Expression.get_objective_value` function.

>>> m.solve()
>>> print(m.get_objective_value())
42.0


Variables
---------

Creating variables
~~~~~~~~~~~~~~~~~~

Variables can be created either separately or inside a model.

**Creating a variable outside a model**

The first way to create a variable uses the default constructor.

>>> x = so.Variable(vartype=so.INT, ub=5, name='x')

When created separately, a variable needs to be included (or added) inside the
model:

>>> y = so.Variable(name='y', lb=5)
>>> m.add_variable(y)

and

>>> y = m.add_variable(name='y', lb=5) 

are equivalent.

**Creating a variable inside a model**

The second way is to use :func:`Model.add_variable`. This function creates
a :class:`Variable` object and returns a pointer.

>>> x = m.add_variable(vartype=so.INT, ub=5, name='x')


Arguments
~~~~~~~~~

There are three types of variables: continuous variables, integer variables,
and binary variables. Continuous variables are the default type and can be
created using the ``vartype=so.CONT`` argument. Integer variables and binary
variables can be created using the ``vartype=so.INT`` and ``vartype=so.BIN``
arguments, respectively.

The default lower bound for variables is 0, and the upper bound is infinity.
Name is a required argument. If the given name already exists in the 
namespace, then a different generic name can be used for the variable.
The :func:`reset_globals` function can be 
used to reset sasoptpy namespace when needed.

Changing bounds
~~~~~~~~~~~~~~~

The function :func:`Variable.set_bounds` can change the bounds of a variable.

>>> x = so.Variable(name='x', lb=0, ub=20)
>>> print(repr(x))
sasoptpy.Variable(name='x', lb=0, ub=20, vartype='CONT')
>>> x.set_bounds(lb=5, ub=15)
>>> print(repr(x))
sasoptpy.Variable(name='x', lb=5, ub=15, vartype='CONT')


Working with a set of variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A set of variables can be added using single or multiple indices.
Valid index sets include list, dict, and :class:`pandas.Index` objects. 
See :ref:`input-data` for more about allowed index types.

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

Similar to :class:`Variable` objects, :class:`Constraint` objects can be
created inside or outside optimization models.

**Creating a constraint outside a model**

>>> c1 = sasoptpy.Constraint(3 * x - 5 * y <= 10, name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

**Creating a constraint inside a model**

>>> c1 = m.add_constraint(3 * x - 5 * y <= 10, name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')


Modifying variable coefficients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The coefficient of a variable inside a constraint can be updated using the
:func:`Constraint.update_var_coef` function:

>>> c1 = so.Constraint(exp=3 * x - 5 * y <= 10, name='c1')
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')
>>> c1.update_var_coef(x, -1)
>>> print(repr(c1))
sasoptpy.Constraint( -  5.0 * y  -  x  <=  10, name='c1')


Working with a set of constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A set of constraints can be added using single or multiple indices.
Valid index sets include list, dict, and :class:`pandas.Index` objects. 
See :ref:`input-data` for more about allowed index types.

**Creating a set of variables outside a model**

>>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
>>> cg = so.ConstraintGroup((2 * z[i, j] + 3 * z[i-1, j] >= 2 for i in
                             [1] for j in ['a', 'b', 'c']), name='cg')
>>> print(cg)
Constraint Group (cg) [
  [(1, 'a'):  3.0 * z[0, 'a']  +  2.0 * z[1, 'a']  >=  2]
  [(1, 'b'):  3.0 * z[0, 'b']  +  2.0 * z[1, 'b']  >=  2]
  [(1, 'c'):  2.0 * z[1, 'c']  +  3.0 * z[0, 'c']  >=  2]
]


**Creating a set of variables inside a model**

>>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
>>> cg2 = m.add_constraints((2 * z[i, j] + 3 * z[i-1, j] >= 2 for i in
                              [1] for j in ['a', 'b', 'c']), name='cg2')
>>> print(cg2)
Constraint Group (cg2) [
  [(1, 'a'):  2.0 * z[1, 'a']  +  3.0 * z[0, 'a']  >=  2]
  [(1, 'b'):  3.0 * z[0, 'b']  +  2.0 * z[1, 'b']  >=  2]
  [(1, 'c'):  2.0 * z[1, 'c']  +  3.0 * z[0, 'c']  >=  2]
]

