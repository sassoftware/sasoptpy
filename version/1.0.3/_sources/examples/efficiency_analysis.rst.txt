
.. _efficiency-analysis:

Efficiency Analysis
===================

Reference
---------

SAS/OR example: https://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex22_toc.htm&docsetVersion=15.1&locale=en

SAS/OR code for example: http://support.sas.com/documentation/onlinedoc/or/ex_code/151/mpex22.html

Model
-----

.. literalinclude:: ../../examples/server_side/efficiency_analysis.py

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

   from examples.server_side.efficiency_analysis import test
   test(cas_conn)

