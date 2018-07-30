.. sasoptpy documentation master file

sasoptpy: SAS Optimization Interface for Python
***********************************************

`PDF Version <sasoptpy.pdf>`_

.. module:: sasoptpy

**Date**: |today| **Version**: |version|


*sasoptpy* is a Python package providing a modeling interface for 
`SAS Viya <https://www.sas.com/en_us/software/viya.html>`_  and SAS/OR
Optimization solvers. 
It provides a quick way for users to deploy optimization models and
solve them using
`SAS Viya Optimization Action Set <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casactmopt&docsetTarget=casactmopt_optimization_toc.htm&locale=en>`_.

*sasoptpy* can handle linear optimization, mixed integer linear optimization,
and nonlinear optimization problems. Users can benefit from native Python
structures like dictionaries, tuples, and list to define an optimization
problem. *sasoptpy* supports `Pandas <http://pandas.pydata.org/>`_
objects extensively.

Under the hood, *sasoptpy* uses
`swat package <https://sassoftware.github.io/python-swat/>`_ to communicate
SAS Viya, and uses
`saspy package <https://sassoftware.github.io/saspy/>`_ to communicate SAS 9.4
installations.

*sasoptpy* is an interface to SAS Optimization solvers. Check
`SAS/OR <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=titlepage.htm&locale=en>`_
and 
`PROC OPTMODEL <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=casmopt_optmodel_toc.htm&locale=en>`_ 
for more details about optimization tools provided by SAS and an interface to
model optimization problems inside SAS.

See our SAS Global Forum paper: `Optimization Modeling with Python and SAS Viya <https://www.sas.com/content/dam/SAS/support/en/sas-global-forum-proceedings/2018/1814-2018.pdf>`_

.. toctree::
   :glob:
   :name: mastertoc
   :maxdepth: 2

   overview
   getting-started
   input-data
   models
   components
   workflow
   examples
   api/api

