
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

In order to define an optimization formulation, modeler should define several elements in a problem.
To clarify these elements, consider an optimization problem of finding a route from your home to the airport.

1. **Variables**: Variables are parameters which optimization algorithm tunes.
   In our example, the decision of which roads to be used is a decision variable.
   An optimization algorithm eventually determines values for variables in the problem.
2. **Objective**: Objectives are the measure of performance that is to be maximized or minimized.
   An objective is a function of variables in a problem, meaning an objective value is obtained for given
   values of variables in an optimization problem.
   In our example, our objective function is the time to reach to the airport.
   Optimization algorithm should decide which roads to use to minimize our travel time.
3. **Constraints**: Constraints are restrictions on variables that prevents illogical solutions.
   In our example, fuel in our car is a restriction on how long we can drive.
   We can force optimization algorithm to find a solution under a certain mileage, even if there are other
   solutions which could be shorter in terms of travel time.

In short, *optimization* is choosing **variable** values to maximize or minimize an **objective** function subject
to certain **constraints**.

Simple Problem
--------------




Types of Optimization
---------------------

Structure of a formulation affects which algorithms can be deployed to solve a problem.
Most popular optimization types are as follows:

* **Linear optimization**: If the objective function and all constraints of a problem can be described
  by linear mathematical relations, and if all decision variables are continuous, that formulation is called a
  Linear Problem (LP). LPs are one of the easiest problems in terms of solution time and well-studied in literature.
* **Mixed-integer optimization**: If a linear formulation involves binary (on/off type decisions) or integer variables,
  that problem is an Integer Problem (IP) or Mixed-Integer Problem (MIP) depending on variables.
  MIPs are very popular as many real-life problems can be represented as MIPs.
* **Nonlinear optimization**: If a problem involves non-linear objectives or constraints (such as
  exponentials, polynomials, absolute values) they problem is called a nonlinear problem (NLP).
  


.. [#] Hillier, Frederick S., and Gerald J. Lieberman. Introduction to operations research. McGraw-Hill Science, Engineering & Mathematics, 1995.
.. [#] SAS Institute. SAS/OR 9.3 User's Guide: Mathematical Programming Examples. SAS institute, 2012.



