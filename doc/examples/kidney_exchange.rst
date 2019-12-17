
Kidney Exchange
===============

Reference
---------

SAS Blog: https://blogs.sas.com/content/operations/2015/02/06/the-kidney-exchange-problem/

Model
-----

.. literalinclude:: ../../examples/client_side/sas_kidney_exchange.py

Output
------

.. ipython:: python
   :suppress:
   
   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.client_side.sas_kidney_exchange import test
   test(cas_conn)

