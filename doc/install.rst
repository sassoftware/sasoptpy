
.. _install:

.. currentmodule:: sasoptpy

Installation
============

Python version support and dependencies
---------------------------------------

**sasoptpy** is developed and tested for Python version 3.5+.

It depends on the following packages:

* numpy
* saspy (Optional)
* swat
* pandas

.. note::

   You need to download
   `swat package <https://sassoftware.github.io/python-swat/>`_
   from the online repository before using **sasoptpy**. 


Getting swat
------------

`swat <https://github.com/sassoftware/python-swat>`_ should be available
to use solver actions.

swat releases are listed at
`<https://github.com/sassoftware/python-swat/releases>`_.
After downloading the platform-specific release file, it can be installed using
pip::

	pip install python-swat-X.X.X-platform.tar.gz

Getting saspy
-------------

`saspy <https://github.com/sassoftware/saspy>`_ should be available to use
solver methods for local SAS 9.4 clients.
**sasoptpy** support for local solve methods are currently experimental.
saspy is not a requirement for the SAS Viya functionality.

saspy releases are listed at
`<https://github.com/sassoftware/saspy/releases>`_.
Easiest way to download the latest stable version of saspy is to use::

        pip install saspy

	
Getting sasoptpy
----------------

Latest release of **sasoptpy** can be obtained from the online repository.
Call::

  git clone https://github.com/sassoftware/sasoptpy.git

Then inside the sasoptpy folder, call::

  pip install .

Alternatively, you can use::

  python setup.py install


Step-by-step installation
-------------------------

#. **Installing pandas and numpy**
   
   First, download and install numpy and pandas using pip:

   .. code-block:: bash

      pip install numpy
      pip install pandas

      
#. **Installing the swat package**

   First, check the
   `swat release page <https://github.com/sassoftware/python-swat/releases>`_
   to find the latest release of the SAS-SWAT package for your environment.

   Then install it using

   .. code-block:: bash

      pip install python-swat-X.X.X.platform.tar.gz

   As an example, run

   .. code-block:: bash

      wget https://github.com/sassoftware/python-swat/releases/download/v1.2.1/python-swat-1.2.1-linux64.tar.gz
      pip install python-swat-1.2.1-linux64.tar.gz

   to install the version 1.2.1 of the swat package for 64-bit Linux
   environments.

#. **Installing sasoptpy**

   Finally you can install *sasoptpy* by downloading the latest archive file
   and install via pip.

   .. code-block:: bash

      wget *url-to-sasoptpy.tar.gz*
      pip install sasoptpy.tar.gz

   Latest release file is available at
   `Github releases <https://github.com/sassoftware/sasoptpy/releases/latest>`_
   page.

