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

"""
API includes implementation of RESTful API for connecting other applications
"""

from collections import OrderedDict
from swat import CAS
import sys
from flask import Response, stream_with_context, Flask, request
from flask.json import jsonify
from flask_restful import Resource, Api, reqparse
from gevent.pywsgi import WSGIServer
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as TimedSerializer, Signer,
                          BadSignature, SignatureExpired)
import json
import secrets
import threading
import time


class UserApi(Api):
    """
    Main class for using the API abilities
    """

    def __init__(self):
        self.app = Flask('sasoptpy')
        super().__init__(self.app)
        self.app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
        self.workspaces = dict()
        self.setup_resources()

    def setup_resources(self):
        self.add_resource(Entry, '/')
        self.add_resource(Workspaces, '/workspaces', '/workspaces/<string:workspace>')
        self.add_resource(Sessions, '/sessions')
        self.add_resource(Data, '/data', '/data/<string:name>')
        self.add_resource(Models, '/models', '/models/<string:model_name>')
        self.add_resource(
            Variables, '/variables', '/models/<string:model_name>/variables')
        self.add_resource(
            Expressions, '/expressions', '/models/<string:model_name>/objectives')
        self.add_resource(
            Constraints, '/constraints', '/models/<string:model_name>/constraints')
        self.add_resource(
            Solutions, '/models/<string:model_name>/solutions')
        self.add_resource(
            VariableGroups, '/variable_groups', '/models/<string:model_name>/variable_groups')
        self.add_resource(
            ConstraintGroups, '/constraint_groups', '/models/<string:model_name>/constraint_groups')

    def start(self, host='', port=5000, thread=False):
        if thread:
            def gevent_run():
                self.http_server = WSGIServer((host, port), self.app)
                self.http_server.serve_forever()
            self.t = threading.Thread(target=gevent_run)
            self.t.setDaemon(True)
            print('Starting WSGI Server...')
            self.t.start()
            time.sleep(1)
        else:
            print('Starting WSGI Server...')
            self.http_server = WSGIServer((host, port), self.app)
            self.http_server.serve_forever()

    def stop(self):
        if self.http_server is None:
            raise RuntimeError('Not running HTTP Server')
        self.t = None
        self.http_server.stop()
        return 'Server shutting down...'

    @classmethod
    def transform(cls, val):
        import sasoptpy as so
        return so.utils._transform.get(val, val)


def verify_auth_token(func):
    """
    Decorator for functions requiring authorization token. Passes the workspace as an argument.
    """

    def wrapper(*args, **kwargs):

        parser = reqparse.RequestParser()
        parser.add_argument('Authorization', location='headers', required=True)
        args = parser.parse_args()
        splittoken = args['Authorization'].split()
        if len(splittoken) == 2 and splittoken[0] == 'Bearer':
            s = TimedSerializer(api.app.config['SECRET_KEY'])
            try:
                data = s.loads(splittoken[1])
            except SignatureExpired:
                return {'message': 'Error: Token is expired.'}, 400
            except BadSignature:
                return {'message': 'Error: Bad Signature. Token is not verified.'}, 400
            name = data['name']
            if name in api.workspaces:
                ws = api.workspaces[name]
                return func(*args, **kwargs, ws=ws)
            else:
                return {'message': 'Error: Workspace {} does not exist'.format(name)}, 400
        else:
            return {'message': 'Error: Bearer token is not passed or malformed.'}, 400

    return wrapper


def generate_auth_token(name, expiration=600):
    """
    Generates an authentication token for given expiration time.
    """
    s = TimedSerializer(api.app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'name': name})


