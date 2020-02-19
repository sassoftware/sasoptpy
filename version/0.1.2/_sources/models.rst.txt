
.. currentmodule:: sasoptpy

.. _models:

Sessions and Models
===================

CAS Sessions
------------

A :class:`swat.cas.connection.CAS` session is needed to solve optimization 
problems with **sasoptpy**.
See SAS documentation to learn more about CAS sessions and SAS Viya.

A sample CAS Session can be created using the following commands.

.. ipython:: python
   :suppress:
   
   import os
   cas_host = os.getenv('CASHOST')
   cas_port = os.getenv('CASPORT')
   cas_username = os.getenv('CASUSERNAME')
   cas_password = None
   import sasoptpy
   sasoptpy.reset_globals()

.. ipython:: python
   :suppress:

   import sasoptpy as so
   from swat import CAS
   s = CAS(hostname=cas_host, username=cas_username, password=cas_password, port=cas_port)
   m = so.Model(name='demo', session=s)
   print(repr(m))


>>> import sasoptpy as so
>>> from swat import CAS
>>> s = CAS(hostname=cas_host, username=cas_username, password=cas_password, port=cas_port)
>>>  m = so.Model(name='demo', session=s)
>>> print(repr(m))
sasoptpy.Model(name='demo', session=CAS(hostname, port, username, protocol='cas', name='py-session-1', session=session-no))


Models
------

Creating a model
~~~~~~~~~~~~~~~~

An empty model can be created using the :class:`Model` constructor:

.. ipython:: python

   import sasoptpy as so
   m = so.Model(name='model1')
   
Adding new components to a model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding a variable:

.. ipython:: python

   x = m.add_variable(name='x', vartype=so.BIN)
   print(m)
   y = m.add_variable(name='y', lb=1, ub=10)
   print(m)

Adding a constraint:

.. ipython:: python

   c1 = m.add_constraint(x + 2 * y <= 10, name='c1')
   print(m)
   
Adding existing components to a model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A new model can use existing variables. The typical way to include a variable
is to use the :func:`Model.include` method:

.. ipython:: python

   new_model = so.Model(name='new_model')
   new_model.include(x, y)
   print(new_model)
   new_model.include(c1)
   print(new_model)
   z = so.Variable(name='z', vartype=so.INT, lb=3)
   new_model.include(z)
   print(new_model)

Note that variables are added to :class:`Model` objects by reference.
Therefore, after :func:`Model.solve` is called, values of variables will be
replaced with optimal values.

Accessing components
~~~~~~~~~~~~~~~~~~~~

You can get a list of model variables using :func:`Model.get_variables()`
method.

.. ipython:: python

   print(m.get_variables())

Similarly, you can access a list of constraints using
:func:`Model.get_constraints()` method. 

.. ipython:: python

   c2 = m.add_constraint(2 * x - y >= 1, name='c2')
   print(m.get_constraints())

To access a certain constraint using its name, you can use
:func:`Model.get_constraint` method:

.. ipython:: python

   print(m.get_constraint('c2'))


Dropping components
~~~~~~~~~~~~~~~~~~~

A variable inside a model can simply be dropped using 
:func:`Model.drop_variable`. Similarly, a set of variables can be dropped
using :func:`Model.drop_variables`.

.. ipython:: python

   m.drop_variable(y)
   print(m)

.. ipython:: python
   
   m.include(y)
   print(m)

A constraint can be dropped using :func:`Model.drop_constraint` method.
Similarly, a set of constraints can be dropped using
:func:`Model.drop_constraints`.

.. ipython:: python

   m.drop_constraint(c1)
   m.drop_constraint(c2)
   print(m)

.. ipython:: python

   m.include(c1)
   print(m)


Copying a model
~~~~~~~~~~~~~~~

An exact copy of the existing model can be obtained by including the :class:`Model`
object itself.

.. ipython:: python

   copy_model = so.Model(name='copy_model')
   copy_model.include(m)
   print(copy_model)

Note that all variables and constraints are included by reference.


Solving a model
~~~~~~~~~~~~~~~

A model is solved using the :func:`Model.solve` method. This method converts
Python definitions into an MPS file and uploads to a CAS server for the optimization
action. The type of the optimization problem (Linear Optimization or Mixed Integer
Linear Optimization) is determined based on variable types.

>>> m.solve()
NOTE: Initialized model model_1
NOTE: Converting model model_1 to DataFrame
NOTE: Added action set 'optimization'.
...
NOTE: Optimal.
NOTE: Objective = 124.343.
NOTE: The Dual Simplex solve time is 0.01 seconds.

Solve options
~~~~~~~~~~~~~

**Solver Options**

All options listed for the CAS solveLp and solveMilp actions can be used through
:func:`Model.solve` method.
LP options can passed to :func:`Model.solve` using ``lp`` argument, while MILP
options can be passed using ``milp`` argument:

>>> m.solve(milp={'maxtime': 600})
>>> m.solve(lp={'algorithm': 'ipm'})

See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvelp_syntax.htm&locale=en for a list of LP options.

See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvemilp_syntax.htm&locale=en for a list of MILP options.

**Package Options**

Besides ``lp`` and ``milp`` arguments, there are 4 arguments that can be passed
into :func:`Model.solve` method:

- name: Upload name of the MPS data
- drop: Option for dropping the data from server after solve
- replace: Option for replacing an existing data with the same name
- primalin: Option for using the current values of the variables as an initial solution

When ``primalin`` argument is ``True``, it grabs :class:`Variable` objects
``_init`` field. This field can be modified with :func:`Variable.set_init`
method.


Getting solutions
~~~~~~~~~~~~~~~~~

After the solve is completed, all variable and constraint values are parsed
automatically.
A summary of the problem can be accessed using the 
:func:`Model.get_problem_summary` method, 
and a summary of the solution can be accesed using the
:func:`Model.get_solution_summary`
method.

To print values of any object, :func:`get_solution_table` can be used:

>>> print(so.get_solution_table(x, y))

All variables and constraints passed into this method are returned based on
their indices. See :ref:`examples` for more details.


