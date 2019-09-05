
Least Squares
=============

Reference
---------

https://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_nlpsolver_gettingstarted05.htm&docsetVersion=15.1&locale=en

https://support.sas.com/documentation/onlinedoc/or/ex_code/151/nlpsg01.html

Model
-----

.. literalinclude:: ../../examples/client_side/least_squares.py

Output
------

.. ipython:: python
   :suppress:

   import sasoptpy
   sasoptpy.reset()


.. ipython:: python

   from examples.client_side.least_squares import test
   test(cas_conn)

