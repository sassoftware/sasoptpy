
.. _examples/rest_knapsack:

Knapsack
========

Model
-----

.. literalinclude:: ../../examples/rest_knapsack.py

Output
------

.. ipython:: python
   :suppress:

   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.rest_knapsack import test
   test(hostname, port)
