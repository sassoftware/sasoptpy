
.. currentmodule:: sasoptpy

.. _workspaces:

Workspaces
==========

.. ipython:: python
   :suppress:

   import sasoptpy as so

One of the most powerful features of SAS Optimization and PROC OPTMODEL is the ability to combine several optimization
models in a single call. Using this ability, users can read a common data set once, or parallelize solve steps for
similar subproblems.

Newly introduced :class:`Workspace` provides this ability in a familiar syntax. Compared to :class:`Model` objects,
a :class:`Workspace` can consists of several models and able to use server-side data and OPTMODEL statements in a
more detailed way.

Creating a workspace
~~~~~~~~~~~~~~~~~~~~

A :class:`Workspace` should be called using the `with` keyword of Python as follows:

>>> with so.Workspace('my_workspace') as w:
>>>    ...

You can define several models in the same workspace, and solve problems multiple times. All the statements are sent
to server after :meth:`Workspace.submit` is called.

Adding components
~~~~~~~~~~~~~~~~~

Unlike :class:`Model` objects, where components are added explicitly, objects defined inside a :class:`Workspace` is
added automatically.

For example, adding a new variable is performed as follows:

.. ipython:: python

   with so.Workspace(name='my_workspace') as w:
      x = so.Variable(name='x', vartype=so.integer)

Contents of a workspace can be displayed using :meth:`Workspace.to_optmodel`:

.. ipython:: python

   print(w.to_optmodel())


See the following full example where a data is loaded into the server, and problem is solved using a Workspace:

Create CAS session:

.. ipython:: python

   import os
   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   from swat import CAS
   cas_conn = CAS(hostname, port)
   import sasoptpy as so
   import pandas as pd

Upload data:

.. ipython:: python

   def send_data():
      data = [
         ['clock', 8, 4, 3],
         ['mug', 10, 6, 5],
         ['headphone', 15, 7, 2],
         ['book', 20, 12, 10],
         ['pen', 1, 1, 15]
      ]
      df = pd.DataFrame(data, columns=['item', 'value', 'weight', 'limit'])
      cas_conn.upload_frame(df, casout={'name': 'mydata', 'replace': True})
   send_data()

Model workspace:

.. ipython:: python

   from sasoptpy.actions import read_data, solve
   def create_workspace():
      with so.Workspace('my_knapsack', session=cas_conn) as w:
         items = so.Set(name='ITEMS', settype=so.string)
         value = so.ParameterGroup(items, name='value')
         weight = so.ParameterGroup(items, name='weight')
         limit = so.ParameterGroup(items, name='limit')
         total_weight = so.Parameter(name='total_weight', value=55)
         read_data(
            table='mydata', index={'target': items, 'key': ['item']},
            columns=[value, weight, limit]
         )
         get = so.VariableGroup(items, name='get', vartype=so.integer, lb=0)
         limit_con = so.ConstraintGroup((get[i] <= limit[i] for i in items),
                                        name='limit_con')
         weight_con = so.Constraint(
            so.expr_sum(weight[i] * get[i] for i in items) <= total_weight,
            name='weight_con')
         total_value = so.Objective(
            so.expr_sum(value[i] * get[i] for i in items), name='total_value',
            sense=so.maximize)
         solve()
      return w

   my_workspace = create_workspace()

Print content:

.. ipython:: python

   print(so.to_optmodel(my_workspace))

Submit:

.. ipython:: python

   my_workspace.submit()


.. _abstract-actions:

Abstract actions
~~~~~~~~~~~~~~~~

As shown in the previous example, a :class:`Workspace` can have statements such as :func:`actions.read_data`
and :func:`actions.solve`.

These statements are called "Abstract Statements" and are fully supported inside :class:`Workspace` objects.

Adding abstract actions
-----------------------

You can import abstract actions through `sasoptpy.actions` as follows:

>>> from sasoptpy.actions import read_data, create_data

