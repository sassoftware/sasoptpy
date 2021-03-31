
.. currentmodule:: sasoptpy

.. _basics:

Quick Reference
***************

This is a short introduction to sasoptpy functionality, mainly for new users.
You can find more details in the linked chapters.

Using sasoptpy usually consists of the following steps:

1. Create a :ref:`CAS session <cas-sessions>` or a :ref:`SAS session <sas-sessions>`
2. Initialize the :ref:`model <models>`
3. Process the :ref:`input data <input-data>`
4. Add the :ref:`model components <components>`
5. :ref:`Solve the model <solving-model>`

Solving an optimization problem via sasoptpy
starts with having a running CAS (SAS Viya) Server or having a SAS 9.4 installation.
It is possible to model a problem without a connection
but solving a problem requires access to SAS Optimization or SAS/OR solvers at runtime.

Creating a session
------------------

Creating a SAS Viya session
+++++++++++++++++++++++++++

To create a SAS Viya session (also called a CAS session), see `SWAT documentation <https://sassoftware.github.io/python-swat/generated/swat.cas.connection.CAS.html#swat-cas-connection-cas>`_.
A simple connection can be made using:

.. ipython:: python
   :suppress:

   import os
   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   userid = None
   password = None

.. ipython:: python

   from swat import CAS
   s = CAS(hostname, port, userid, password)

The last two parameters are optional for some use
cases.

Creating a SAS 9.4 session
++++++++++++++++++++++++++

To create a SAS 9.4 session (also called a SAS session), see
`SASPy documentation <https://sassoftware.github.io/saspy/getting-started.html#start-a-sas-session>`_.
After customizing the configurations for your setup, you can create a session as follows:

.. code-block:: python

   import saspy
   s = saspy.SASsession(cfgname='winlocal')

Initializing a model
--------------------

After creating a CAS or SAS session, you can create an empty model as follows:

.. ipython:: python

   import sasoptpy as so
   m = so.Model(name='my_first_model', session=s)

This command initializes the optimization model as a :class:`Model` object, called `m`.

Processing input data
---------------------

The easiest way to work with sasoptpy is to
define problem inputs as pandas DataFrames.
You can define objective and cost coefficients, and lower and upper bounds by using the DataFrame and Series objects, respectively.
See
`pandas documentation <http://pandas.pydata.org/pandas-docs/stable/>`_
to learn more.

.. ipython:: python

   import pandas as pd
   prob_data = pd.DataFrame([
       ['Period1', 30, 5],
       ['Period2', 15, 5],
       ['Period3', 25, 0]
       ], columns=['period', 'demand', 'min_prod']).set_index(['period'])
   price_per_product = 10
   capacity_cost = 10

You can refer the set ``PERIODS`` and the other fields ``demand`` and ``min_production`` as follows:

.. ipython:: python

   PERIODS = prob_data.index.tolist()
   demand = prob_data['demand']
   min_production = prob_data['min_prod']

Adding variables
----------------

You can add a single variable or a set of variables to :class:`Model` objects.

* :meth:`Model.add_variable` method is used to add a single variable.
  
  .. ipython:: python
  
     production_cap = m.add_variable(vartype=so.INT, name='production_cap', lb=0)
  
  When working with multiple models, you can create a variable independent of
  the model, such as

  >>> production_cap = so.Variable(name='production_cap', vartype=so.INT, lb=0)
  
  Then you can add it to an existing model by using :meth:`Model.include`:

  >>> m.include(production_cap)

* :meth:`Model.add_variables` method is used to add a set of variables.
  
  .. ipython:: python
  
     production = m.add_variables(PERIODS, vartype=so.INT, name='production',
	                          lb=min_production)
  
  When the input is a set of variables, you can retrieve individual variables by
  using individual keys, such as ``production['Period1']``.
  To create multidimensional variables, simply list all the keys as follows:

  >>> multivar = m.add_variables(KEYS1, KEYS2, KEYS3, name='multivar')

Creating expressions
--------------------

:class:`Expression` objects hold mathematical expressions.
Although these objects are mostly used under the hood when defining a model,
it is possible to define a custom :class:`Expression` to use later.

When :class:`Variable` objects are used in a mathematical expression, sasoptpy creates an :class:`Expression` object
automatically:

.. ipython:: python

   totalRevenue = production.sum('*')*price_per_product
   totalCost = production_cap * capacity_cost

Note the use of the :meth:`VariableGroup.sum` method
over a variable group. This method returns the sum of variables inside the
group as an :class:`Expression` object. Its multiplication with a scalar
``price_per_product`` gives the final expression.

