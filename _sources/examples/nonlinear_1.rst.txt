
Nonlinear 1
===========

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpug&docsetTarget=ormpug_nlpsolver_examples01.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/nlpse01.html

Model
-----

.. literalinclude:: ../../examples/nonlinear_1.py

Output
------

.. ipython:: python
   :suppress:

   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.nonlinear_1 import test
   test(cas_conn)

