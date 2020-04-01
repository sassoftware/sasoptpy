
Economic Planning
=================

Reference
---------

SAS/OR example: http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex9_toc.htm&docsetVersion=15.1&locale=en

SAS/OR code for example: http://support.sas.com/documentation/onlinedoc/or/ex_code/151/mpex09.html

Model
-----

.. literalinclude:: ../../examples/client_side/economic_planning.py

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

   from examples.client_side.economic_planning import test
   test(cas_conn)

