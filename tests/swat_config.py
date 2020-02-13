
import os
from swat import CAS
import warnings

def create_cas_connection():
    cas_args = {'host': os.environ.get('CASHOST'),
                'port': int(os.environ.get('CASPORT'))}
    authinfo = os.environ.get('AUTHINFO', None)
    if authinfo:
        cas_args['authinfo'] = authinfo
        return CAS(**cas_args)

    username = os.environ.get('CASUSERNAME', None)
    if username:
        cas_args['username'] = username
        cas_args['password'] = os.environ.get('CASPASSWORD', None)
        return CAS(**cas_args)

    warnings.warn('CAS connection cannot be established.', RuntimeWarning)
    return None
