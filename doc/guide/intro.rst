
.. currentmodule:: sasoptpy

.. _intro:


Introduction to Optimization
****************************

Optimization is an umbrella term for maximizing or minimizing a specified target; given as a mathematical function.
Optimization is often used in real-life problems from finance to aviation, from chemistry to sports analytics.

Optimization problems can describe a business problem or a physical concept.
Any phenomenon that can be represented as a function can be optimized by several algorithms.
Optimization lies at the heart of several tools you use every day, from routing to machine learning.

Steps of Optimization
---------------------

Optimization problems often consist of the following steps: [#]_ [#]_

1. Observe the system and define the problem.
2. Gather relevant data.
3. Develop a formulation.
4. Solve the model.
5. Interpret the solution.

A modeler observes the process in order to identify the problems and potential improvements.
Several examples of optimization problems are finding the shortest path between two locations, maximizing a profit,
and maximizing the accuracy of a handwriting recognition algorithm.

Collecting data is often the most daunting process.
In the age of big data, it is often difficult to distinguish noise from relevant data.
After data are gathered, you can write a formulation.
A proper formulation is critical because features such as linearity and convexity greatly impact
the performance of solution algorithms, especially for large problems.

Solving a problem requires an optimization algorithm.
SAS Optimization provides several optimization algorithms to solve a variety of different problem types.
For more information, see `Types of Optimization <#types-of-optimization>`_.

Finally, the modeler decides whether the result of an optimization process is valid.
If not, the process is repeated by adding the missing pieces until a satisfactory result is obtained.

Basic Elements
--------------

An optimization formulation has the following elements:

-  *Variables* are parameters that the optimization algorithm tunes.
   An optimization algorithm determines optimal values for variables in the problem.
   As an example, in an optimization problem of finding a route from your home to the airport,
   which roads to use are decision variables.
-  An *objective* is a performance measure that is to be maximized or minimized.
   An objective is a function of variables in an optimization problem, meaning an objective value is obtained for
   specified values of variables.
   In the home to airport route example, the objective function is the time to reach the airport.
   The optimization algorithm decides which roads to use in order to minimize the travel time.
-  *Constraints* are restrictions on variables that are added in order to prevent illogical or undesired solutions.
   In the example, the amount of fuel in the car restricts how far you can drive.
   You can the force optimization algorithm to find a solution under a certain mileage, even if there are other
   solutions that might be shorter in terms of travel time.

In short, *optimization* consists of choosing *variable* values to maximize or minimize an *objective* function subject
to certain *constraints*.

Simple Problem
--------------

Consider a simple example. The following problem (brewer's dilemma) is a simplified resource allocation problem,
presented by Robert G. Bland. [#]_

In the problem, a brewer has limited corn, hops, and barley malt inventory. The brewer wants to produce ale and beer
that will maximize the total profit. Each product requires a certain amount of these three ingredients, as follows:

+-------------------+------------------------------------------------------+------------+
| (per barrel)      |                    Amount Required                   |            |
+-------------------+---------------+---------------+----------------------+------------+
| Product           | Corn (Pounds) | Hops (Ounces) | Barley Malt (Pounds) | Profit ($) |
+===================+===============+===============+======================+============+
| Ale               |             5 |             4 |                   35 |         13 |
+-------------------+---------------+---------------+----------------------+------------+
| Beer              |            15 |             4 |                   20 |         23 |
+-------------------+---------------+---------------+----------------------+------------+
| (Total Available) |           480 |           160 |                1,190 |            |
+-------------------+---------------+---------------+----------------------+------------+

The variables (`ale` and `beer`) in this problem are the number of barrels of ale and beer to produce.
It might be intuitive to prefer beer to ale because of its higher profit rate. However, doing so might deplete all
the resources faster and might leave you with an excess amount of hops and barley malt.

The objective in this problem is to maximize the total profit function, which is
:math:`13 \times \text{ale} + 23 \times \text{beer}`.

Each limitation on ingredients is a constraint. For corn, hops, and barley malt, the following constrains apply:

.. math::

   5 \times \text{ale} + 15 \times \text{beer} &\leq 480 \\
   4 \times \text{ale} + 4 \times \text{beer} &\leq 160 \\
   35 \times \text{ale} + 20 \times \text{beer} &\leq 1,190 \\

Combining all items, the optimization formulation is written as follows:

.. math::

    \begin{array}{rllcl}
    \displaystyle \text{maximize:} & 13 \times \text{ale} &+ 23 \times \text{beer} \\
    \textrm{subject to:}  \\
    &5 \times \text{ale} &+ \; 15 \times \text{beer} &\leq& 480 \\
    &4 \times \text{ale} &+ \; 4 \times \text{beer} &\leq& 160 \\
    &35 \times \text{ale} &+ \; 20 \times \text{beer} &\leq& 1,190 \\
    & & \text{ale} & \geq & 0 \\
    & & \text{beer} & \geq & 0
    \end{array}

This problem is small enough to be solved by hand, but consider some alternatives.

+---+------------------+------------+
|   | Barrels Produced |            |
+---+--------+---------+------------+
| # |   Ale  |   Beer  | Profit ($) |
+===+========+=========+============+
| 1 |     34 |       0 |        442 |
+---+--------+---------+------------+
| 2 |      0 |      32 |        736 |
+---+--------+---------+------------+
| 3 |     15 |      25 |        770 |
+---+--------+---------+------------+
| 4 |     12 |      28 |        800 |
+---+--------+---------+------------+

The preceding table indicates that producing only ale or beer creates less profit than producing a combination of the two.
Alternative solution 4 gives the optimal
values that maximize the profit in this example.

Following are additional examples of problems that can be formulated as optimization problems:

* scheduling project steps to minimize total completion time, where some tasks might depend on completion of earlier tasks
* choosing distribution centers for retailers to minimize total cost while satisfying customer demands on delivery time
* assigning soccer players to a squad to maximize the total rating of the team under foreign player rules
* finding the cheapest travel option and shortest route between two cities
* blending chemical products to minimize the total cost while achieving a certain efficiency of detergents
* choosing a price that will maximize the total profit in a competitive market

For more information about optimization problems and examples,
see the related section of
`SAS Optimization Mathematical Optimization Procedures <https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_intro_toc.htm&locale=en>`__.

Types of Optimization
---------------------

The structure of a formulation affects which algorithms can be deployed to solve a problem.
The most common optimization types are as follows:

* **Linear optimization**: If the objective function and all constraints of a problem can be described
  by linear mathematical relations and if all decision variables are continuous, the formulation is called a
  linear problem (LP). LPs are among the easiest problems in terms of solution time and are well-studied in literature.
* **Mixed integer linear optimization**: If a linear formulation involves binary (yes or no type decisions), or integer variables,
  the problem is an integer linear problem (ILP) or mixed integer linear problem (MILP), depending on the variables.
  MILPs are very popular as many real-life problems can be represented as MILPs.
* **Nonlinear optimization**: If a problem involves nonlinear objectives or constraints (such as
  exponential, polynomial, or absolute values), the problem is called a nonlinear problem (NLP).

.. only:: html

    **References**

.. [#] Hillier, Frederick S., and Gerald J. Lieberman. Introduction to operations research. McGraw-Hill Science, Engineering & Mathematics, 1995.
.. [#] SAS Institute. SAS/OR 15.1 User's Guide: Mathematical Programming Examples. SAS institute, 2018.
.. [#] Bland, Robert G. "The Allocation of Resources by Linear Programming." Scientific American 244 (1981): 126-144.


