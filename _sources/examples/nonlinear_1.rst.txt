
Nonlinear 1
===========

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_nlpsolver_examples01.htm&docsetVersion=15.1&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/151/nlpse01.html

Model
-----

.. literalinclude:: ../../examples/client_side/nonlinear_1.py

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

   from examples.client_side.nonlinear_1 import test
   test(cas_conn)

