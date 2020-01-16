
Mining Optimization
===================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex7_toc.htm&docsetVersion=15.1&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/151/mpex07.html

Model
-----

.. literalinclude:: ../../examples/client_side/mining_optimization.py

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

   from examples.client_side.mining_optimization import test
   test(cas_conn)

