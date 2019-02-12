
# SAS Optimization Interface for Python

**sasoptpy** is a Python package providing a modeling interface for [SAS Viya](https://www.sas.com/en_us/software/viya.html) and SAS/OR Optimization solvers.
It provides a quick way for users to deploy optimization models and solve them using CAS Actions.

**sasoptpy** can handle linear, mixed integer linear and nonlinear optimization problems.
Users can benefit from native Python structures like dictionaries, tuples, and list to define an optimization problem.
**sasoptpy** uses [Pandas](http://pandas.pydata.org/) structures extensively.

Under the hood, **sasoptpy** uses
[swat package](https://sassoftware.github.io/python-swat/) to communicate
SAS Viya, and uses
[saspy package](https://sassoftware.github.io/saspy/) to communicate SAS 9.4
installations.

**sasoptpy** is an interface to SAS Optimization solvers. Check
[SAS/OR](http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=titlepage.htm&locale=en)
and 
[PROC OPTMODEL](http://go.documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.3&docsetId=casmopt&docsetTarget=casmopt_optmodel_toc.htm&locale=en)
for more details about optimization tools provided by SAS and an interface to
model optimization problems inside SAS.

## Requirements

To use **sasoptpy**, you need to have:
* Python 3.5+
* [numpy](https://pypi.python.org/pypi/numpy)
* [saspy](https://github.com/sassoftware/saspy) (Optional)
* [swat](https://github.com/sassoftware/python-swat)
* [pandas](https://pypi.python.org/pypi/pandas)

### Installation

**sasoptpy** can be installed from [project releases](https://github.com/sassoftware/sasoptpy/releases) page.
Download the release and install it using `pip`:

    pip install vX.X.X.tar.gz

where `vX.X.X` is the release you want to install.

Alternatively, use:

``` shell
   pip install https://github.com/sassoftware/sasoptpy/archive/vX.X.X.tar.gz
```

## Getting Started

* The source code is currently hosted on GitHub at https://github.com/sassoftware/sasoptpy
* Online documentation is at https://sassoftware.github.io/sasoptpy/
* For the latest release go to https://github.com/sassoftware/sasoptpy/releases/latest

### Examples

![sasoptpy demo gif](img/sasoptpy-demo.gif)

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
# Solve the optimization problem
result = m.solve()
# Print and list variable values
print(so.get_solution_table(x, y))
print('Optimal objective value:', m.get_objective_value())
```

**Output**

```shell
NOTE: Initialized model demo.
NOTE: Added action set 'optimization'.
NOTE: Converting model demo to OPTMODEL.
NOTE: Submitting OPTMODEL codes to CAS server.
NOTE: Problem generation will use 32 threads.
NOTE: The problem has 2 variables (2 free, 0 fixed).
NOTE: The problem has 0 binary and 1 integer variables.
NOTE: The problem has 2 linear constraints (2 LE, 0 EQ, 0 GE, 0 range).
NOTE: The problem has 4 linear constraint coefficients.
NOTE: The problem has 0 nonlinear constraints (0 LE, 0 EQ, 0 GE, 0 range).
NOTE: The OPTMODEL presolver is disabled for linear problems.
NOTE: The initial MILP heuristics are applied.
NOTE: The MILP presolver value AUTOMATIC is applied.
NOTE: The MILP presolver removed 0 variables and 1 constraints.
NOTE: The MILP presolver removed 2 constraint coefficients.
NOTE: The MILP presolver modified 0 constraint coefficients.
NOTE: The presolved problem has 2 variables, 1 constraints, and 2 constraint coefficients.
NOTE: The MILP solver is called.
NOTE: The parallel Branch and Cut algorithm is used.
NOTE: The Branch and Cut algorithm is using up to 32 threads.
             Node   Active   Sols    BestInteger      BestBound      Gap    Time
                0        1      2      3.3333333      4.2000000   20.63%       0
                0        1      3      4.0000000      4.0000000    0.00%       0
                0        0      3      4.0000000      4.0000000    0.00%       0
NOTE: Optimal.
NOTE: Objective = 4.
NOTE: The CAS table 'solutionSummary' in caslib 'CASUSERHDFS(casuser)' has 18 rows and 4 columns.
NOTE: The CAS table 'problemSummary' in caslib 'CASUSERHDFS(casuser)' has 20 rows and 4 columns.
NOTE: The CAS table 'primal' in caslib 'CASUSERHDFS(casuser)' has 2 rows and 6 columns.
NOTE: The CAS table 'dual' in caslib 'CASUSERHDFS(casuser)' has 2 rows and 4 columns.
     x    y
1          
   1.5  1.0
Optimal objective value: 4.0
```

## Resources

- [SAS Viya](http://www.sas.com/en_us/software/viya.html)

Copyright SAS Institute