Theses abstract actions are performed on the server side by generating an equivalent OPTMODEL code at execution.

Grabbing results
----------------

In order to solve a problem, you need to use :func:`actions.solve` function explicitly.
Since :class:`Workspace` objects allow several models and solve statements to be included,
each of these solve statements are grabbed
separately. Solution after each solve can be returned using :func:`actions.print` function.

See the following example where we change a parameter and solve the same problem twice:

.. ipython:: python

   from sasoptpy.actions import read_data, solve, print_item
   def create_multi_solve_workspace():
       with so.Workspace('my_knapsack', session=cas_conn) as w:
           items = so.Set(name='ITEMS', settype=so.string)
           value = so.ParameterGroup(items, name='value')
           weight = so.ParameterGroup(items, name='weight')
           limit = so.ParameterGroup(items, name='limit')
           total_weight = so.Parameter(name='total_weight', init=55)
           read_data(table='mydata', index={'target': items, 'key': ['item']}, columns=[value, weight, limit])
           get = so.VariableGroup(items, name='get', vartype=so.integer, lb=0)
           limit_con = so.ConstraintGroup((get[i] <= limit[i] for i in items), name='limit_con')
           weight_con = so.Constraint(
               so.expr_sum(weight[i] * get[i] for i in items) <= total_weight, name='weight_con')
           total_value = so.Objective(so.expr_sum(value[i] * get[i] for i in items), name='total_value', sense=so.MAX)
           s1 = solve()
           p1 = print_item(get)
           total_weight.set_value(40)
           s2 = solve()
           p2 = print_item(get)
       return w, s1, p1, s2, p2

   (my_workspace, solve1, print1, solve2, print2) = create_multi_solve_workspace()

Submit:

.. ipython:: python

   my_workspace.submit()

Print results:

.. ipython:: python

   print(solve1.get_solution_summary())

.. ipython:: python

   print(print1.get_response())

.. ipython:: python

   print(solve2.get_solution_summary())

.. ipython:: python

   print(print2.get_response())



List of abstract actions
------------------------

.. currentmodule:: sasoptpy.actions

A full list of abstract actions are as follows:

.. table:: List of abstract actions
   :widths: 25 60 15

   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | Method                | Description                                                   | Reference                                                                                                                                                                          |
   +=======================+===============================================================+====================================================================================================================================================================================+
   | :func:`read_data`     | Reads data sets into model sets and parameters                | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxreadstmt>`__    |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`create_data`   | Creates data sets from model components                       | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxcreatestmt>`__  |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`solve`         | Calls the optimization solver                                 | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxsolvestmt>`__   |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`for_loop`      | Creates for loops                                             | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxforstmt>`__     |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`cofor_loop`    | Creates concurrently executed for loops                       | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxcoforstmt>`__   |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`set_value`     | Sets values of model components                               |                                                                                                                                                                                    |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`fix`           | Fixes values of variables                                     | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxfixstmt>`__     |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`unfix`         | Unfixes variable values                                       | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxunfixstmt>`__   |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`set_objective` | Defines objective functions                                   | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax03.htm&locale=en#casmopt.optmodel.npxminstmt>`__     |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`print_item`    | Prints given arguments into :class:`pandas.DataFrame` objects | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxprintstmt>`__   |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`put_item`      | Displays value of given arguments                             | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxputstmt>`__     |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`expand`        | Expands current model into log in explicit format             | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxexpandstmt>`__  |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`drop`          | Drops constraints                                             | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxdropstmt>`__    |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`union`         | Produces union of given sets                                  |                                                                                                                                                                                    |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`diff`          | Produces difference of given sets                             |                                                                                                                                                                                    |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`substring`     | Gives partial values of given strings                         |                                                                                                                                                                                    |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | :func:`use_problem`   | Activates given problems                                      | `R <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_syntax11.htm&locale=en#casmopt.optmodel.npxuseprobstmt>`__ |
   +-----------------------+---------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

