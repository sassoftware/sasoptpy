
.. currentmodule:: sasoptpy

.. _sessions:

Sessions
========


.. _cas-sessions:

CAS Sessions
~~~~~~~~~~~~

A :class:`swat.cas.connection.CAS` session is needed in order to use sasoptpy and SAS Optimization solvers
to solve optimization problems.
You can find more details about CAS sessions in `SWAT Documentation <https://sassoftware.github.io/python-swat/>`_.

You can create a sample CAS Session as follows:

.. ipython:: python
   :suppress:
   
   import os
   cas_host = os.getenv('CASHOST')
   cas_port = os.getenv('CASPORT')
   cas_username = os.getenv('CASUSERNAME')
   cas_password = None
   import sasoptpy
   sasoptpy.reset()

.. ipython:: python
   :suppress:

   import sasoptpy as so
   from swat import CAS
   s = CAS(hostname=cas_host, username=cas_username, password=cas_password, port=cas_port)
   m = so.Model(name='demo', session=s)
   print(repr(m))


>>> import sasoptpy as so
>>> from swat import CAS
>>> s = CAS(hostname=cas_host, username=cas_username, password=cas_password, port=cas_port)
>>> m = so.Model(name='demo', session=s)
>>> print(repr(m))
sasoptpy.Model(name='demo', session=CAS(hostname, port, username, protocol='cas', name='py-session-1', session=session-no))

You can end the session and close the connection as follows:

>>> s.terminate()

.. _sas-sessions:

SAS Sessions
~~~~~~~~~~~~

A :class:`saspy.SASsession` session is needed in order to use sasoptpy and SAS/OR solvers to solve optimization
problems on SAS 9.4 clients.

You can create a sample SAS session as follows:

>>> import sasoptpy as so
>>> import saspy
>>> sas_session = saspy.SASsession(cfgname='winlocal')
>>> m = so.Model(name='demo', session=sas_session)
>>> print(repr(m))
sasoptpy.Model(name='demo', session=saspy.SASsession(cfgname='winlocal'))


You can connect to a SAS session by using a configuration file

.. ipython:: python
   :suppress:

   import saspy
   config_file = os.path.abspath('../tests/examples/saspy_config.py')

.. ipython:: python

   sas = saspy.SASsession(cfgfile=config_file)

.. ipython:: python

   m = so.Model(name='demo', session=sas)

.. ipython:: python

   print(m.get_session().sasver)

You can terminate the SAS session as follows:

.. ipython:: python

   sas.endsas()





