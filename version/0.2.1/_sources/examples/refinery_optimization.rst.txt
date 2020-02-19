
Refinery Optimization
=====================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex6_toc.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex06.html

Model
-----

.. literalinclude:: ../../examples/refinery_optimization.py

Output
------

.. ipython:: python
   :suppress:
   
   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python
   :okwarning:

   from examples.refinery_optimization import test
   test(cas_conn)

