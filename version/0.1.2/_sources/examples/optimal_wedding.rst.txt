
Optimal Wedding
===============

SAS Blog: https://blogs.sas.com/content/operations/2014/11/10/do-you-have-an-uncle-louie-optimal-wedding-seat-assignments/

Model
-----

.. literalinclude:: ../../examples/sas_optimal_wedding.py

Output
------

.. ipython:: python
   :suppress:
   
   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.sas_optimal_wedding import test
   test(cas_conn)

