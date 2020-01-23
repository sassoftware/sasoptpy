
.. currentmodule:: sasoptpy

.. _sessions:

Sessions
========

CAS Sessions
~~~~~~~~~~~~

A :class:`swat.cas.connection.CAS` session is needed to solve optimization 
problems with *sasoptpy* using SAS Viya OR solvers.
See the SAS documentation to learn more about CAS sessions and SAS Viya.

A sample CAS Session can be created using the following commands.

.. ipython:: python
   :suppress:
   
   import os
   cas_host = os.getenv('CASHOST')
   cas_port = os.getenv('CASPORT')
   cas_username = os.getenv('CASUSERNAME')
   cas_password = None
   import sasoptpy
   sasoptpy.reset_globals()

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


SAS Sessions
~~~~~~~~~~~~

A :class:`saspy.SASsession` session is needed to solve optimization 
problems with *sasoptpy* using SAS/OR solvers on SAS 9.4 clients.

A sample SAS session can be created using the following commands.

>>> import sasoptpy as so
>>> import saspy
>>> sas_session = saspy.SASsession(cfgname='winlocal')
>>> m = so.Model(name='demo', session=sas_session)
>>> print(repr(m))
sasoptpy.Model(name='demo', session=saspy.SASsession(cfgname='winlocal'))


It is possible to connect to a SAS session using a configuration file

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

A SAS session can be terminated as follows:

.. ipython:: python

   sas.endsas()





