
Food Manufacture 1
==================

Model
-----

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex1_toc.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex01.html

.. literalinclude:: ../../examples/food_manufacture_1.py

Output
------

.. ipython:: python
   :suppress:

   import sasoptpy
   sasoptpy.reset_globals()


.. ipython:: python

   from examples.food_manufacture_1 import test
   test(cas_conn)

