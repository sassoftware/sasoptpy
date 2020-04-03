
.. _examples/decentralization-saspy:

Decentralization (SASPy)
========================

Reference
---------

SAS/OR example: http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex10_toc.htm&docsetVersion=15.1&locale=en

SAS/OR code for example: http://support.sas.com/documentation/onlinedoc/or/ex_code/151/mpex10.html

Model
-----

.. literalinclude:: ../../examples/client_side/decentralization.py

Output
------

.. ipython:: python

   import os
   import saspy
   config_file = os.path.abspath('../tests/examples/saspy_config.py')
   sas_conn = saspy.SASsession(cfgfile=config_file)
   import sasoptpy

.. ipython:: python
   :suppress:

   sasoptpy.reset()


.. ipython:: python

   from examples.client_side.decentralization import test
   test(sas_conn)


