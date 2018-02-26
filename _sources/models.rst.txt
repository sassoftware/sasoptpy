
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
is to use the :func:`Model.include` function:

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

A model is solved using the :func:`Model.solve` function. This function converts
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
NOTE: Data length = 189 rows
NOTE: Conversion to MPS =   0.0010 secs
NOTE: Upload to CAS time =  0.0710 secs
NOTE: Solution parse time = 0.1900 secs
NOTE: Server solve time =   0.1560 secs

Solve options
~~~~~~~~~~~~~

All options listed for the CAS solveLp and solveMilp actions can be used through
:func:`Model.solve` function.
LP options can passed to :func:`Model.solve` using ``lp`` argument, while MILP
options can be passed using ``milp`` argument:

>>> m.solve(milp={'maxtime': 600})
>>> m.solve(lp={'algorithm': 'ipm'})

See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvelp_syntax.htm&locale=en for a list of LP options.

See http://go.documentation.sas.com/?cdcId=vdmmlcdc&cdcVersion=8.11&docsetId=casactmopt&docsetTarget=casactmopt_solvemilp_syntax.htm&locale=en for a list of MILP options.

Getting solutions
~~~~~~~~~~~~~~~~~

After the solve is completed, all variable and constraint values are parsed
automatically.
A summary of the problem can be accessed using the 
:func:`Model.get_problem_summary` function, 
and a summary of the solution can be accesed using the
:func:`Model.get_solution_summary`
function.

To print values of any object, :func:`get_solution_table` can be used:

>>> print(so.get_solution_table(x, y))

All variables and constraints passed into this function are returned based on
their indices. See :ref:`examples` for more details.


