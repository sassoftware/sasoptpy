
.. _examples/decentralization-saspy:

Decentralization (saspy)
========================

Reference
---------

http://go.documentation.sas.com/?docsetId=ormpex&docsetTarget=ormpex_ex10_toc.htm&docsetVersion=14.3&locale=en

http://support.sas.com/documentation/onlinedoc/or/ex_code/143/mpex10.html

Model
-----

.. literalinclude:: ../../examples/client_side/decentralization.py

Output
------

.. code-block:: python

   >>> from examples.client_side.decentralization import test
   >>> sas_session = saspy.SASsession(cfgname='winlocal')
   >>> test(sas_session)

   SAS Connection established. Subprocess id is 18384
   
   NOTE: Initialized model decentralization.
   NOTE: Converting model decentralization to OPTMODEL.
   NOTE: Submitting OPTMODEL codes to SAS server.
   NOTE: Writing HTML5(SASPY_INTERNAL) Body file: _TOMODS1
   NOTE: Problem generation will use 4 threads.
   NOTE: The problem has 105 variables (0 free, 0 fixed).
   NOTE: The problem has 105 binary and 0 integer variables.
   NOTE: The problem has 278 linear constraints (183 LE, 5 EQ, 90 GE, 0 range).
   NOTE: The problem has 660 linear constraint coefficients.
   NOTE: The problem has 0 nonlinear constraints (0 LE, 0 EQ, 0 GE, 0 range).
   NOTE: The OPTMODEL presolver is disabled for linear problems.
   NOTE: The initial MILP heuristics are applied.
   NOTE: The MILP presolver value AUTOMATIC is applied.
   NOTE: The MILP presolver removed 0 variables and 120 constraints.
   NOTE: The MILP presolver removed 120 constraint coefficients.
   NOTE: The MILP presolver added 120 constraint coefficients.
   NOTE: The MILP presolver modified 0 constraint coefficients.
   NOTE: The presolved problem has 105 variables, 158 constraints, and 540 constraint coefficients.
   NOTE: The MILP solver is called.
   NOTE: The parallel Branch and Cut algorithm is used.
   NOTE: The Branch and Cut algorithm is using up to 4 threads.
             Node   Active   Sols    BestInteger      BestBound      Gap    Time
                0        1      3    -14.9000000    135.0000000  111.04%       0
                0        1      3    -14.9000000     67.5000000  122.07%       0
                0        1      3    -14.9000000     55.0000000  127.09%       0
                0        1      4      8.1000000     48.0000000   83.12%       0
                0        1      4      8.1000000     44.8375000   81.93%       0
                0        1      4      8.1000000     42.0000000   80.71%       0
                0        1      4      8.1000000     39.0666667   79.27%       0
                0        1      4      8.1000000     34.7500000   76.69%       0
                0        1      4      8.1000000     33.9000000   76.11%       0
                0        1      4      8.1000000     29.6800000   72.71%       0
                0        1      4      8.1000000     28.5000000   71.58%       0
                0        1      4      8.1000000     28.5000000   71.58%       0
                0        1      4      8.1000000     28.5000000   71.58%       0
                0        1      4      8.1000000     28.5000000   71.58%       0
   NOTE: The MILP solver added 31 cuts with 168 cut coefficients at the root.
                2        0      5     14.9000000     14.9000000    0.00%       0
   NOTE: Optimal.
   NOTE: Objective = 14.9.
   NOTE: The data set WORK.PROB_SUMMARY has 20 observations and 3 variables.
   NOTE: The data set WORK.SOL_SUMMARY has 18 observations and 3 variables.
   NOTE: The data set WORK.PRIMAL_OUT has 105 observations and 6 variables.
   NOTE: The data set WORK.DUAL_OUT has 278 observations and 4 variables.
   NOTE: PROCEDURE OPTMODEL used (Total process time):
         real time           0.34 seconds
         cpu time            0.29 seconds
         
                                   Value
   Label                                
   Objective Sense          Maximization
   Objective Function         netBenefit
   Objective Type                 Linear
                                        
   Number of Variables               105
   Bounded Above                       0
   Bounded Below                       0
   Bounded Below and Above           105
   Free                                0
   Fixed                               0
   Binary                            105
   Integer                             0
                                        
   Number of Constraints             278
   Linear LE (<=)                    183
   Linear EQ (=)                       5
   Linear GE (>=)                     90
   Linear Range                        0
                                        
   Constraint Coefficients           660
   NOTE: Converting model decentralization to OPTMODEL.
   NOTE: Submitting OPTMODEL codes to SAS server.
   NOTE: Writing HTML5(SASPY_INTERNAL) Body file: _TOMODS1
   NOTE: Problem generation will use 4 threads.
   NOTE: The problem has 105 variables (0 free, 0 fixed).
   NOTE: The problem has 105 binary and 0 integer variables.
   NOTE: The problem has 68 linear constraints (3 LE, 65 EQ, 0 GE, 0 range).
   NOTE: The problem has 270 linear constraint coefficients.
   NOTE: The problem has 0 nonlinear constraints (0 LE, 0 EQ, 0 GE, 0 range).
   NOTE: The OPTMODEL presolver is disabled for linear problems.
   NOTE: The initial MILP heuristics are applied.
   NOTE: The MILP presolver value AUTOMATIC is applied.
   NOTE: The MILP presolver removed 0 variables and 0 constraints.
   NOTE: The MILP presolver removed 0 constraint coefficients.
   NOTE: The MILP presolver modified 0 constraint coefficients.
   NOTE: The presolved problem has 105 variables, 68 constraints, and 270 constraint coefficients.
   NOTE: The MILP solver is called.
   NOTE: The parallel Branch and Cut algorithm is used.
   NOTE: The Branch and Cut algorithm is using up to 4 threads.
             Node   Active   Sols    BestInteger      BestBound      Gap    Time
                0        1      3    -28.1000000    135.0000000  120.81%       0
                0        1      3    -28.1000000     30.0000000  193.67%       0
                0        1      4    -16.3000000     30.0000000  154.33%       0
                0        1      5     14.9000000     14.9000000    0.00%       0
   NOTE: Optimal.
   NOTE: Objective = 14.9.
   NOTE: The data set WORK.PROB_SUMMARY has 20 observations and 3 variables.
   NOTE: The data set WORK.SOL_SUMMARY has 18 observations and 3 variables.
   NOTE: The data set WORK.PRIMAL_OUT has 105 observations and 6 variables.
   NOTE: The data set WORK.DUAL_OUT has 68 observations and 4 variables.
   NOTE: PROCEDURE OPTMODEL used (Total process time):
         real time           0.19 seconds
         cpu time            0.14 seconds
         
                                   Value
   Label                                
   Objective Sense          Maximization
   Objective Function         netBenefit
   Objective Type                 Linear
                                        
   Number of Variables               105
   Bounded Above                       0
   Bounded Below                       0
   Bounded Below and Above           105
   Free                                0
   Fixed                               0
   Binary                            105
   Integer                             0
                                        
   Number of Constraints              68
   Linear LE (<=)                      3
   Linear EQ (=)                      65
   Linear GE (>=)                      0
   Linear Range                        0
                                        
   Constraint Coefficients           270
      totalBenefit  totalCost
   1                         
              80.0       65.1
       assign  assign assign
   2 Brighton Bristol London
   1                        
   A      0.0     1.0    0.0
   B      1.0     0.0    0.0
   C      1.0     0.0    0.0
   D      0.0     1.0    0.0
   E      1.0     0.0    0.0

