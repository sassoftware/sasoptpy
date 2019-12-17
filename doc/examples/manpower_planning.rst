
Manpower Planning
=================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex5_toc.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex05.html

Model
-----

.. literalinclude:: ../../examples/client_side/manpower_planning.py

Output
------

.. ipython:: python
   :suppress:
   
   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.client_side.manpower_planning import test
   test(cas_conn)

