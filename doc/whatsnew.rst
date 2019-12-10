
.. currentmodule:: sasoptpy

.. _whatsnew:


What's New
**********

This page outlines changes from each release.

v1.0.0-alpha (TBD)
============

New Features
++++++++++++

- Added workspaces
- Added `read_data` function for workspaces
- Added `concat` function for concatenating expressions and strings

Changes
+++++++

- `get_obj_by_name` function is removed

Bug Fixes
+++++++++

- Fixed the bug regarding arithmetic operations involving powers


v0.2.1 (February 26, 2019)
==========================

New Features
++++++++++++

- Support for evaluating nonlinear expressions is added, see
  :meth:`Expression.get_value` and :func:`utils._evaluate`
- Support for multiple objectives is added for LSO solver, see
  :meth:`Model.set_objective` and
  :ref:`Multiobjective <examples/multiobjective>` example
- Support for spaces inside variable indices is added
- Experimental RESTful API is added

Changes
+++++++

- Dictionaries inside components are replaced with ordered dictionaries
  to preserve deterministic behavior
- Math operators are added into the keys of linear coefficient dictionaries
- Some iterators are rewritten using `yield` keyword for performance
- `key_name` and `col_names` parameters are added into :meth:`read_table`

Bug Fixes
+++++++++

- Fixed: Using a single variable as an objective is producing incorrect input
- Fixed: :meth:`Expression.get_value` fails to evaluate expressions with
  operators
- Fixed: :meth:`Expression.add` overrides operators in some instances
- Fixed: Expressions with same components but different operators get summed
  incorrectly
- Fixed: New version of Viya complains about :class:`pandas.DataFrame` column
  types
- Syntax fixes for :pep:`8` compliance

Notes
+++++

- A Jupyter notebook example of the Diet Problem is added
- A new example is added to show usage of experiment RESTful API:
  :ref:`Knapsack <examples/rest_knapsack>`
- Unit tests are added for development repository
- CD/CI integration is added for the development repository on Gitlab
- Generated models can be checked using the hash values inside tests.responses

v0.2.0 (July 30, 2018)
======================

New Features
++++++++++++

- Support for the new `runOptmodel` CAS action is added
- Nonlinear optimization model building support is added for both SAS 9.4 and
  SAS Viya solvers
- Abstract model building support is added when using SAS Viya solvers
- New object types, :class:`Set`, :class:`SetIterator`, :class:`Parameter`,
  :class:`ParameterValue`, :class:`ImplicitVar`, :class:`ExpressionDict`, and
  :class:`Statement` are added for abstract model building
- :meth:`Model.to_optmodel` method is added for exporting model objects into
  PROC OPTMODEL codes as a string
- Wrapper functions :func:`read_table` and :func:`read_data` are added to
  read CASTable and DataFrame objects into the models
- Math function wrappers are added
- :code:`_expr` and :code:`_defn` methods are added to all object types for
  producing OPTMODEL expression and definitions
- Multiple solutions are now being returned when using `solveMilp` action and
  can be grabbed using :meth:`Model.get_solution` method
- :meth:`Model.get_variable_value` is added to get solution values of abstract
  variables

Changes
+++++++

- Variable and constraint naming schemes are replaced with OPTMODEL equivalent
  versions
- Variables and constraints now preserve the order they are inserted to the
  problem
- :meth:`Model.to_frame` method is updated to reflect changes to VG and CG
  orderings
- Two solve methods, :meth:`Model.solve_on_cas` and
  :meth:`Model.solve_on_viya` are merged into :meth:`Model.solve`
- :meth:`Model.solve` method checks the available CAS actions and uses
  `runOptmodel` whenever possible
- As part of the merging process, :code:`lp` and :code:`milp` arguments are
  replaced with :code:`options` argument in :meth:`Model.solve` and
  :meth:`Model.to_optmodel`