Similarly, ``totalCost`` is simply multiplication of a :class:`Variable` object
with a scalar.

Setting an objective function
-----------------------------

You can define objective functions in terms of expressions.
In this problem, the objective is to maximize the profit, so the
:func:`Model.set_objective` method is used as follows:

.. ipython:: python
   
   m.set_objective(totalRevenue-totalCost, sense=so.MAX, name='totalProfit')

Notice that you can define the same objective by using:

>>> m.set_objective(production.sum('*')*price_per_product - production_cap*capacity_cost, sense=so.MAX, name='totalProfit')

The mandatory argument ``sense`` should be assigned the value of either ``so.MIN`` for a minimization problem
or ``so.MAX`` for a maximization problems.

Adding constraints
------------------

In sasoptpy, constraints are simply expressions that have a direction.
It is possible to define an expression and add it to a model by defining which
direction the linear relation should have.

There are two methods to add constraints. The first
is :meth:`Model.add_constraint`, which adds a single constraint to amodel.

The second is :meth:`Model.add_constraints`, which adds multiple constraints to a model.

.. ipython:: python
   
   m.add_constraints((production[i] <= production_cap for i in PERIODS),
	             name='capacity')
   
.. ipython:: python

   m.add_constraints((production[i] <= demand[i] for i in PERIODS),
	             name='demand')

The first term, provides a Python generator, which is then translated into
constraints in the problem. The symbols ``<=``, ``>=``, and ``==`` are used for
less than or equal to, greater than or equal to, and equal to,
respectively. You can define range constraints by using the ``==`` symbol followed by a list of two
values that represent lower and upper bounds.

.. ipython:: python

   m.add_constraint(production['Period1'] == [10, 100], name='production_bounds')

Solving a problem
-----------------

After a problem is defined, you can send it to the CAS server or SAS session by calling the
:func:`Model.solve` method, which returns the primal solution when it is available,
and ``None`` otherwise.

.. ipython:: python
   
   m.solve()

At the end of the solve operation, the solver returns 
a "Problem Summary" table and a "Solution Summary" table. These tables can
later be accessed by using ``m.get_problem_summary()`` and
``m.get_solution_summary()``.

.. ipython:: python

   print(m.get_solution_summary())


Printing solutions
------------------

You can retrieve the solutions by using the
:func:`get_solution_table` method. It is strongly suggested that you group
variables and expressions that share the same keys in a call.

.. ipython:: python

   print(so.get_solution_table(demand, production))


Initializing a workspace
------------------------

If you want to use the extensive abstract modeling capabilities of sasoptpy,
you can create a workspace.
Workspaces support features such as server-side for loops,
cofor loops (parallel), reading and creating CAS tables.
You can initialize a :class:`Workspace` by using Python's
:code:`with` keyword.
For example, you can create a workspace that has a set and a variable group as follows:

.. ipython:: python

   def create_workspace():
      with so.Workspace(name='my_workspace', session=s) as w:
         I = so.Set(name='I', value=range(1, 11))
         x = so.VariableGroup(I, name='x', lb=0)
      return w

.. ipython:: python

   workspace = create_workspace()
   print(so.to_optmodel(workspace))


You can submit a workspace to a CAS server and retrieve the response by using:

.. ipython:: python

   workspace.submit()


.. _configurations:

Package configurations
----------------------

sasoptpy comes with certain package configurations.
The configuration parameters and their default values are as follows:

- verbosity (default 3)
- max_digits (default 12)
- print_digits (default 6)
- default_sense (default so.minimization)
- default_bounds
- valid_outcomes

It is possible to override these configuration parameters.
As an example, consider the following constraint representation:

.. ipython:: python

   x = so.Variable(name='x')
   c = so.Constraint(10 / 3 * x + 1e-20 * x ** 2 <= 30 + 1e-11, name='c')
   print(so.to_definition(c))

You can change the number of digits to be printed as follows:

.. ipython:: python

   so.config['max_digits'] = 2

.. ipython:: python

   print(so.to_definition(c))

You can remove the maximum number of digits to print as follows:

.. ipython:: python

   so.config['max_digits'] = None

.. ipython:: python

   print(so.to_definition(c))

You can reset the parameter to its default value by deleting the parameter:

.. ipython:: python

   del so.config['max_digits']

You can also create a new configuration to be used globally:

.. ipython:: python

   so.config['myvalue'] = 2


