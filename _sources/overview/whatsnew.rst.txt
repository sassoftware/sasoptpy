
.. currentmodule:: sasoptpy

.. _whatsnew:


What's New
**********

New Features
++++++++++++

- Added workspaces; for more information, see :ref:`Workspaces in User Guide <workspaces>` and :ref:`Efficiency Analysis example <efficiency-analysis>`
- Added :ref:`package configurations <configurations>`
- Added :ref:`abstract actions <abstract-actions>` that allow server-side operations. Highlights include:

  - :func:`actions.read_data` and :func:`actions.create_data`
  - :func:`actions.for_loop` and :func:`actions.cofor_loop`
  - :func:`actions.print_item`
  - :func:`actions.solve`

- Added structure decorators for better control of submissions

Changes
+++++++

- Refactored the entire package; sasoptpy now has `core`, `abstract`, `interface`,
  `session`, and `util` directories
- Experimental RESTful API was dropped
- `get_obj_by_name` function was removed
- `lso` solver was renamed `blackbox`
- Because of the use of literal strings (:pep:`498`), only Python 3.6 or later versions are supported

Bug Fixes
+++++++++

- Fixed: Arithmetic operations with powers are generating incorrect results
- Fixed: Variable groups with space in their index are not getting values
- Fixed: Constraints without directions do not produce an error
- Fixed: Documentation does not mention conda-forge library requirement
- Fixed: Single-dimensional parameters are hard to access

