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

from swat import CAS
import sys
from flask import Response, stream_with_context, Flask
from flask.json import jsonify
from flask_restful import Resource, Api, reqparse
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as TimedSerializer, Signer,
                          BadSignature, SignatureExpired)
import secrets
import threading
import time

app = Flask('sasoptpy')
api = Api(app)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
print('App SECRET KEY', app.config['SECRET_KEY'])

workspaces = {}


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
            s = TimedSerializer(app.config['SECRET_KEY'])
            try:
                data = s.loads(splittoken[1])
            except SignatureExpired:
                return {'message': 'Error: Token is expired.'}, 400
            except BadSignature:
                return {'message': 'Error: Bad Signature. Token is not verified.'}, 400
            name = data['name']
            if name in workspaces:
                ws = workspaces[name]
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
    s = TimedSerializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'name': name})


class Workspace:

    def __init__(self, name, password):
        import sasoptpy as so
        self.so = so
        self.name = name
        self.sessions = {}
        self.models = {}
        self.variables = {}
        self.variable_groups = {}
        self.constraints = {}
        self.constraint_groups = {}
        self.expressions = {}
        self.parameters = {}
        self.sets = {}
        self.tables = {}
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

        s = Signer(app.config['SECRET_KEY'])
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

        s = Signer(app.config['SECRET_KEY'])
        current_secret = s.sign('{} {}'.format(name, password).encode('utf-8'))

        return current_secret == self._secret


class Workspaces(Resource):
    """
    Creates a workspace for a user, using a token-based authentication.
    """

    def post(self, workspace=None):
        """
        Creates a workspace using a workspace name and returns a token.
        """
        parser = reqparse.RequestParser()
        if workspace is None:
            parser.add_argument('name', type=str, help='Workspace name', required=True)
        else:
            if workspace not in workspace:
                return {'message': 'Workspace does not exist, cannot renew token.'}, 400
        parser.add_argument('password', type=str, help='Password for workspace', required=True)
        args = parser.parse_args()
        if workspace is None:
            if args['name'] in workspaces:
                return {'message': 'A workspace with the same name exists.'}, 422
            name = args['name']
        else:
            name = workspace
        workspaces[name] = Workspace(name, args['password'])
        token = generate_auth_token(name, 600)
        return {'token': token.decode('ascii'), 'duration': 600}, 200

    def get(self, workspace=None):
        """
        Shows a list of available workspace names.
        """
        if workspace is None:
            return {'workspaces': list(workspaces.keys())}, 200
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
                                                protocol='http',
                                                authinfo=args['auth'])
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
        ws : :class:`Workspace` object
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

        m = ws.so.Model(name=args['name'],
                        session=ws.sessions[args['session']])
        ws.models[m._name] = m
        m._session_name = args['session']

        return {
            'name': m._name,
            'workspace': ws.name,
            'session': args['session']
            }, 201


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
                           vartype=args['vartype'])
        ws.variables[v._name] = v

        return {
            'name': v._name}, 201


class Expressions(Resource):

    @verify_auth_token
    def get(self, ws):
        """
        Returns a list of expressions
        """
        return {'expressions':
                {i: str(ws.expressions[i]) for i in ws.expressions}}, 200

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

        combined = {**ws.variables, **ws.variable_groups}
        exec(args['name'] + ' = ' + args['expression'], globals(), combined)

        e = combined[args['name']]

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
    def get(self, ws):
        """
        Returns a list of constraints
        """

        return {'constraints':
                {i: str(ws.constraints[i]) for i in ws.constraints}}, 200

    @verify_auth_token
    def post(self, model_name=None, ws=None):
        """
        Creates a new constraint

        Parameters
        ----------
        model_name : string, optional
            Name of the model
        """

        if model_name is not None and model_name not in ws.models:
            return {
                'message': 'Model name is not found'}, 404
        elif model_name is not None:
            m = ws.models[model_name]
        else:
            m = None

        parser = reqparse.RequestParser()
        parser.add_argument('expression', type=str, help='Constraint')
        parser.add_argument('name', type=str, help='Name of the constraint')
        args = parser.parse_args()

        combined = {**ws.variables, **ws.variable_groups, 'ws': ws, 'so': ws.so}

        exec(
            '{} = so.Constraint({}, name=\'{}\')'.format(
                args['name'], args['expression'], args['name']),
            globals(), combined)
        c = combined[args['name']]

        if m is None:
            return {
                'name': c._name,
                'expression': str(c)
            }, 201
        else:
            m = ws.models[model_name]
            m.include(c)
            return {
                'name': c._name,
                'model': model_name,
                'expression': str(c)
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
        parser.add_argument('stream', type=str, help='Stream option')
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
            # Get options, later!
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


api.add_resource(Entry, '/')
api.add_resource(Workspaces, '/workspaces', '/workspaces/<string:workspace>')
api.add_resource(Sessions, '/sessions')
api.add_resource(Models, '/models', '/models/<string:model_name>')
api.add_resource(
    Variables, '/variables', '/models/<string:model_name>/variables')
api.add_resource(
    Expressions, '/expressions', '/models/<string:model_name>/objectives')
api.add_resource(
    Constraints, '/constraints', '/models/<string:model_name>/constraints')
api.add_resource(
    Solutions, '/models/<string:model_name>/solutions')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
