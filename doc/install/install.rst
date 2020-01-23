
.. _install:

.. currentmodule:: sasoptpy

Installation
============

Python version support and dependencies
---------------------------------------

*sasoptpy* is developed and tested for Python version 3.6+.

It requires the following packages:

* numpy
* saspy
* swat
* pandas

Getting sasoptpy
----------------

*sasoptpy* can be installed using `pip` or `conda`::

   pip install sasoptpy

   conda install -c sas-institute sasoptpy

Any dependencies should be installed automatically.

Depending on your installation, you may need to add `conda-forge` channel to `conda` using::

    conda config --append channels conda-forge
   
GitHub repository
+++++++++++++++++

You can also get stable and development versions of *sasoptpy* from the GitHub repository.
To get the latest version,  call::

  git clone https://github.com/sassoftware/sasoptpy.git

Then inside the sasoptpy folder, call::

  pip install .

Alternatively, you can use::

  python setup.py install


