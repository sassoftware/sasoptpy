
.. _examples/decentralization-saspy:

Decentralization (saspy)
========================

Model
-----

.. literalinclude:: ../../examples/decentralization.py

Output
------

.. code-block:: python

   >>> from examples.food_manufacture_1 import test
   >>> sas_session = saspy.SASsession(cfgname='winlocal')
   >>> test(sas_session)

   SAS Connection established. Subprocess id is 14868
   
   NOTE: Initialized model decentralization.
   NOTE: Converting model decentralization to DataFrame.
   NOTE: Writing HTML5(SASPY_INTERNAL) Body file: _TOMODS1
   NOTE: The problem decentralization has 105 variables (105 binary, 0 integer, 0 free, 0 fixed).
   NOTE: The problem has 278 constraints (183 LE, 5 EQ, 90 GE, 0 range).
   NOTE: The problem has 660 constraint coefficients.
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
                0        1      3     14.9000000     67.5000000   77.93%       0
                0        1      3     14.9000000     53.5000000   72.15%       0
                0        1      3     14.9000000     47.7000000   68.76%       0
                0        1      3     14.9000000     45.3000000   67.11%       0
                0        1      3     14.9000000     38.5000000   61.30%       0
                0        1      3     14.9000000     34.4666667   56.77%       0
                0        0      3     14.9000000     14.9000000    0.00%       0
   NOTE: The MILP solver added 44 cuts with 254 cut coefficients at the root.
   NOTE: Optimal.
   NOTE: Objective = 14.9.
   NOTE: The data set WORK.PROB_SUMMARY has 21 observations and 3 variables.
   NOTE: The data set WORK.SOL_SUMMARY has 17 observations and 3 variables.
   NOTE: There were 825 observations read from the data set WORK.MPS.
   NOTE: The data set WORK.PRIMAL_OUT has 105 observations and 8 variables.
   NOTE: The data set WORK.DUAL_OUT has 278 observations and 8 variables.
   NOTE: PROCEDURE OPTMILP used (Total process time):
         real time           0.09 seconds
         cpu time            0.06 seconds
         
                                       Value
   Label                                    
   Problem Name             decentralization
   Objective Sense              Maximization
   Objective Function             netBenefit
   RHS                                   RHS
                                            
   Number of Variables                   105
   Bounded Above                           0
   Bounded Below                           0
   Bounded Above and Below               105
   Free                                    0
   Fixed                                   0
   Binary                                105
   Integer                                 0
                                            
   Number of Constraints                 278
   LE (<=)                               183
   EQ (=)                                  5
   GE (>=)                                90
   Range                                   0
                                            
   Constraint Coefficients               660
   NOTE: Converting model decentralization to DataFrame.
   NOTE: Writing HTML5(SASPY_INTERNAL) Body file: _TOMODS1
   NOTE: The problem decentralization has 105 variables (105 binary, 0 integer, 0 free, 0 fixed).
   NOTE: The problem has 68 constraints (3 LE, 65 EQ, 0 GE, 0 range).
   NOTE: The problem has 270 constraint coefficients.
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
                0        1      3    -12.3000000    135.0000000  109.11%       0
                0        1      3    -12.3000000     30.0000000  141.00%       0
                0        1      3    -12.3000000     28.5000000  143.16%       0
                0        1      4     14.9000000     14.9000000    0.00%       0
   NOTE: The MILP solver added 1 cuts with 2 cut coefficients at the root.
   NOTE: Optimal.
   NOTE: Objective = 14.9.
   NOTE: The data set WORK.PROB_SUMMARY has 21 observations and 3 variables.
   NOTE: The data set WORK.SOL_SUMMARY has 17 observations and 3 variables.
   NOTE: There were 384 observations read from the data set WORK.MPS.
   NOTE: The data set WORK.PRIMAL_OUT has 105 observations and 8 variables.
   NOTE: The data set WORK.DUAL_OUT has 68 observations and 8 variables.
   NOTE: PROCEDURE OPTMILP used (Total process time):
         real time           0.08 seconds
         cpu time            0.06 seconds
         
                                       Value
   Label                                    
   Problem Name             decentralization
   Objective Sense              Maximization
   Objective Function             netBenefit
   RHS                                   RHS
                                            
   Number of Variables                   105
   Bounded Above                           0
   Bounded Below                           0
   Bounded Above and Below               105
   Free                                    0
   Fixed                                   0
   Binary                                105
   Integer                                 0
                                            
   Number of Constraints                  68
   LE (<=)                                 3
   EQ (=)                                 65
   GE (>=)                                 0
   Range                                   0
                                            
   Constraint Coefficients               270
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
   SAS Connection terminated. Subprocess id was 14868
