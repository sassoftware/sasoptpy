
.. _examples:

Examples
********

Examples are provided from `SAS/OR documentation <http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=titlepage.htm&docsetVersion=14.3&locale=en>`_.

.. ipython:: python
   :suppress:
   
   hostname = os.getenv('CASHOST')
   port = os.getenv('CASPORT')
   from swat import CAS
   cas_conn = CAS(hostname, port)

Viya Examples / Concrete
------------------------

.. toctree::
   :maxdepth: 1

   Food Manufacture 1 <food_manufacture_1.rst>
   Food Manufacture 2 <food_manufacture_2.rst>
   Factory Planning 1 <factory_planning_1.rst>
   Factory Planning 2 <factory_planning_2.rst>
   Manpower Planning <manpower_planning.rst>
   Refinery Optimization <refinery_optimization.rst>
   Mining Optimization <mining_optimization.rst>
   Farm Planning <farm_planning.rst>
   Economic Planning <economic_planning.rst>
   Decentralization <decentralization.rst>
   SAS/OR Blog: Optimal Wedding <optimal_wedding.rst>
   SAS/OR Blog: Kidney Exchange <kidney_exchange.rst>
   Multiobjective <multiobjective.rst>
   Least Squares <least_squares.rst>

Viya Examples / Abstract
------------------------

.. toctree::
   :maxdepth: 1
   
   Curve Fitting <curve_fitting.rst>
   Nonlinear 1 <nonlinear_1.rst>
   Nonlinear 2 <nonlinear_2.rst>

SAS (saspy) Examples
--------------------

.. toctree::
   :maxdepth: 1

   Decentralization <decentralization_saspy.rst>
