
.. currentmodule:: sasoptpy

.. _models:

Models
======

Creating a model
~~~~~~~~~~~~~~~~

You can create an empty model by using the :class:`Model` constructor:

.. ipython:: python

   import sasoptpy as so
   m = so.Model(name='model1')

Adding new components to a model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add a variable:

.. ipython:: python

   x = m.add_variable(name='x', vartype=so.BIN)
   print(m)
   y = m.add_variable(name='y', lb=1, ub=10)
   print(m)

Add a constraint:

.. ipython:: python

   c1 = m.add_constraint(x + 2 * y <= 10, name='c1')
   print(m)

Adding existing components to a model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A new model can use existing variables. The typical way to include a variable
is to use the :meth:`Model.include` method:

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
Therefore, after :meth:`Model.solve` is called, the values of variables are
replaced with optimal values.

Accessing components
~~~~~~~~~~~~~~~~~~~~

You can access a list of model variables by using the :meth:`Model.get_variables()`
method:

.. ipython:: python

   print(m.get_variables())

Similarly, you can access a list of constraints by using the
:meth:`Model.get_constraints()` method:

.. ipython:: python

   c2 = m.add_constraint(2 * x - y >= 1, name='c2')
   print(m.get_constraints())

To access a certain constraint by using its name, you can use the
:meth:`Model.get_constraint` method:

.. ipython:: python

   print(m.get_constraint('c2'))


Dropping components
~~~~~~~~~~~~~~~~~~~

You can drop a variable inside a model by using
:meth:`Model.drop_variable` method. Similarly, you can drop a set of variables
by using the :meth:`Model.drop_variables` method.

.. ipython:: python

   m.drop_variable(y)
   print(m)

.. ipython:: python
   :suppress:

   m.include(y)

You can drop a constraint by using the :meth:`Model.drop_constraint` method.
Similarly, you can drop a set of constraints by using the
:meth:`Model.drop_constraints` method.

.. ipython:: python

   m.drop_constraint(c1)
   m.drop_constraint(c2)
   print(m)

.. ipython:: python

   m.include(c1)
   print(m)


Copying a model
~~~~~~~~~~~~~~~

You can copy an existing model by including the :class:`Model` object itself.

.. ipython:: python

   copy_model = so.Model(name='copy_model')
   copy_model.include(m)
   print(copy_model)

Note that all variables and constraints are included by reference.

.. _solving-model:


Solving a model
~~~~~~~~~~~~~~~

A model is solved by using the :meth:`Model.solve` method. This method converts
Python definitions into OPTMODEL language and submits using SWAT or SASPy packages.

>>> m.solve()
NOTE: Initialized model model_1
NOTE: Added action set 'optimization'.
NOTE: Converting model model_1 to OPTMODEL.
...
NOTE: Optimal.
NOTE: Objective = 124.343.
NOTE: The Dual Simplex solve time is 0.01 seconds.

Solve options
~~~~~~~~~~~~~

.. _solver-options:

Solver Options
++++++++++++++

You can pass either solve options from the OPTMODEL procedure or solve parameter from the ``solveLp`` and ``solveMilp``
actions by using the ``options`` parameter of the :meth:`Model.solve` method.

>>> m.solve(options={'with': 'milp', 'maxtime': 600})
>>> m.solve(options={'with': 'lp', 'algorithm': 'ipm'})

The parameter ``with`` is used to specificy the optimization solver in OPTMODEL procedure.
If the ``with`` parameter is not passed, PROC OPTMODEL chooses a solver that depends on the problem type.
Possible ``with`` values are listed in the `SAS/OR documentation <http://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_optmodel_syntax11.htm&docsetVersion=15.1&locale=en#ormpug.optmodel.npxsolvestmt>`__.


You can find specific solver options in the SAS Optimization documentation:

- `LP solver options <https://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_lpsolver_syntax02.htm&docsetVersion=15.1&locale=en>`__
- `MILP solver options <https://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_milpsolver_syntax02.htm&docsetVersion=15.1&locale=en>`__
- `NLP solver options <https://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_nlpsolver_syntax02.htm&docsetVersion=15.1&locale=en>`__
- `QP solver options <https://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_qpsolver_syntax02.htm&docsetVersion=15.1&locale=en>`__
- `Black-box solver options <https://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_lsosolver_syntax02.htm&docsetVersion=15.1&locale=en>`__ (formerly called LSO solver)

