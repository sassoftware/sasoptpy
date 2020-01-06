
.. currentmodule:: sasoptpy

.. _about:

About Package
=============

**sasoptpy** is a Python package providing easy and integrated ways of working with SAS Optimization and SAS/OR
optimization solvers. The main goal of the project is to enable developers to model optimization problems with ease by
providing high-level building blocks. We aim to be one of the most user-friendly optimization modeling tool in Python.

Capabilities
------------

sasoptpy is very flexible in terms of optimization problem types it supports and workflow alternatives.

Solvers
~~~~~~~

It currently supports following model types:

- Linear Problems (lp)
- Integer Problems / Mixed Integer Problems (mip)
- Quadratic Problems (qp)
- Nonlinear / Black-box Problems (blackbox)

Data
~~~~

It supports working with both client-side data and server-side data.
When data is available on the client-side, it populates the model with integrated data and brings back solution to the
user.
When data is available on the server-side, it generates the code to be able to populate model on the server.
Final solution can be grabbed after the solve by the user.

Platforms
~~~~~~~~~

sasoptpy can be used with SAS Viya 3.3+ and SAS 9.4, in all the operating systems these can be installed.


Road map
--------

sasoptpy has the broader goal of supporting all the functionality SAS Optimization and SAS/OR solvers have and
provide high-level set of tools for working with models more easily.


Versioning
----------

sasoptpy follows `Semantic Versioning <https://semver.org/>`_ as of version 1.0.0.

- Any backwards incompatible changes increase major version (X.y.z).
- Minor changes and improvements increase the minor version (x.Y.z).
- Patches increase the patch version (x.y.Z).
- Pre-releases are marked using *alpha* and *beta*, and release candidates are marked using *rc* identifiers.

License
-------

sasoptpy is an open-source package and uses the standard :ref:`Apache 2.0 license <license>`.

Support
-------

Have any questions?

* If you are having a package-related issue, feel free to report it on `GitHub <https://github.com/sassoftware/sasoptpy/issues>`_.
* If you have an optimization-related question, consider asking it on `SAS Communities <https://communities.sas.com/t5/Mathematical-Optimization/bd-p/operations_research>`_.
* For further technical support, reach `SAS Technical Support <https://support.sas.com/en/technical-support.html>`_.

Contribution
------------

Contributions are always welcome. Clone project to your working environment and submit pull requests as you see fit.
For more details, see the guidelines at the GitHub repository.

Highlighted Works
-----------------

A list of highlighted projects and blog posts:

* `Fastest, cheapest, greenest: How will football fans choose which matches to attend? <https://blogs.sas.com/content/hiddeninsights/2019/12/03/fastest-cheapest-greenest-how-will-football-fans-choose-which-matches-to-attend/>`_
* `1 tournament, 12 countries: A logistical maze? <https://blogs.sas.com/content/hiddeninsights/2019/12/03/1-tournament-12-countries-a-logistical-maze/>`_
* `Using SAS Optimization with Python and containers <https://blogs.sas.com/content/subconsciousmusings/2019/08/27/using-sas-optimization-with-python-and-containers/>`_
* `Bringing Analytics to the Soccer Transfer Season <https://blogs.sas.com/content/operations/2019/06/18/bringing-analytics-to-soccer-transfer-season/>`_
* `Visiting all 30 Major League Baseball Stadiums - with Python and SAS Viya <https://blogs.sas.com/content/operations/2018/06/13/visiting-all-30-major-league-baseball-stadiums-with-python-and-sas-viya/>`_
