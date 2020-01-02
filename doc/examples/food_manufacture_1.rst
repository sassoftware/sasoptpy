
Food Manufacture 1
==================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex1_toc.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex01.html

Model
-----

.. literalinclude:: ../../examples/client_side/food_manufacture_1.py

Output
------

.. ipython:: python

   import os
   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   from swat import CAS
   cas_conn = CAS(hostname, port)
   import sasoptpy

.. ipython:: python
   :suppress:

   sasoptpy.reset()


.. ipython:: python

   from examples.client_side.food_manufacture_1 import test
   test(cas_conn)

