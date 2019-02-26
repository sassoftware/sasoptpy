#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import requests
import sys
import json
from urllib.parse import unquote

def print_details(res):
    #print(res.status_code, res.json())
    def pretty_print_post(req):
        if type(req.body) == bytes:
            body = unquote(req.body.decode())
        elif type(req.body) == str:
            body = unquote(req.body)
        else:
            body = ''
        print('{}\n{}\n{}\n{}\n\n{}\n{}'.format(
            '-----------START-----------',
            req.method + ' ' + req.path_url + ' HTTP/1.1',
            'Host: ' + 'localhost:5000',
            '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            body,
            '------------END-------------'
        ))

    def pretty_print_response(req):
        raw = req.raw
        print('{}\n{}\n{}\n\n{}\n{}'.format(
            '----------START------------',
            'HTTP/1.1 ' + str(req.status_code) + ' ' + req.reason,
            '\n'.join(['{}: {}'.format(i, req.headers[i]) for i in req.headers]),
            json.dumps(req.json(), indent=2),
            '-----------END-------------'
        ))

    pretty_print_post(res.request)
    pretty_print_response(res)


sys.path.insert(1, os.path.join(sys.path[0], '..'))
import sasoptpy as so
from sasoptpy.api import api
so.reset_globals()

# Start server
api.start(thread=True, host='127.0.0.1', port=5000)

host = 'http://127.0.0.1:5000'

# Get server and version info (#1)
res = requests.get(host)
print_details(res)

# Create new workspace (#4)
res = requests.post(host + '/workspaces',
                    data={'name': 'myworkspace',
                          'password': 12345})
print_details(res)

# If workspace exists, renew the token (#6)
res = requests.post(host + '/workspaces/myworkspace',
                    data={'password': 12345})
print_details(res)

# Save the token
token = 'Bearer ' + res.json()['token']
headers = {'Authorization': token}

# List workspaces (#3)
res = requests.get(host + '/workspaces')
print_details(res)

# Clean workspace (#2)
res = requests.post(host, data={'action': 'clean'}, headers=headers)
print_details(res)

# Get specific workspace
res = requests.get(host + '/workspaces/myworkspace', headers=headers)
print_details(res)

# Create a new CAS session
res = requests.post(host + '/sessions', headers=headers,
                    data={'name': 'mycas', 'host': 'rdcgrd001.unx.sas.com', 'port': 23037, 'auth': 'U:\.authinfo'})
print_details(res)

# Get list of CAS sessions
res = requests.get(host + '/sessions', headers=headers)
print_details(res)

print('--- Models ---')

# Create a new model
res = requests.post(host + '/models', headers=headers,
                    data={'name': 'knapsack', 'session': 'mycas'})
print_details(res)

# Get a list of models
res = requests.get(host + '/models', headers=headers)
print_details(res)

# Get specific model
res = requests.get(host + '/models/knapsack', headers=headers)
print_details(res)

print('--- Variables ---')

# print(14, "Create standalone variable")
# res = requests.post(host + '/variables', headers=headers,
#                     data={'name': 'x', 'vartype': 'binary'})
# print_details(res)

print(14, "Create standalone variable inside model")
res = requests.post(host + '/models/knapsack/variables', headers=headers,
                    data={'name': 'myvar', 'vartype': 'binary'})
print_details(res)

print(12, "Return a list of variables")
res = requests.get(host + '/variables', headers=headers)
print_details(res)

print(13, "Return a list of variables inside the model")
res = requests.get(host + '/models/knapsack/variables', headers=headers)
print_details(res)

print(17, "Create a variable group inside the model")
res = requests.post(host + '/models/knapsack/variable_groups', headers=headers,
                    json={'name': 'pick', 'index': [["pen","watch","cup"]], 'vartype': 'integer'})
print_details(res)

print(15, "Returns a list of variable groups")
res = requests.get(host + '/variable_groups', headers=headers)
print_details(res)

print(16, "Returns a list of variable groups inside the model")
res = requests.get(host + '/models/knapsack/variable_groups', headers=headers)
print_details(res)

print('--- Expressions ---')

print(20, "Set objective function of a model")
res = requests.post(host + '/models/knapsack/objectives', headers=headers,
                    json={'expression': "5*pick['pen']+20*pick['watch']+2*pick['cup']", 'sense': 'maximize', 'name': 'total_value'})
print_details(res)

print(18, "Return the objective function of a model")
res = requests.get(host + '/expressions', headers=headers)
print_details(res)

print(19, "Return a list of expressions")
res = requests.get(host + '/models/knapsack/objectives', headers=headers)
print_details(res)

print('--- Constraints ---')

print(23, "Creates a constraint inside the model")
res = requests.post(host + '/models/knapsack/constraints', headers=headers,
                    json={'expression': "1*pick['pen']+3*pick['watch']+10*pick['cup']<=22", 'name': 'total_weight'})
print_details(res)

print(21, "Returns a list of constraints")
res = requests.get(host + '/constraints', headers=headers)
print_details(res)

print(22, "Return a list of constraints inside the model")
res = requests.get(host + '/models/knapsack/constraints', headers=headers)
print_details(res)

print('--- Constraint Groups ---')

print(26, "Creates a constraint group inside the model")
res = requests.post(host + '/models/knapsack/constraint_groups', headers=headers,
                    json={
                        'expression': 'pick[i]<=5', 'index': "for i in ['pen','watch','cup']",
                        'name': 'bounds'})
print_details(res)

print(24, "Returns a list of constraint groups")
res = requests.get(host + '/constraint_groups', headers=headers)
print_details(res)

print(25, "Return a list of constraint groups inside the model")
res = requests.get(host + '/models/knapsack/constraint_groups', headers=headers)
print_details(res)

print('--- Data ---')

print(27, "Creates a data object in the server")
res = requests.post(host + '/data', headers=headers,
                    data={'name': 'capacity', 'value': '20'})
print_details(res)

print(27, "Creates a data object in the server")
values = [5, 20, 2]
res = requests.post(host + '/data', headers=headers,
                    json={'name': 'value_data', 'value': json.dumps(values)})
print_details(res)

print(27, "Creates a data object in the server")
weights = {'pen': 1, 'watch': 3, 'cup': 10}
res = requests.post(host + '/data', headers=headers,
                    json={'name': 'weight_data', 'value': json.dumps(weights)})
print_details(res)

# Get optmodel code of the model
res = requests.get(host+'/models/knapsack', headers=headers,
                 params={'format': 'optmodel'})
print_details(res)
print(res.json()['optmodel'])


# Solve
res = requests.post(host+'/models/knapsack/solutions', headers=headers,
              data={'stream': False})
print_details(res)