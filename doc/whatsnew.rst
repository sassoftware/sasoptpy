
.. currentmodule:: sasoptpy

.. _whatsnew:


What's New
**********

This page outlines changes from each release.

v0.2.0 (TBD)
=======================

New Features
++++++++++++


Changes
+++++++
- Variable and constraint naming schemes are replaced with OPTMODEL equivalent
  versions.
- Variables and constraints now preserve the order they are inserted to the
  problem.
- :func:`Model.to_frame` method is updated to reflect changes to VG and CG
  orderings.

Bug Fixes
+++++++++
- Nondeterministic behavior when generating MPS files is fixed.

Notes
+++++

v0.1.2 (April 24, 2018)
=======================

New Features
++++++++++++

- As an experimental feature, **sasoptpy** supports *saspy* connections now
- :func:`Model.solve_local` method is added for solving optimization
  problems using SAS 9.4 installations
- :func:`Model.drop_variable`, :func:`Model.drop_variables`,
  :func:`Model.drop_constraint`, :func:`Model.drop_constraints` methods are
  added
- :func:`Model.get_constraint` and :func:`Model.get_constraints` methods are
  added to grab :class:`Constraint` objects in a model
- :func:`Model.get_variables` method is added
- :code:`_dual` attribute is added to the :class:`Expression` objects
- :func:`Variable.get_dual` and :func:`Constraint.get_dual` methods are added
- :func:`Expression.set_name` method is added

Changes
+++++++

- Session argument accepts :class:`saspy.SASsession` objects
- :func:`VariableGroup.mult` method now supports :class:`pandas.DataFrame`
- Type check for the :func:`Model.set_session` is removed to support new session
  types
- Problem and solution summaries are not being printed by default anymore,
  see :func:`Model.get_problem_summary` and :func:`Model.get_solution_summary`
- The default behavior of dropping the table after each solve is changed, but
  can be controlled with the :code:`drop` argument of the :func:`Model.solve` method

Bug Fixes
+++++++++

- Fixed: Variables do not appear in MPS files if they are not used in the model
- Fixed: :func:`Model.solve` primalin argument does not pass into options

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
- :func:`Variable.set_init` method is added for variables
- Initial value option 'primalin' is added to :func:`Model.solve` method
- Table name argument 'name', table drop option 'drop' and replace
  option 'replace' are added to :func:`Model.solve` method
- Decomposition block implementation is rewritten, block numbers does
  not need to be consecutive and ordered :func:`Model.upload_user_blocks`
- :func:`VariableGroup.get_name` and :func:`ConstraintGroup.get_name` methods
  are added
- :func:`Model.test_session` method is added for checking if session is defined
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
