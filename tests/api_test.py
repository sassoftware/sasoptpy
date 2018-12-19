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

def print_details(res):
    print(res.status_code, res.json())

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
if res.status_code == 422:
    res = requests.post(host + '/workspaces/myworkspace',
                        data={'password': 12345})

# Save the token
token = 'Bearer ' + res.json()['token']
headers = {'Authorization': token}

# List workspaces (#3)
res = requests.get(host + '/workspaces')
print_details(res)

# Clean workspace (#2)
res = requests.post(host, data={'action': 'clean'}, headers=headers)
print_details(res)
