
.. currentmodule:: sasoptpy

.. _intro:


Introduction to Optimization
****************************

Optimization is an umbrella term for maximizing or minimizing a given target, which
can be represented as a function.
It is often used in real-life problems from finance to aviation, from chemistry to sports analytics.

Optimization problems can describe a business problem or a physical concept.
Any phenomena that can be represented as a function can be optimized by several algorithms.
It lies at the heart of several tools we use every day, from routing to Machine Learning.

Steps of Optimization
---------------------

Optimization problems often consists of the following steps [#]_ [#]_:

1. Observe the system and define the problem
2. Gather relevant data
3. Develop a formulation
4. Solve the model
5. Interpret the solution

Often, a process is observed by the modeler to identify the problems.
Several examples are finding the shortest path between two locations, maximizing a profit,
and maximizing the accuracy of a handwriting recognition algorithm.

Collecting data is often the most daunting process.
In the age of big data, it is often difficult to distinguish noise from relevant data.
After data are gathered, you can write a formulation.
A proper formulation is critical because features such as linearity and convexity greatly impact
the performance of solution algorithms, especially for large problems.

Solving a model requires an optimization algorithm.
SAS Optimization provides several optimization algorithms to solve a variety of different formulations.
See `types of optimization <#types-of-optimization>`_ for more information on this topic.

Finally, the modeler should decide whether the result of an optimization process is valid.
If not, the process should be repeated by adding the missing pieces until a satisfactory result is obtained.

Basic Elements
--------------

There might be several elements in the definition of an optimization formulation.
To clarify these elements, consider an optimization problem of finding a route from your home to the airport.

1. **Variables**: Variables are parameters that the optimization algorithm tunes.
   In the example, the decisions of which roads to be used are decision variables.
   An optimization algorithm determines optimal values for variables in the problem.
2. **Objective**: An objective is the measure of performance that is to be maximized or minimized.
   An objective is a function of variables in a problem, meaning an objective value is obtained for given
   values of variables in an optimization problem.
   In the example, the objective function is the time to reach the airport.
   The optimization algorithm should decide which roads to use in order to minimize the travel time.
3. **Constraints**: Constraints are restrictions on variables that prevent illogical solutions.
   In the example, the amount of fuel in the car places a restriction on how far you can drive.
   You can the force optimization algorithm to find a solution under a certain mileage, even if there are other
   solutions which could be shorter in terms of travel time.

In short, *optimization* is choosing **variable** values to maximize or minimize an **objective** function subject
to certain **constraints**.

Simple Problem
--------------

Let us consider a simple example. The following problem (Brewer's Dilemma) is a simplified Resource Allocation problem,
presented by Robert G. Bland [#]_.

In the problem, a brewer has limited corn, hops, and barley malt inventory. The brewer wants to produce Ale and Beer that
will maximize the total profit. Each product requires a certain amount of these three ingredients, as follows:

+-------------------+----------------------------------------+--------+
| (per barrel)      |             Amount Required            |        |
+-------------------+------------+------------+--------------+--------+
| Product           |    Corn    |    Hops    |  Barley Malt | Profit |
+===================+============+============+==============+========+
| Ale               |   5 pounds |   4 ounces |    35 pounds |    $13 |
+-------------------+------------+------------+--------------+--------+
| Beer              |  15 pounds |   4 ounces |    20 pounds |    $23 |
+-------------------+------------+------------+--------------+--------+
| (Total Available) | 480 pounds | 160 ounces | 1,190 pounds |        |
+-------------------+------------+------------+--------------+--------+

The **variables** in this problem are to decide how many barrels of ale and beer to produce. Let us call them `ale` and
`beer`. It might be intuitive to prefer beer to ale due to its higher profit rate. However, doing so might deplete all
the resources faster and might leave you with excess amount of hops and barley malt.

The **objective** in this problem is to maximize the total profit function, which is
:math:`13 \cdot \text{ale} + 23 \cdot \text{beer}`.

Each limitation on ingredients is a **constraint**. For corn, hops, and barley malt, the following constrains apply:

.. math::

   5 \cdot \text{ale} + 15 \cdot \text{beer} &\leq 480 \\
   4 \cdot \text{ale} + 4 \cdot \text{beer} &\leq 160 \\
   35 \cdot \text{ale} + 20 \cdot \text{beer} &\leq 1,190 \\

Combining all items, the optimization formulation is written as follows:

.. math::

    \begin{array}{rllcl}
    \displaystyle \text{maximize:} & 13 \cdot \text{ale} &+ 23 \cdot \text{beer} \\
    \textrm{subject to:}  \\
    &5 \cdot \text{ale} &+ \; 15 \cdot \text{beer} &\leq& 480 \\
    &4 \cdot \text{ale} &+ \; 4 \cdot \text{beer} &\leq& 160 \\
    &35 \cdot \text{ale} &+ \; 20 \cdot \text{beer} &\leq& 1,190 \\
    & & \text{ale} & \geq & 0 \\
    & & \text{beer} & \geq & 0
    \end{array}

This problem is small enough to be solved by hand, but let us consider some alternatives.

+---+------------------+--------+
|   | Barrels produced |        |
+---+--------+---------+--------+
| # |   Ale  |   Beer  | Profit |
+===+========+=========+========+
| 1 |     34 |       0 |   $442 |
+---+--------+---------+--------+
| 2 |      0 |      32 |   $736 |
+---+--------+---------+--------+
| 3 |     15 |      25 |   $770 |
+---+--------+---------+--------+
| 4 |     12 |      28 |   $800 |
+---+--------+---------+--------+

Producing only ale or beer is inferior to producing a combination of the two, for obvious reasons. Finding the exact ratio
that will maximize the profit might be tricky, as seen in solutions 3 and 4. Indeed, solution 4 gives the optimal
values that maximize the profit in this example.

Some additional examples of problems that can be formulated as optimization problems are as follows:

* Scheduling project steps to minimize total completion, where tasks might depend on completion of earlier tasks
* Choosing distribution centers for retailers to minimize total cost while satisfying customer demands on time
* Assigning soccer players to a squad to maximize the total rating of the team under foreign player rules
* Finding the cheapest travel option and shortest route between two cities
* Blending chemical products to minimize the total cost while achieving a certain efficiency of detergents
* Choosing a price that will maximize the total profit in a competitive market

See the related section of SAS Optimization 8.5 Mathematical Optimization Procedures [#]_ for more information about
optimization problems and examples.

Types of Optimization
---------------------

The structure of a formulation affects which algorithms can be deployed to solve a problem.
The most common optimization types are as follows:

* **Linear optimization**: If the objective function and all constraints of a problem can be described
  by linear mathematical relations, and if all decision variables are continuous, the formulation is called a
  Linear problem (LP). LPs are one of the easiest problems in terms of solution time and well-studied in literature.
* **Mixed integer linear optimization**: If a linear formulation involves binary (on/off type decisions) or integer variables,
  that problem is an Integer Linear Problem (ILP) or Mixed Integer Linear Problem (MILP) depending on variables.
  MILPs are very popular as many real-life problems can be represented as MILPs.
* **Nonlinear optimization**: If a problem involves nonlinear objectives or constraints (such as
  exponential, polynomial, absolute values) the problem is called a nonlinear problem (NLP).

.. only:: html

    **References**

.. [#] Hillier, Frederick S., and Gerald J. Lieberman. Introduction to operations research. McGraw-Hill Science, Engineering & Mathematics, 1995.
.. [#] SAS Institute. SAS/OR 15.1 User's Guide: Mathematical Programming Examples. SAS institute, 2018.
.. [#] Bland, Robert G. "The Allocation of Resources by Linear Programming." Scientific American 244 (1981): 126-144.
.. [#] https://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=casmopt&docsetTarget=casmopt_intro_toc.htm&locale=en


