
.. currentmodule:: sasoptpy

Workflows
=========

*sasoptpy* can work both with client-side data and server-side data.
Some limitations to the functionalities may apply in terms of which
workflow is being used. In this part, overall flow of the package
is explained.

Client-side models
------------------

If the data is on the client-side (Python), then a concrete model is generated
on the client-side and uploaded using one of the available CAS actions.

Using client-side models brings several advantages, such as accessing
variables, expressions, and constraints directly. You may do more intensive 
operations like filter data, sort values, changing variable values,
and print expressions more easily.

There are two main disadvantages of working with client-side models.
First, if your model is relatively big size, then the generated
MPS DataFrame or OPTMODEL codes may allocate a large memory on your
machine.
Second, the information that needs to be passed from client to server
might be bigger than using a server-side model.

See the following representation of the client-side model workflow for CAS (Viya) servers:

.. image:: _static/images/clientside_cas.png

See the following representation of the client-side model workflow for SAS clients:

.. image:: _static/images/clientside_sas.png




Server-side models
------------------

If the data is on the server-side (CAS or SAS), then an abstract model
is generated on the client-side. This abstract model is later converted to
PROC OPTMODEL code, which combines the data on the server.

The main advantage of the server-side models is faster upload times compared
to client-side. This is especially very noticable when using large chunks of
variable and constraint groups.

The only disadvantage of using server-side models is that variables are often
needs to be accessed directly from the resulting SASDataFrame objects. Since
components of the models are abstract, accessing objects directly is often
not possible.

See the following representation of the server-side model workflow for CAS (Viya) servers:

.. image:: _static/images/serverside_cas.png

See the following representation of the server-side model workflow for SAS clients:

.. image:: _static/images/serverside_sas.png

