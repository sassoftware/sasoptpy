
Factory Planning 1
==================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex3_toc.htm&docsetVersion=15.1&locale=en

https://support.sas.com/documentation/onlinedoc/or/ex_code/151/mpex03.html

Model
-----

.. literalinclude:: ../../examples/client_side/factory_planning_1.py

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

   from examples.client_side.factory_planning_1 import test
   test(cas_conn)

