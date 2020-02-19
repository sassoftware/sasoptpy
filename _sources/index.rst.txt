.. sasoptpy documentation master file

sasoptpy: SAS Optimization Interface for Python
***********************************************

`PDF Version <sasoptpy.pdf>`_

.. module:: sasoptpy

**Date**: |today| **Version**: |version|

**Links**: `Repository <https://github.com/sassoftware/sasoptpy>`_ |
`Issues <https://github.com/sassoftware/sasoptpy/issues>`_ |
`Releases <https://github.com/sassoftware/sasoptpy/releases>`_ |
`Community <https://communities.sas.com/t5/Mathematical-Optimization/bd-p/operations_research>`_

*sasoptpy* is a Python package that provides a modeling interface for
`SAS Viya <https://www.sas.com/en_us/software/viya.html>`_  and SAS/OR
optimization solvers.
It provides a quick way for users to deploy optimization models and
solve them by using the
`SAS Viya Optimization Action Set <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casactmopt&docsetTarget=casactmopt_optimization_toc.htm&locale=en>`_.

*sasoptpy* can handle linear, mixed integer linear, nonlinear, and black-box
optimization problems. You can use native Python
structures like dictionaries, tuples, and lists to define an optimization
problem. *sasoptpy* supports `Pandas <http://pandas.pydata.org/>`_
objects extensively.

Under the hood, *sasoptpy* uses the
`swat package <https://sassoftware.github.io/python-swat/>`_ to communicate with
SAS Viya, and uses the
`saspy package <https://sassoftware.github.io/saspy/>`_ to communicate with SAS 9.4
installations.

*sasoptpy* is an interface to SAS Optimization solvers. Check
`SAS/OR <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=titlepage.htm&locale=en>`_
and 
`PROC OPTMODEL <http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_optmodel_toc.htm&locale=en>`_ 
for more details about optimization tools provided by SAS and an interface to
model optimization problems inside SAS.

See the SAS Global Forum paper: `Optimization Modeling with Python and SAS Viya <https://www.sas.com/content/dam/SAS/support/en/sas-global-forum-proceedings/2018/1814-2018.pdf>`_

.. toctree::
   :glob:
   :name: mastertoc
   :maxdepth: 2

   overview/overview
   install/install
   guide/user-guide
   examples/examples
   api/api
   version-history

