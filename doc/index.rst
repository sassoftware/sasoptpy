.. sasoptpy documentation master file

sasoptpy: SAS Viya Optimization Interface for Python
****************************************************

`PDF Version <../latex/sasoptpy.pdf>`_

.. module:: sasoptpy

**Date**: |today| **Version**: |version|


**sasoptpy** is a Python package providing a modeling
interface for `SAS Viya <https://www.sas.com/en_us/software/viya.html>`_ 
Optimization solvers. It provides a quick way for 
users to deploy optimization models and solve them
using CAS Action.

**sasoptpy** currently can handle linear optimization
and mixed integer linear optimization problems. 
Users can benefit from native Python structures
like dictionaries, tuples, and list to define an 
optimization problem. **sasoptpy** uses `Pandas <http://pandas.pydata.org/>`_
structures extensively.

Underlying methods for communication to SAS Viya
are provided by the 
`SAS-SWAT Package <https://sassoftware.github.io/python-swat/>`_.

**sasoptpy** is merely an interface to SAS Optimization
solvers. Check
`SAS/OR <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=titlepage.htm&locale=en>`_
and 
`PROC OPTMODEL <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=casmopt_optmodel_toc.htm&locale=en>`_ 
for more details about optimization tools provided by SAS
and an interface to model optimization problems inside SAS.


.. toctree::
   :glob:
   :name: mastertoc
   :maxdepth: 2

   whatsnew
   install
   getting-started
   input-data
   models
   components
   sasoptpy
   examples


