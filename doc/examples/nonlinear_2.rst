
Nonlinear 2
===========

Reference
---------

SAS/OR example: http://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_nlpsolver_examples02.htm&docsetVersion=15.1&locale=en

SAS/OR code for example: http://support.sas.com/documentation/onlinedoc/or/ex_code/151/nlpse02.html

Model
-----

.. literalinclude:: ../../examples/client_side/nonlinear_2.py

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

   from examples.client_side.nonlinear_2 import test
   test(cas_conn)

