
Kidney Exchange
===============

Reference
---------

SAS blog: https://blogs.sas.com/content/operations/2015/02/06/the-kidney-exchange-problem/

Model
-----

.. literalinclude:: ../../examples/client_side/sas_kidney_exchange.py

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

   from examples.client_side.sas_kidney_exchange import test
   test(cas_conn)

