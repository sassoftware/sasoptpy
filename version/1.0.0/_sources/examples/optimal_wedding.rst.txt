
Optimal Wedding Seating
=======================

Reference
---------

SAS blog: https://blogs.sas.com/content/operations/2014/11/10/do-you-have-an-uncle-louie-optimal-wedding-seat-assignments/

Model
-----

.. literalinclude:: ../../examples/client_side/sas_optimal_wedding.py

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

   from examples.client_side.sas_optimal_wedding import test
   test(cas_conn)

