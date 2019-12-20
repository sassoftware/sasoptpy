
.. currentmodule:: sasoptpy

.. _intro:


Introduction to Optimization
****************************

Optimization is an umbrella term for maximizing or minimizing a given target, which
can be represented as a function.
It is often used in real-life problems from finance to aviation, from chemistry to sports analytics.

Optimization problems can describe a business problem or a physical concept.
Any phonemena that can be represented as a function can be optimized by several algorithms.
It lies at the heart of several tools we use every day, from routing to Machine Learning.

Steps of Optimization
---------------------

Optimization problems often consists of following steps [#]_ [#]_:

* Observe the system and define the problem
* Gather relevant data
* Develop a formulation
* Solve the model
* Interpret the solution

Often, a process if often observed by the modeler to identify the problems.
Several examples are finding shortest path between two locations, maximizing a profit,
and maximizing the accuracy of a handwriting recognition algorithm.

Collecting data is often the most daunting process.
In the age of big data, it is often difficult to distinguish noise from relevant data.
After data is gathered, a formulation can be written.
Formulations are important pieces of optimization, since features like linearity and convexity heavily impacts
the performance of solution algorithms, especially for large size problems.

Solving a model requires an optimization algorithm.
SAS Optimization provides several optimization algorithms to solve a variety of different formulations.
See `types of optimization <#types-of-optimization>`_ for more information on this topic.

Finally, modeler should decide whether the results of an optimization process is valid.
If not, process should be repeated by adding the missing pieces until an applicable results is obtained.

Basic Elements
--------------

In order to define an optimization formulation, modeler should decide following elements:

1. **Variables**: 

Sample Problem
--------------

Types of Optimization
---------------------




.. [#] Hillier, Frederick S., and Gerald J. Lieberman. Introduction to operations research. McGraw-Hill Science, Engineering & Mathematics, 1995.
.. [#] SAS Institute. SAS/OR 9.3 User's Guide: Mathematical Programming Examples. SAS institute, 2012.