- An optional argument :code:`frame` is added to :meth:`Model.solve` for
  forcing to use MPS mode and `solveLp`-`solveMilp` actions
- Minor changes are applied to :code:`__str__` and :code:`__repr__` methods
- Creation indices for objects are being kept using the return of the
  :func:`register_name` function
- Objective constant values are now being passed using new CAS action arguments
  when posssible
- A linearity check is added for models
- Test folder is added to the repository

Bug Fixes
+++++++++

- Nondeterministic behavior when generating MPS files is fixed.

Notes
+++++

- Abstract and nonlinear models can be solved on Viya only if `runOptmodel`
  action is available on the CAS server.
- Three new examples are added which demonstrate abstract model building.
- Some minor changes are applied to the existing examples.

v0.1.2 (April 24, 2018)
=======================

New Features
++++++++++++

- As an experimental feature, *sasoptpy* supports *saspy* connections now
- :meth:`Model.solve_local` method is added for solving optimization
  problems using SAS 9.4 installations
- :meth:`Model.drop_variable`, :meth:`Model.drop_variables`,
  :meth:`Model.drop_constraint`, :meth:`Model.drop_constraints` methods are
  added
- :meth:`Model.get_constraint` and :meth:`Model.get_constraints` methods are
  added to grab :class:`Constraint` objects in a model
- :meth:`Model.get_variables` method is added
- :code:`_dual` attribute is added to the :class:`Expression` objects
- :meth:`Variable.get_dual` and :meth:`Constraint.get_dual` methods are added
- :meth:`Expression.set_name` method is added

Changes
+++++++

- Session argument accepts :class:`saspy.SASsession` objects
- :meth:`VariableGroup.mult` method now supports :class:`pandas.DataFrame`
- Type check for the :meth:`Model.set_session` is removed to support new session
  types
- Problem and solution summaries are not being printed by default anymore,
  see :meth:`Model.get_problem_summary` and :meth:`Model.get_solution_summary`
- The default behavior of dropping the table after each solve is changed, but
  can be controlled with the :code:`drop` argument of the :meth:`Model.solve` method

Bug Fixes
+++++++++

- Fixed: Variables do not appear in MPS files if they are not used in the model
- Fixed: :meth:`Model.solve` primalin argument does not pass into options

Notes
+++++

- A .gitignore file is added to the repository.
- A new example is added: Decentralization.
- Both :ref:`CAS/Viya <examples/decentralization>` and 
  :ref:`SAS <examples/decentralization-saspy>` versions of the new example
  are available.
- There is a known issue with the nondeterministic behavior when creating MPS
  tables. This will be fixed with a hotfix after the release.
- A new option (no-ex) is added to makedocs script for skipping examples when
  building docs.


v0.1.1 (February 26, 2018)
==========================

New Features
++++++++++++

- Initial value argument 'init' is added for :class:`Variable` objects
- :meth:`Variable.set_init` method is added for variables
- Initial value option 'primalin' is added to :meth:`Model.solve` method
- Table name argument 'name', table drop option 'drop' and replace
  option 'replace' are added to :meth:`Model.solve` method
- Decomposition block implementation is rewritten, block numbers does
  not need to be consecutive and ordered :meth:`Model.upload_user_blocks`
- :meth:`VariableGroup.get_name` and :meth:`ConstraintGroup.get_name` methods
  are added
- :meth:`Model.test_session` method is added for checking if session is defined
  for models
- :func:`quick_sum` function is added for faster summation of
  :class:`Expression` objects

Changes
+++++++

- methods.py is renamed to utils.py

Bug Fixes
+++++++++

- Fixed: Crash in VG and CG when a key not in the list is called
- Fixed: get_value  of pandas is depreceated
- Fixed: Variables can be set as temporary expressions
- Fixed: Ordering in :func:`get_solution_table` is incorrect for multiple entries  

v0.1.0 (December 22, 2017)
==========================

- Initial release