The ``options`` parameter can also pass ``solveLp`` and ``solveMilp`` action
parameter when ``frame=True`` is used when the :meth:`Model.solve` method is called.

- `solveLp options <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=cas-optimization-solvelp.htm&docsetVersion=8.5&locale=en>`__
- `solveMilp options <https://go.documentation.sas.com/?docsetId=casactmopt&docsetTarget=cas-optimization-solvemilp.htm&docsetVersion=8.5&locale=en>`__

Call parameters
+++++++++++++++

Besides the ``options`` parameter, you can pass following parameters into the :meth:`Model.solve` method:

- name: Name of the uploaded problem information
- drop: Drops the data from server after the solve
- replace: Replaces an existing data with the same name
- primalin: Uses the current values of the variables as an initial solution.
            When the value of this parameter is ``True``, the solve method grabs :class:`Variable` objects'
            ``_init`` fields. You can modify this field by using the :meth:`Variable.set_init` method.
- submit: Calls the CAS action or SAS procedure
- frame: Uses the frame (MPS) method. If the value of this parameter is ``False``, then the method uses OPTMODEL codes.
- verbose: Prints the generated PROC OPTMODEL code or MPS DataFrame object before the solve


Getting solutions
~~~~~~~~~~~~~~~~~

After the solve is completed, all variable and constraint values are parsed
automatically.
You can access a summary of the problem by using the
:meth:`Model.get_problem_summary` method,
and a summary of the solution by using the
:meth:`Model.get_solution_summary`
method.

To print the values of any object, you can use the :func:`get_solution_table` method:

>>> print(so.get_solution_table(x, y))

All variables and constraints that are passed into this method are returned on
the basis of their indices. See :ref:`examples` for more details.

Tuning MILP model parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SAS Optimization solvers provide a variety of settings.
However, it might be difficult to find the best settings for a
particular model. In order to compare parameters and make a good choice, you can use the `optimization.tune` action
for mixed integer linear optimization problems.

The :meth:`Model.tune_parameters` method is a wrapper for the tune action. Consider the following knapsack problem example:

.. ipython:: python
   :suppress:

   import os
   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   from swat import CAS
   cas_conn = CAS(hostname, port)
   import sasoptpy as so
   import pandas as pd

.. ipython:: python

   def get_model():
      m = so.Model(name='knapsack_with_tuner', session=cas_conn)
      data = [
          ['clock', 8, 4, 3],
          ['mug', 10, 6, 5],
          ['headphone', 15, 7, 2],
          ['book', 20, 12, 10],
          ['pen', 1, 1, 15]
      ]
      df = pd.DataFrame(data, columns=['item', 'value', 'weight', 'limit']).set_index(['item'])
      ITEMS = df.index
      value = df['value']
      weight = df['weight']
      limit = df['limit']
      total_weight = 55
      get = m.add_variables(ITEMS, name='get', vartype=so.INT)
      m.add_constraints((get[i] <= limit[i] for i in ITEMS), name='limit_con')
      m.add_constraint(so.expr_sum(weight[i] * get[i] for i in ITEMS) <= total_weight, name='weight_con')
      total_value = so.expr_sum(value[i] * get[i] for i in ITEMS)
      m.set_objective(total_value, name='total_value', sense=so.MAX)
      return m

   m = get_model()

For this problem, you can compare configurations as follows:

.. ipython:: python

   results = m.tune_parameters(tunerParameters={'maxConfigs': 10})

.. ipython:: python

   print(results)

:meth:`Model.tune_parameters` accepts three main arguments

* milpParameters
* tunerParameters
* tuningParameters

For a full set of tuning parameters and acceptable values of these arguments, see the `SAS Optimization documentation <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casactmopt&docsetTarget=casactmopt_optimization_details37.html>`__.

For the example problem, you can tune the `presolver`, `cutStrategy`, and `strongIter` settings, by using initial values and
candidate values, and limit the maximum number of configurations and maximum running time as follows:

.. ipython:: python

   results = m.tune_parameters(
      milpParameters={'maxtime': 10},
      tunerParameters={'maxConfigs': 20, 'logfreq': 5},
      tuningParameters=[
         {'option': 'presolver', 'initial': 'none', 'values': ['basic', 'aggressive', 'none']},
         {'option': 'cutStrategy'},
         {'option': 'strongIter', 'initial': -1, 'values': [-1, 100, 1000]}
      ])

.. ipython:: python

   print(results)

You can retrieve full details by using the :meth:`Model.get_tuner_results` method.
