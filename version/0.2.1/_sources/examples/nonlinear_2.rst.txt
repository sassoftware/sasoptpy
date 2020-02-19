
Nonlinear 2
===========

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_nlpsolver_examples02.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/nlpse02.html

Model
-----

.. literalinclude:: ../../examples/nonlinear_2.py

Output
------

.. ipython:: python
   :suppress:

   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.nonlinear_2 import test
   test(cas_conn)

