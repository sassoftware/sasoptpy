
.. currentmodule:: sasoptpy

.. _web-api:

RESTful API
***********

*sasoptpy* provides an experimental RESTful API as of v0.2.1.
This API is intended to be used to connect development on other languages through a common interface.

.. csv-table:: List of RESTful API requests
   :file: web-api.csv
   :widths: 2, 1, 6, 3, 15
   :header-rows: 1

Overview
++++++++

You need to start *sasoptpy*'s web server using

.. code-block:: python

   from sasoptpy.api import api
   api.start()

You can also start the web server in a separate thread using `thread=True` parameter.

Status of the server can be checked using a request to the `localhost` address.

..  http:example:: curl wget httpie python-requests

    GET / HTTP/1.1
    Host: localhost:5000
    Accept: application/json


    HTTP/1.1 200 OK
    Content-Type: application/json
    Server: Werkzeug/0.14.1 Python/3.6.5

    {
      "package": "sasoptpy",
      "version": "v0.2.1"
    }


Almost all *sasoptpy* RESTful API request requires an authorization token.
You can create a separate workspace for your work without affecting other work that might be running.
To create a workspace, you need to make a `POST` request to `/workspaces` with a name and password.

..  http:example:: curl wget httpie python-requests

    POST /workspaces HTTP/1.1
    Host: localhost:5000
    Accept: application/json
    Content-Type: application/json

    {
      "name": "myworkspace",
      "password": 12345
    }


    HTTP/1.1 200 OK
    Content-Type: application/json
    Server: Werkzeug/0.14.1 Python/3.6.5

    {
      "token": "eyJhbGciOiJIUzI1NiIsImlhdCI6MTU0NTIzNzQ3MSwiZXhwIjoxNTQ1MjM4MDcxfQ.eyJuYW1lIjoibXl3b3Jrc3BhY2VzIn0.WJg6W5LjzFEfBcMs3zw8-e6NK1bdEP7pvbctO7bgm6c",
      "duration": "600"
    }