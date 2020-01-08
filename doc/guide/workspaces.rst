
.. currentmodule:: sasoptpy

.. _workspaces:

Workspaces
==========

.. ipython:: python
   :suppress:

   import sasoptpy as so

One of the most powerful features of SAS Optimization and PROC OPTMODEL is the ability to combine several optimization
models in a single call. Using this ability, users can read a common data set once, or parallelize solve steps for
similar subproblems.

Newly introduced :class:`Workspace` provides this ability in a familiar syntax. Compared to :class:`Model` objects,
a :class:`Workspace` can consists of several models and able to use server-side data and OPTMODEL statements in a
more detailed way.

Creating a workspace
~~~~~~~~~~~~~~~~~~~~

A :class:`Workspace` should be called using the `with` keyword of Python as follows:

>>> with so.Workspace('my_workspace') as w:
>>>    ...

You can define several models in the same workspace, and solve problems multiple times. All the statements are sent
to server after :meth:`Workspace.submit` is called.

Adding components
~~~~~~~~~~~~~~~~~

Unlike :class:`Model` objects, where components are added explicitly, objects defined inside a :class:`Workspace` is
added automatically.

For example, adding a new variable is performed as follows:

.. ipython:: python

   with so.Workspace(name='my_workspace') as w:
      x = so.Variable(name='x', vartype=so.integer)

Contents of a workspace can be displayed using :meth:`Workspace.to_optmodel`:

.. ipython:: python

   print(w.to_optmodel())


See the following full example where a data is loaded into the server, and problem is solved using a Workspace:




Abstract actions
================


Adding abstract actions
~~~~~~~~~~~~~~~~~~~~~~~

Grabbing results
~~~~~~~~~~~~~~~~

List of abstract actions
~~~~~~~~~~~~~~~~~~~~~~~~

