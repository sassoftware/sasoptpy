
.. currentmodule:: sasoptpy

.. _whatsnew:


What's New
**********

This page outlines changes from each release.

v0.1.1 (TBD)
============

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
