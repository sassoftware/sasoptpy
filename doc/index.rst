.. sasoptpy documentation master file

SAS Optimization Interface for Python
*************************************

`PDF Version <sasoptpy.pdf>`_

.. module:: sasoptpy

**Date**: |today| **Version**: |version|

**Links**: `Repository <https://github.com/sassoftware/sasoptpy>`_ |
`Issues <https://github.com/sassoftware/sasoptpy/issues>`_ |
`Releases <https://github.com/sassoftware/sasoptpy/releases>`_ |
`Community <https://communities.sas.com/t5/Mathematical-Optimization/bd-p/operations_research>`_

sasoptpy is a Python package that provides a modeling interface for
SAS Optimization  and SAS/OR
optimization solvers.
It provides a quick way for users to deploy optimization models and
solve them using SAS Viya and SAS 9.4.

sasoptpy can handle linear, mixed integer linear, nonlinear, and black-box
optimization problems. You can use native Python
structures such as dictionaries, tuples, and lists to define an optimization
problem. sasoptpy offers extensive support of `pandas <http://pandas.pydata.org/>`_
objects.

Under the hood, sasoptpy uses the `SAS Scripting Wrapper for Analytic Transfer
(SWAT) package <https://sassoftware.github.io/python-swat/>`_ to communicate with
SAS Viya, and uses the
`SASPy package <https://sassoftware.github.io/saspy/>`_ to communicate with SAS 9.4
installations.

sasoptpy is an interface to SAS Optimization solvers. See
`SAS Optimization: Mathematical Optimization Procedures <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=titlepage.htm&locale=en>`_
for more information about SAS optimization tools.

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

