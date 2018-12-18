
.. _examples/multiobjective:

Multiobjective
==============

Reference
---------

https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.4&docsetId=ormpug&docsetTarget=ormpug_lsosolver_examples07.htm&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/lsoe10.html


Model
-----

.. literalinclude:: ../../examples/multiobjective.py

Output
------

.. ipython:: python
   :suppress:
   
   import sasoptpy
   sasoptpy.reset_globals()

.. ipython:: python

   from examples.multiobjective import test
   sols = test(cas_conn, sols=True)

.. ipython:: python

   # Plots
   import matplotlib.pyplot as plt

   tr = sols.transpose()
   scvalues = tr.iloc[2:]
   scvalues = scvalues.astype({0: float, 1: float})

.. ipython:: python

   x = sasoptpy.get_obj_by_name('x')
   f1 = sasoptpy.get_obj_by_name('f1')
   f2 = sasoptpy.get_obj_by_name('f2')
   x[1].set_value(scvalues[0])
   x[2].set_value(scvalues[1])
   scvalues['f1'] = f1.get_value()
   scvalues['f2'] = f2.get_value()

.. ipython:: python   

   f = scvalues.plot.scatter(x='f1', y='f2')
   @savefig multiobj.png
   f
