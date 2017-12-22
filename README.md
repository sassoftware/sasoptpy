
# SAS Viya Optimization Interface for Python

**sasoptpy** is a Python package providing a modeling interface for [SAS Viya](https://www.sas.com/en_us/software/viya.html) Optimization solvers. It provides a quick way for users to deploy optimization models and solve them using CAS Action.

**sasoptpy** currently can handle linear optimization and mixed integer linear optimization problems. Users can benefit from native Python structures like dictionaries, tuples, and list to define an optimization problem. **sasoptpy** uses [Pandas](http://pandas.pydata.org/) structures extensively.

Underlying methods for communication to SAS Viya are provided by the [SAS-SWAT Package](https://sassoftware.github.io/python-swat/)

**sasoptpy** is merely an interface to SAS Optimization solvers. Check [SAS/OR](http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=titlepage.htm&locale=en) and [PROC OPTMODEL](http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=casmopt_optmodel_toc.htm&locale=en) for more details about optimization tools provided by SAS and an interface to model optimization problems inside SAS.

## Requirements

To use **sasoptpy**, you need to have:
* Python 3.5+
* [sas-swat](https://github.com/sassoftware/python-swat)
* [numpy](https://pypi.python.org/pypi/numpy)
* [pandas](https://pypi.python.org/pypi/pandas)

### Installation

**sasoptpy** can be installed from [project releases](https://github.com/sassoftware/sasoptpy/releases) page. Download the release and install it using `pip`:

    pip install sasoptpy-X.X.X.tar.gz

where `X.X.X` is the release you want to install.

## Getting Started

* The source code is currently hosted on Github at https://github.com/sassoftware/sasoptpy
* For the full documentation go to https://sassoftware.github.io/sasoptpy
* For the latest release go to https://github.com/sassoftware/sasoptpy/releases/latest

### Examples

<div style="border:1px gray solid">
![sasoptpy demo gif](img/sasoptpy-demo.gif)
</div>

```python
from swat import CAS
import sasoptpy as so

# Create a CAS Session
s = CAS(hostname='host', port=12345)
# Create an empty optimization model
m = so.Model('demo', session=s)
# Add variables
x = m.add_variable(vartype=so.CONT, name='x')
y = m.add_variable(vartype=so.INT, name='y')
# Set objective function
m.set_objective(2*x+y, sense=so.MAX, name='obj')
# Add constraints
m.add_constraint(x+2*y <= 4.5, name='c1')
m.add_constraint(3*x+y <= 5.5, name='c2')
# Print model details
print(m)
# Solve the optimization problem
result = m.solve()
# Print and list variable values
print(so.get_solution_table(x, y))
print('Obj: {}'.format(m.get_objective_value()))
```

**Output**

```shell
NOTE: Initialized model demo
Model: [
  Name: demo
  Session: host:12345
  Objective: MAX [ y  +  2.0 * x ]
  Variables (2): [
    x
    y
  ]
  Constraints (2): [
     2.0 * y  +  x  <=  4.5
     y  +  3.0 * x  <=  5.5
  ]
]
NOTE: Converting model demo to data frame
NOTE: Added action set 'optimization'.
NOTE: Uploading the problem data frame to the server.
NOTE: Cloud Analytic Services made the uploaded file available as table TMPLZLOW3J0 in caslib CASUSERHDFS(casuser).
NOTE: The table TMPLZLOW3J0 has been created in caslib CASUSERHDFS(casuser) from binary data uploaded to Cloud Analytic Services.
NOTE: The problem demo has 2 variables (0 binary, 1 integer, 0 free, 0 fixed).
NOTE: The problem has 2 constraints (2 LE, 0 EQ, 0 GE, 0 range).
NOTE: The problem has 4 constraint coefficients.
NOTE: The initial MILP heuristics are applied.
NOTE: The MILP presolver value AUTOMATIC is applied.
NOTE: The MILP presolver removed 0 variables and 0 constraints.
NOTE: The MILP presolver removed 0 constraint coefficients.
NOTE: The MILP presolver modified 1 constraint coefficients.
NOTE: The presolved problem has 2 variables, 2 constraints, and 4 constraint coefficients.
NOTE: The MILP solver is called.
NOTE: The parallel Branch and Cut algorithm is used.
NOTE: The Branch and Cut algorithm is using up to 32 threads.
             Node   Active   Sols    BestInteger      BestBound      Gap    Time
                0        1      3      4.0000000      4.1111126    2.70%       0
                0        1      3      4.0000000      4.0000000    0.00%       0
                0        0      3      4.0000000      4.0000000    0.00%       0
NOTE: Optimal.
NOTE: Objective = 4.
NOTE: Data length = 18 rows
NOTE: Conversion to MPS =   0.0010 secs
NOTE: Upload to CAS time =  0.1344 secs
NOTE: Solution parse time = 0.2669 secs
NOTE: Server solve time =   1.0903 secs
NOTE: Cloud Analytic Services dropped table TMPLZLOW3J0 from caslib CASUSERHDFS(casuser).
Problem Summary

                                Value
Label                                
Problem Name                     demo
Objective Sense          Maximization
Objective Function                obj
RHS                               RHS
                                     
Number of Variables                 2
Bounded Above                       0
Bounded Below                       2
Bounded Above and Below             0
Free                                0
Fixed                               0
Binary                              0
Integer                             1
                                     
Number of Constraints               2
LE (<=)                             2
EQ (=)                              0
GE (>=)                             0
Range                               0
                                     
Constraint Coefficients             4
Solution Summary

                                Value
Label                                
Solver                           MILP
Algorithm              Branch and Cut
Objective Function                obj
Solution Status               Optimal
Objective Value                     4
                                     
Relative Gap                        0
Absolute Gap                        0
Primal Infeasibility                0
Bound Infeasibility                 0
Integer Infeasibility               0
                                     
Best Bound                          4
Nodes                               1
Iterations                          7
                                     
Presolve Time                    0.01
Solution Time                    0.96
     x    y
1          
   1.5  1.0
Obj: 4.0
```

## Resources

- [SAS SWAT](http://github.com/sassoftware/python-swat/)
- [SAS Viya](http://www.sas.com/en_us/software/viya.html)

Copyright SAS Institute