
Curve Fitting
=============

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex11_toc.htm&docsetVersion=15.1&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex11.html

Model
-----

.. literalinclude:: ../../examples/server_side/curve_fitting.py

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

   from examples.server_side.curve_fitting import test
   (s1, s2, s3, s4) = test(cas_conn, sols=True)


.. ipython:: python

   # Plots
   import matplotlib.pyplot as plt

   p1 = s1.plot.scatter(x='x', y='y', c='g')
   s1.plot.line(ax=p1, x='x', y='estimate', label='Line1');
   s2.plot.line(ax=p1, x='x', y='estimate', label='Line2');
   @savefig cf_line.png
   p1

   p2 = s3.plot.scatter(x='x', y='y', c='g')
   s3.plot.line(ax=p2, x='x', y='estimate', label='Curve1');
   s4.plot.line(ax=p2, x='x', y='estimate', label='Curve2');
   @savefig cf_curve.png
   p2
