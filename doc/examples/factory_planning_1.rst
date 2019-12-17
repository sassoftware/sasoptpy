
Factory Planning 1
==================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex3_toc.htm&docsetVersion=14.3&locale=en

https://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex03.html

Model
-----

.. literalinclude:: ../../examples/client_side/factory_planning_1.py

Output
------

.. ipython:: python
   :suppress:

   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.client_side.factory_planning_1 import test
   test(cas_conn)