class Workspace:

    def __init__(self, name, password):
        import sasoptpy as so
        self.so = so
        self.name = name
        self.sessions = OrderedDict()
        self.models = OrderedDict()
        self.variables = OrderedDict()
        self.variable_groups = OrderedDict()
        self.constraints = OrderedDict()
        self.constraint_groups = OrderedDict()
        self.expressions = OrderedDict()
        self.parameters = OrderedDict()
        self.sets = OrderedDict()
        self.tables = OrderedDict()
        self.data = OrderedDict()
        self.dictlist = [
            self.sessions,
            self.models,
            self.variables,
            self.variable_groups,
            self.constraints,
            self.constraint_groups,
            self.expressions,
            self.parameters,
            self.sets,
            self.tables]

        s = Signer(api.app.config['SECRET_KEY'])
        mystr = '{} {}'.format(name, password)
        self._secret = s.sign(mystr.encode('utf-8'))

    def is_owner(self, name, password):
        """
        Checks if a given name and password matches with original owner.

        Parameters
        ----------
        name : string
            User name to verify identity of the original owner
        password : string
            Password to verify identity of the original owner

        Returns
        -------
        bool : True if the passed identity is the original owner
        """

        s = Signer(api.app.config['SECRET_KEY'])
        current_secret = s.sign('{} {}'.format(name, password).encode('utf-8'))

        return current_secret == self._secret

    def get_combined(self):
        """
        Returns a combined dictionary of the workspace objects
        """
        return {**self.variables,
                **self.variable_groups,
                **self.data, 'ws': self,
                'so': self.so,
                'sum': self.so.quick_sum}

class Workspaces(Resource):
    """
    Creates a workspace for a user, using a token-based authentication.
    """

    def post(self, workspace=None):
        """
        Creates a workspace using a workspace name and returns a token.
        """
        parser = reqparse.RequestParser()

        # If no workspace is passed, user is trying to create a new one
        if workspace is None:
            parser.add_argument('name', type=str, help='Workspace name', required=True)
        else:
            # Else, it is trying to renew the token
            if workspace not in workspace:
                return {'message': 'Workspace does not exist, cannot renew token.'}, 400

        parser.add_argument('password', type=str, help='Password for workspace', required=True)
        args = parser.parse_args()

        if workspace is None:
            # If user is trying to create a new workspace but if the name already exists, give an error
            if args['name'] in api.workspaces:
                return {'message': 'A workspace with the same name already exists.'}, 422
            name = args['name']
        else:
            # If renewing a token, check if workspace belongs to the user
            if not api.workspaces[workspace].is_owner(workspace, args['password']):
                return {'message': 'Wrong password, cannot renew token'}, 401
            name = workspace


        api.workspaces[name] = Workspace(name, args['password'])
        token = generate_auth_token(name, 600)
        return {'token': token.decode('ascii'), 'duration': 600}, 201

    def get(self, workspace=None):
        """
        Shows a list of available workspace names.
        """
        if workspace is None:
            return {'workspaces': list(api.workspaces.keys())}, 200
        else:
            return self.test(name=workspace)

    @verify_auth_token
    def test(self, name, ws):
        if name == ws.name:
            return {'status': 'Token is valid for the workspace'}, 200
        else:
            return {'status': 'Error: Token is not valid for the workspace'}, 422

    def delete(self):
        """
        Deletes a workspace
        """
        pass


class Entry(Resource):
    """
    Entry point for the API listing information about package.
    """

    def get(self):
        """
        Get current sasoptpy version
        """
        import sasoptpy as so
        return {
            'package': 'sasoptpy',
            'version': so.__version__}, 200

    @verify_auth_token
    def post(self, ws):

        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, help='Task for the workspace', required=True)
        args = parser.parse_args()

        if isinstance(args, tuple):
            return args

        if args['action'] == 'clean':
            # Clean variables inside session
            ws.so.reset_globals()
            for i in ws.dictlist:
                i.clear()
            return {'message': 'Cleaned the workspace contents',
                    'workspace': ws.name}, 200
        elif args['action'] == 'submit':
            # Submit Python code as a string
            return {'message': 'Not implemented'}, 501  # TODO finish python submission



class Sessions(Resource):
    """
    Session objects for Viya connections
    """

    @verify_auth_token
    def get(self, ws):
        """
        Returns a list of sessions
        """

        return {'sessions': [i for i in ws.sessions]}, 200

    @verify_auth_token
    def post(self, ws):
        """
        Creates a new CAS connection
        """

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the session', required=True)
        parser.add_argument('host', type=str, help='Address of the CAS Server', required=True)
        parser.add_argument('port', type=int, help='Port number of the CAS Server', required=True)
        parser.add_argument('auth', type=str, help='Absolute address of the auth file on client')
        args = parser.parse_args()

        try:
            s = ws.sessions[args['name']] = CAS(args['host'],
                                                args['port'],
                                                authinfo=args.get('auth', None))
        except:
            ws.sessions[args['name']] = None
            return {
                'status': 400, 'message': 'Cannot create CAS session'}, 400

        return {
            'id': list(s.sessionid().values())[0],
            'name': args['name']}, 201


