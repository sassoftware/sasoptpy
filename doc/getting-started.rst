
.. currentmodule:: sasoptpy

.. _getting-started:

Getting Started
***************

Solving an optimization problem via *sasoptpy*
starts with having a running CAS Server or having a SAS 9.4 installation.
It is possible to model a problem without a server
but solving a problem requires access to SAS/OR solvers.

Creating a session
------------------

Creating a SAS Viya session
+++++++++++++++++++++++++++

*sasoptpy* uses the CAS connection provided by the
swat package.
After installation simply use

.. ipython:: python
   :suppress:

   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   userid = None
   password = None

.. ipython:: python

   from swat import CAS
   s = CAS(hostname, port, userid, password)

The last two parameters are optional for some use
cases.
See `swat Documentation <https://sassoftware.github.io/python-swat/generated/swat.cas.connection.CAS.html#swat-cas-connection-cas>`_
for more details.

Creating a SAS 9.4 session
++++++++++++++++++++++++++

To create a SAS 9.4 session, see
`saspy Documentation <https://sassoftware.github.io/saspy/getting-started.html#start-a-sas-session>`_.
After customizing the configurations for your setup, a session can be created
as follows:

.. code-block:: python

   import saspy
   s = saspy.SASsession(cfgname='winlocal')

Initializing a model
--------------------

After having an active CAS/SAS session, an empty model can be defined as
follows:

.. ipython:: python

   import sasoptpy as so
   m = so.Model(name='my_first_model', session=s)

This command creates an empty model.

Processing input data
---------------------

The easisest way to work with *sasoptpy* is to
define problem inputs as Pandas DataFrames.
Objective and cost coefficients, and 
lower and upper bounds can 
be defined using the
DataFrame and Series objects.
See
`Pandas Documentation <http://pandas.pydata.org/pandas-docs/stable/>`_
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

Set ``PERIODS`` and other fields ``demand``, ``min_production`` can be
extracted as follows

.. ipython:: python

   PERIODS = prob_data.index.tolist()
   demand = prob_data['demand']
   min_production = prob_data['min_prod']

Adding variables
----------------

You can add a single variables or a set of variables to :class:`Model` objects.

* :meth:`Model.add_variable` method is used to add a single variable.
  
  .. ipython:: python
  
     production_cap = m.add_variable(vartype=so.INT, name='production_cap', lb=0)
  
  When working with multiple models, you can create a variable independent of
  the model, such as

  >>> production_cap = so.Variable(name='production_cap', vartype=so.INT, lb=0)
  
  and add it to an existing model using

  >>> m.include(production_cap)

* :meth:`Model.add_variables` method is used to add a set of variables.
  
  .. ipython:: python
  
     production = m.add_variables(PERIODS, vartype=so.INT, name='production',
	                          lb=min_production)
  
  When passed as a set of variables, individual variables can be obtained by
  using individual keys, such as ``production['Period1']``.
  To create multi-dimensional variables, simply list all the keys as

  >>> multivar = m.add_variables(KEYS1, KEYS2, KEYS3, name='multivar')

Creating expressions
--------------------

:class:`Expression` objects keep mathematical expressions.
Although these objects are mostly used under the hood when defining a model,
it is possible to define a custom :class:`Expression` to use later.

.. ipython:: python

   totalRevenue = production.sum('*')*price_per_product
   totalCost = production_cap * capacity_cost

The first thing to notice is the use of the :meth:`VariableGroup.sum` method
over a variable group. This method returns the sum of variables inside the
group as an :class:`Expression` object. Its multiplication with a scalar
``profit_per_product`` gives the final expression.

Similarly, ``totalCost`` is simply multiplication of a :class:`Variable` object
with a scalar.

Setting an objective function
-----------------------------

Objective functions can be written in terms of expressions. 
In this problem, the objective is to maximize the profit, so 
:func:`Model.set_objective` method is used as follows:

.. ipython:: python
   
   m.set_objective(totalRevenue-totalCost, sense=so.MAX, name='totalProfit')

Notice that you can define the same objective using

>>> m.set_objective(production.sum('*')*price_per_product - production_cap*capacity_cost, sense=so.MAX, name='totalProfit')

The mandatory argument ``sense`` should be assigned the value of either ``so.MIN`` or ``so.MAX`` for
minimization or maximization problems, respectively.

Adding constraints
------------------

In *sasoptpy*, constraints are simply expressions with a direction.
It is possible to define an expression and add it to a model by defining which
direction the linear relation should have.

There are two methods to add constraints. The first one
is :meth:`Model.add_constraint` where a single constraint can be inserted into a
model.

The second one is :meth:`Model.add_constraints` where multiple constraints can
be added to a model.

.. ipython:: python
   
   m.add_constraints((production[i] <= production_cap for i in PERIODS),
	             name='capacity')
   
.. ipython:: python

   m.add_constraints((production[i] <= demand[i] for i in PERIODS),
	             name='demand')

Here, the first term provides a Python generator, which then gets translated into
constraints in the problem. The symbols ``<=``, ``>=``, and ``==`` are used for
less than or equal to, greater than or equal to, and equal to constraints,
respectively. Range constraints can be inserted using ``==`` and a list of 2
values representing lower and upper bounds.

Solving a problem
-----------------

Defined problems can be simply sent to CAS server or SAS sesion by calling the 
:func:`Model.solve` method.

See the solution output to the problem.

.. ipython:: python
   
   m.solve()

At the end of the solve operation, the solver returns 
both Problem Summary and Solution Summary tables. These tables can be
later accessed using ``m.get_problem_summary()`` and
``m.get_solution_summary``.

.. ipython:: python

   print(m.get_solution_summary())


The :func:`Model.solve` method returns the primal solution when available,
and ``None`` otherwise.

Printing solutions
------------------

Solutions provided by the solver can be obtained using
:func:`sasoptpy.get_solution_table` method. It is strongly suggested to group
variables and expressions that share the same keys in a call.

.. ipython:: python

   print(so.get_solution_table(demand, production))

As seen, a Pandas Series and a Variable object that has the same index
keys are printed in this example.

Initializing a workspace
------------------------

If you would like to use extensive abstract modeling capabilities of `sasoptpy`,
can create a workspace. Workspaces support features like server-side for loops,
cofor loops (parallel), read and create data. You can initialize a :class:`sasoptpy.Workspace`
as follows:

.. ipython:: python

   with so.Workspace(name='my_workspace', session=s) as w:
      I = so.Set(name='I', value=range(1, 11))
      x = so.VariableGroup(I, name='x', lb=0)
   print(so.to_optmodel(w))
      
You can submit a workspace to CAS server and grab the response using:

.. ipython:: python

   w.submit()


Next steps
----------

You can browse :ref:`examples` to see various uses of aformentioned
functionality. 

If you have a good understanding of the flow, then check :ref:`sasoptpy-api` to
access API details.
