
.. _examples/multiobjective:

Multiobjective
==============

Reference
---------

https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.4&docsetId=ormpug&docsetTarget=ormpug_lsosolver_examples07.htm&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/lsoe10.html


Model
-----

.. literalinclude:: ../../examples/client_side/multiobjective.py

Output
------

.. ipython:: python

   import os
   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   from swat import CAS
   cas_conn = CAS(hostname, port)
   import sasoptpy

.. ipython:: python
   :suppress:

   sasoptpy.reset()

.. ipython:: python

   from examples.client_side.multiobjective import test
   response = test(cas_conn, sols=True)

.. ipython:: python

   import matplotlib.pyplot as plt
   sols = response['solutions']
   x = response['x']
   f1 = response['f1']
   f2 = response['f2']
   tr = sols.transpose()
   scvalues = tr.iloc[2:]
   scvalues = scvalues.astype({0: float, 1: float})
   x[1].set_value(scvalues[0])
   x[2].set_value(scvalues[1])
   scvalues['f1'] = f1.get_value()
   scvalues['f2'] = f2.get_value()
   f = scvalues.plot.scatter(x='f1', y='f2')
   f.set_title('Multiobjective: Plot of Pareto-Optimal Set');
   @savefig multiobj.png
   f
