
Expression
==========

.. currentmodule:: sasoptpy

Constructor
~~~~~~~~~~~

.. autosummary::
   :toctree: generated/
   :template: autosummary/class_without_autosummary.rst

   Expression
   Auxiliary
   Symbol

General methods
~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Expression.set_name
   Expression.set_permanent
   Expression.set_temporary
   Expression.get_name
   Expression.get_value
   Expression.get_dual

Operations
~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Expression.add
   Expression.copy
   Expression.mult
   Expression.get_member
   Expression.get_member_dict
   Expression.get_member_value
   Expression.get_constant
   Expression.set_member
   Expression.set_member_value
   Expression.add_to_member_value
   Expression.mult_member_value
   Expression.copy_member
   Expression.delete_member


Class methods
~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Expression.to_expression

Private Methods
~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Expression._expr
   Expression._is_linear
   Expression._relational
   Expression.__repr__
   Expression.__str__