class Models(Resource):
    """
    Model objects
    """

    @verify_auth_token
    def get(self, model_name=None, ws=None):
        """
        Returns a single model or a list of models

        Parameters
        ----------
        model_name : string, optional
            Name of a specific model requested
        ws : Workspace
            Current workspace, parsed using the authorization token
        """

        if model_name is None:
            return {'models': {i: ws.models[i]._name for i in ws.models}}, 200
        else:
            return Models.getmodel(model_name, ws)

    @staticmethod
    def getmodel(model_name, ws):
        """
        Get info about a specific model name
        """

        parser = reqparse.RequestParser()
        parser.add_argument('format', type=str, help='Output format', default='summary')
        args = parser.parse_args()

        if model_name in ws.models:
            if args['format'] == 'summary':
                return {
                    'name': model_name,
                    'workspace': ws.name,
                    'session': ws.models[model_name]._session_name}, 200
            elif args['format'] == 'optmodel':
                return {
                    'name': model_name,
                    'workspace': ws.name,
                    'optmodel': ws.models[model_name].to_optmodel()}, 200
        else:
            return {
                'message': 'Model name is not found'}, 404

    @verify_auth_token
    def post(self, ws):
        """
        Creates a new model
        """

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the model', required=True)
        parser.add_argument('session', type=str, help='Name of the CAS session', required=True)
        args = parser.parse_args()

        session = None
        if args['session'] in ws.sessions:
            session = ws.sessions[args['session']]

        m = ws.so.Model(name=args['name'],
                        session=session)
        ws.models[m._name] = m
        m._session_name = args['session']

        return {
            'name': m._name,
            'workspace': ws.name,
            'session': args['session']
            }, 201


class Data(Resource):
    """
    Represents data objects
    """

    @verify_auth_token
    def get(self, name=None, ws=None):
        return {'message': 'Not implemented'}, 501

    @verify_auth_token
    def post(self, ws=None):
        # Parse the input
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the data variable', required=True)
        parser.add_argument('value', type=str, help='JSON representation of data', required=True)
        args = parser.parse_args()
        # Save to the workspace
        ws.data[args['name']] = obj = json.loads(args['value'])
        size = '' if getattr(obj, '__iter__', None) is None else len(obj)
        # Return
        return {'name': args['name'],
                'type': type(obj).__name__,
                'len': size}, 201


class Variables(Resource):
    """
    Represents variables inside models
    """

    @verify_auth_token
    def get(self, model_name=None, ws=None):
        if model_name is None:
            return {'variables':
                    {i: ws.variables[i]._name for i in ws.variables}}, 200
        else:
            if model_name in ws.models:
                m = ws.models[model_name]
                return {'variables': [i._name for i in m.get_variables()]}, 200
            else:
                return {
                    'message': 'Model name is not found'}, 404

    @verify_auth_token
    def post(self, model_name=None, ws=None):
        '''
        Add new variables to model
        '''

        if model_name in ws.models:
            m = ws.models[model_name]
        else:
            return {
                'message': 'Model name is not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the variable')
        parser.add_argument('lb', type=float,
                            help='Lower bound of the variable')
        parser.add_argument('ub', type=float,
                            help='Upper bound of the variable')
        parser.add_argument('vartype', type=str, help='Type of the variable')
        args = parser.parse_args()

        v = m.add_variable(name=args['name'], lb=args['lb'], ub=args['ub'],
                           vartype=UserApi.transform(args['vartype']))
        ws.variables[v._name] = v

        return {
            'name': v._name}, 201


