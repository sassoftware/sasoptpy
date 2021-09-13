#!/bin/python3
# saspy configuration for local tests

import os

ssh_conn = {'saspath': os.environ.get('SASPATH'),
          'ssh': '/usr/bin/ssh',
          'host': os.environ.get('SASHOST'),
          'encoding': 'latin1',
          'options': ['-t', 'dev/mva-v940m7', '-box', 'laxnd', '-nopp',
                         '-encoding', 'latin1'
                     ],
            'tunnel': 15000
          }
SAS_config_names = ['ssh_conn']
