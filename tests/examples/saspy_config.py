#!/bin/python3
# saspy configuration for local tests

sshsas = {'saspath': os.environ.get('SASPATH'),
          'ssh': '/usr/bin/ssh',
          'host': os.environ.get('SASHOST'),
          'encoding': 'iso8859_15',
          'options': ['-t', 'dev/mva-v940m6', '-box', 'laxno', '-nopp',
                      '-encoding', 'latin9']
          }
SAS_config_names = ['sshsas']
