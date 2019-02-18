import requests
import json

import sasoptpy as so
from sasoptpy.api import api
so.reset_globals()

def test(cashost, port):

    # Start server
    api.start(thread=True, host='127.0.0.1', port=5000)

    host = 'http://127.0.0.1:5000'

    # Get server and version info
    res = requests.get(host)

    # Create new workspace
    res = requests.post(host + '/workspaces',
                        data={'name': 'myworkspace',
                              'password': 12345})

    # If workspace exists, renew the token
    res = requests.post(host + '/workspaces/myworkspace',
                        data={'password': 12345})

    # Save the token
    token = 'Bearer ' + res.json()['token']
    headers = {'Authorization': token}

    # Clean workspace
    res = requests.post(host, data={'action': 'clean'}, headers=headers)

    # Create a new CAS session
    res = requests.post(host + '/sessions', headers=headers,
                        data={'name': 'mycas', 'host': cashost, 'port': port})

    # Create a new model
    res = requests.post(host + '/models', headers=headers,
                        data={'name': 'knapsack', 'session': 'mycas'})

    # Create variables
    res = requests.post(host + '/models/knapsack/variable_groups', headers=headers,
                        json={'name': 'pick', 'index': [["pen","watch","cup"]], 'vartype': 'integer'})

    # Set objective function
    res = requests.post(host + '/models/knapsack/objectives', headers=headers,
                        json={'expression': "5*pick['pen']+20*pick['watch']+2*pick['cup']", 'sense': 'maximize',
                              'name': 'total_value'})

    # Capacity constraint
    res = requests.post(host + '/models/knapsack/constraints', headers=headers,
                        json={'expression': "1*pick['pen']+3*pick['watch']+10*pick['cup']<=22", 'name': 'total_weight'})

    # Individual limits for items
    res = requests.post(host + '/models/knapsack/constraint_groups', headers=headers,
                        json={
                            'expression': 'pick[i]<=5', 'index': "for i in ['pen','watch','cup']",
                            'name': 'bounds'})

    # Get optmodel code of the model
    res = requests.get(host+'/models/knapsack', headers=headers,
                     params={'format': 'optmodel'})
    print(res.json()['optmodel'])

    # Solve the model
    res = requests.post(host + '/models/knapsack/solutions', headers=headers,
                        data={'stream': False})
    sols = res.json()['solutions']
    for i in sols:
        print(i, sols[i])
