
Farm Planning
=============

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex8_toc.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex08.html


Model
-----

.. literalinclude:: ../../examples/client_side/farm_planning.py

Output
------

.. ipython:: python
   :suppress:
   
   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.client_side.farm_planning import test
   test(cas_conn)

