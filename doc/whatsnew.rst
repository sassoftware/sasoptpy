
.. currentmodule:: sasoptpy

.. _whatsnew:


What's New
**********

v1.0.0-alpha (TBD)
==================

New Features
++++++++++++

- Added workspaces, see :class:`Workspace`
- Added configurations
- Added several actions to be performed in workspaces, highlights include:

  - :func:`actions.read_data` and :func:`actions.create_data`
  - :func:`actions.for_loop` and :func:`actions.cofor_loop`
  - :func:`actions.print_item`
  - :func:`actions.solve`

- Added structure decorators for better control of submissions

Changes
+++++++

- Refactored entire package, now sasoptpy has `core`, `abstract`, `interface`,
  `session` and `util` directories
- Experimental RESTful API is dropped
- `get_obj_by_name` function is removed
- Following SAS Viya changes, `lso` solver is renamed as `blackbox`

Bug Fixes
+++++++++

- Fixed: Arithmetic operations with powers are generating incorrect results
- Fixed: Variable groups with space in their index is not getting values
- Fixed: Constraints without directions do not produce an error
- Fixed: Documentation does not mention conda-forge library requirement
- Fixed: Single-dimensional parameters are hard to access