class VariableGroups(Resource):
    """
    Represents variables inside models
    """

    @verify_auth_token
    def get(self, model_name=None, ws=None):
        if model_name is None:
            return {'variablegroups':
                    {i: ws.variable_groups[i]._name for i in ws.variable_groups}}, 200
        else:
            if model_name in ws.models:
                m = ws.models[model_name]
                return {'variablegroups': [i._name for i in m._vargroups]}, 200
            else:
                return {
                    'message': 'Model name is not found'}, 404

    @verify_auth_token
    def post(self, model_name=None, ws=None):
        """
        Add new variable groups to model
        """

        if model_name in ws.models:
            m = ws.models[model_name]
        else:
            return {
                'message': 'Model name is not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('index', type=list, location='json', help='Indices of the variable group', action='append')
        parser.add_argument('name', type=str, help='Name of the variable group')
        parser.add_argument('lb', type=float,
                            help='Lower bound of the variable group')
        parser.add_argument('ub', type=float,
                            help='Upper bound of the variable group')
        parser.add_argument('vartype', type=str, help='Type of the variable group')
        parser.add_argument('init', type=float, help='Initial value of the variable group')
        args = parser.parse_args()

        combined = ws.get_combined()

        index = args['index']
        indices = []
        for i in index:
            if isinstance(i, str) and i[0] == '$':
                indices.append(combined[i[1:]])
            else:
                indices.append(i)

        vg = m.add_variables(
            *indices, name=args.get('name', None), lb=args.get('lb', None), ub=args.get('ub', None),
            vartype=UserApi.transform(args.get('vartype', None)))

        ws.variable_groups[args['name']] = vg

        return {'message': 'Variable group is created', 'name': vg._name}, 201


class Expressions(Resource):

    @verify_auth_token
    def get(self, model_name=None, ws=None):
        """
        Returns a list of expressions
        """
        if model_name is None:
            return {'expressions':
                    {i: str(ws.expressions[i]) for i in ws.expressions}}, 200
        else:
            m = ws.models[model_name]
            return {'objective': {m._objective._name: str(m._objective)}}

    @verify_auth_token
    def post(self, model_name=None, ws=None):
        """
        Creates a new expression
        """
        if model_name is not None and model_name not in ws.models:
            return {
                'message': 'Model name is not found'}, 404
        elif model_name is not None:
            m = ws.models[model_name]
        else:
            m = None

        parser = reqparse.RequestParser()
        parser.add_argument('expression', type=str, help='Expression')
        parser.add_argument('sense', type=str, help='Sense if an objective')
        parser.add_argument('name', type=str, help='Name of the expression')
        args = parser.parse_args()

        combined = ws.get_combined()
        # Open transfer of objects
        ws.so.utils.transfer_allowed = True
        ws.so.utils._load_transfer(combined)

        e = eval(args['expression'], None, combined)

        # Clear transfer
        ws.so.utils.transfer_allowed = False
        ws.so.utils._clear_transfer()

        if m is not None:
            e = m.set_objective(e, sense=args['sense'], name=args['name'])
        else:
            e.set_name(args['name'])

        ws.expressions[e._name] = e

        return {
            'name': e._name,
            'expression': str(e)
            }, 201


class Constraints(Resource):

    @verify_auth_token
    def get(self, model_name=None, ws=None):
        """
        Returns a list of constraints
        """

        if model_name is None:
            return {'constraints':
                        {i: str(ws.constraints[i]) for i in ws.constraints}}, 200
        else:
            if model_name in ws.models:
                m = ws.models[model_name]
                return {'constraints': [i._name for i in m.get_constraints()]}, 200
            else:
                return {
                    'message': 'Model name is not found'}, 404

    @verify_auth_token
    def post(self, model_name=None, ws=None):
        """
        Creates a new constraint

        Parameters
        ----------
        model_name : string, optional
            Name of the model
        """

        if model_name in ws.models:
            m = ws.models[model_name]
        else:
            return {
                'message': 'Model name is not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('expression', type=str, help='Constraint')
        parser.add_argument('name', type=str, help='Name of the constraint')
        args = parser.parse_args()

        combined = ws.get_combined()

        ws.so.utils.transfer_allowed = True
        ws.so.utils._load_transfer(combined)

        e = eval(args['expression'], None, combined)
        c = m.add_constraint(e, name=args.get('name', None))

        ws.so.utils.transfer_allowed = False
        ws.so.utils._clear_transfer()

        ws.constraints[args['name']] = c

        return {
            'name': c._name,
            'model': model_name,
            'expression': str(c)
        }, 201


class ConstraintGroups(Resource):

    @verify_auth_token
    def get(self, model_name=None, ws=None):
        if model_name is None:
            return {'constraintgroups':
                        {i: {j._name: str(j) for j in ws.constraint_groups[i]} for i in ws.constraint_groups}}, 200
        else:
            if model_name in ws.models:
                m = ws.models[model_name]
                return {'constraintgroups': {i._name: {j._name: str(j) for j in i} for i in m._congroups}}, 200
            else:
                return {
                           'message': 'Model name is not found'}, 404

    @verify_auth_token
    def post(self, model_name=None, ws=None):
        """
        Creates a new constraint group

        Parameters
        ----------
        model_name : string, optional
            Name of the model
        """

        if model_name in ws.models:
            m = ws.models[model_name]
        else:
            return {
                'message': 'Model name is not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('expression', type=str, help='Constraint expression')
        parser.add_argument('index', type=str, help='Index of the group')
        parser.add_argument('name', type=str, help='Name of the constraint group')
        args = parser.parse_args()

        combined = ws.get_combined()

        ws.so.utils.transfer_allowed = True
        ws.so.utils._load_transfer(combined)

        c = eval('so.ConstraintGroup(({} {}), name=\'{}\')'.format(args['expression'], args['index'], args['name']),
                 None, combined)
        cg = m.add_constraints(None, cg = c, name=args.get('name', None))

        ws.so.utils.transfer_allowed = False
        ws.so.utils._clear_transfer()

        ws.constraint_groups[args['name']] = cg

        return {
            'name': cg._name,
            'model': model_name
        }, 201


class Solutions(Resource):

    @verify_auth_token
    def get(self, model_name, ws):

        if model_name not in ws.models:
            return {
                'message': 'Model name is not found'}, 404
        else:
            m = ws.models[model_name]

        varvalues = {i._name: m.get_variable_value(name=i._name)
                     for i in m.get_variables()}

        return {'model': m._name,
                'solutions': varvalues}, 200

    @verify_auth_token
    def post(self, model_name, ws):

        if model_name not in ws.models:
            return {
                'message': 'Model name is not found'}, 404
        else:
            m = ws.models[model_name]

        parser = reqparse.RequestParser()
        parser.add_argument('stream', type=str, help='Stream option', default='False')
        args = parser.parse_args()

        if args['stream'] == 'True':

            @stream_with_context
            def solve(model):
                sys.stdout = stdout = Streamer(sys.stdout)
                proc = threading.Thread(target=model.solve)
                proc.start()
                while proc.isAlive():
                    for i in iter(stdout.read()):
                        yield i
                    time.sleep(0.05)
 
                proc.join()
                # Clean all output
                for i in iter(stdout.read()):
                    yield i
                sys.stdout = stdout.close()
                yield '\n'

            return Response(stream_with_context(solve(m)))
        else:
            # TODO Get solver options
            sys.stdout = stdout = Streamer(sys.stdout)
            res = m.solve()
            stream = ''.join(stdout.buffer)
            sys.stdout = stdout.close()
            if res is None:
                return {'model': m._name,
                        'message': 'Session is not defined'}, 400

            varvalues = {i._name: m.get_variable_value(name=i._name)
                         for i in m.get_variables()}

            return {'model': m._name,
                    'objective': m.get_objective_value(),
                    'solutions': varvalues,
                    'stream': stream}, 200


class Streamer:
    """
    A custom standard out for streaming processes like :meth:`Model.solve`.

    Parameters
    ----------
    stdout : Object, optional
        Original sys.stdout instance if simultaneous printing is needed
    """

    def __init__(self, stdout=None):
        self.stdout = stdout
        self.buffer = list()

    def write(self, text):
        """
        Appends the text into buffer and writes to sys.stdout if exists
        """
        if self.stdout is not None:
            self.stdout.write(text)
        self.buffer.append(text)
        if len(self.buffer) > 5:
            self.flush()

    def read(self):
        """
        Yields the first element in the buffer
        """
        while len(self.buffer) > 0:
            yield self.buffer.pop(0)
        return

    def flush(self):
        if self.stdout is not None:
            self.stdout.flush()

    def close(self):
        """
        Cleans the buffer and returns the original stdout object if exists
        """
        self.buffer = list()
        return self.stdout


# Create API as an object
api = UserApi()
