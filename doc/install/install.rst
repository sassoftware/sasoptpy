
.. _install:

.. currentmodule:: sasoptpy

Installation
============

Python Version Support and Dependencies
---------------------------------------

Current version is developed and tested for Python 3.6 and later.

It requires the following packages:

* NumPy
* SASPy
* SWAT
* pandas

Getting sasoptpy
----------------

You can install sasoptpy by using `pip` or `conda`::

   pip install sasoptpy

   conda install -c sas-institute sasoptpy

Any dependencies are installed automatically.

Depending on your installation, you might need to add the `conda-forge` channel to `conda`::

    conda config --append channels conda-forge
   
GitHub repository
+++++++++++++++++

You can also get stable and development versions of sasoptpy from the GitHub repository.
To get the latest version,  call::

  git clone https://github.com/sassoftware/sasoptpy.git

Then inside the sasoptpy folder, call::

  pip install .

Alternatively, you can use::

  python setup.py install


