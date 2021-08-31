#!/bin/python3
# saspy configuration for local tests

import os

sshsas = {'saspath': os.environ.get('SASPATH'),
          'ssh': '/usr/bin/ssh',
          'host': os.environ.get('SASHOST'),
          'encoding': 'latin1',
          'options': ['-t', 'dev/mva-v940m8', '-box', 'laxno', '-nopp',
                      '-encoding', 'latin1'
                     ],
        #   'tunnel': 15005
          }
SAS_config_names = ['sshsas']
