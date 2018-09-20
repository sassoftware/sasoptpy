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

'''
API includes implementation of RESTful API for connecting other applications
'''

from swat import CAS
import sys
from flask import Response, stream_with_context, Flask
from flask.json import jsonify
from flask_restful import Resource, Api, reqparse
import threading
import sasoptpy as so
import time

app = Flask('sasoptpy')
api = Api(app)

sessions = {}
models = {}
variables = {}
variable_groups = {}
constraints = {}
constraint_groups = {}
expressions = {}
parameters = {}
sets = {}
tables = {}
dictlist = [sessions, models, variables, variable_groups, constraints,
            constraint_groups, expressions, parameters, sets, tables]


class Entry(Resource):
    '''
    Entry point for the API listing information about package.
    '''

    def get(self):
        '''
        Get current sasoptpy version
        '''
        return {
            'package': 'sasoptpy',
            'version': so.__version__}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, help='Task for server')
        args = parser.parse_args()

        if args['action'] == 'clean':
            so.reset_globals()
            for i in dictlist:
                i.clear()
            return {'message': 'Cleaned the namespace'}, 200


class Sessions(Resource):
    '''
    Session objects for Viya connections
    '''

    def get(self):
        '''
        Returns a list of sessions
        '''
        return {'sessions': [i for i in sessions]}, 200

    def post(self):
        '''
        Creates a new CAS connection
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the session')
        parser.add_argument(
            'host', type=str, required=True, help='Address of the CAS server')
        parser.add_argument(
            'port', type=int, required=True, help='Port number')
        parser.add_argument('auth', type=str, help='Authentication info file')
        args = parser.parse_args()

        if all(args.values()) is False:
            return {'status': 400, 'message': 'Some arguments are missing'}, 400

        try:
            s = sessions[args['name']] = CAS(args['host'],
                                             args['port'],
                                             protocol='http',
                                             authinfo=args['auth'])
        except:
            sessions[args['name']] = None
            return {
                'status': 400, 'message': 'Cannot create CAS session'}, 400

        return {
            'id': list(s.sessionid().values())[0],
            'name': args['name']}, 201


class Models(Resource):
    '''
    Model objects
    '''

    def get(self, model_name=None):
        '''
        Returns a single model or a list of models

        Parameters
        ----------
        model_name : string, optional
            Name of a specific model requested
        '''
        if model_name is None:
            return {'models': {i: models[i]._name for i in models}}, 200
        else:
            return self.getmodel(model_name)

    def getmodel(self, model_name):
        '''
        Get info about a specific model name
        '''

        parser = reqparse.RequestParser()
        parser.add_argument('format', type=str, help='Output format')
        args = parser.parse_args()

        if model_name in models:
            if args['format'] is None or args['format'] == 'summary':
                return {
                    'name': model_name,
                    'session': models[model_name]._session_name}, 200
            elif args['format'] == 'optmodel':
                return {
                    'name': model_name,
                    'optmodel': models[model_name].to_optmodel()}, 200
        else:
            return {
                'message': 'Model name is not found'}, 404

    def post(self):
        '''
        Creates a new model
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the model')
        parser.add_argument('session', type=str, help='Session ID')
        args = parser.parse_args()

        if all(args.values()) is False:
            return jsonify({'status': 400,
                            'message': 'Some arguments are missing'})

        m = so.Model(name=args['name'], session=sessions[args['session']])
        models[m._name] = m
        m._session_name = args['session']

        return {
            'name': m._name,
            'session': args['session']
            }, 201


class Variables(Resource):
    '''
    Represents variables inside models
    '''

    def get(self, model_name=None):
        if model_name is None:
            return {'variables':
                    {i: variables[i]._name for i in variables}}, 200
        else:
            if model_name in models:
                m = models[model_name]
                return {'variables': [i._name for i in m.get_variables()]}, 200
            else:
                return {
                    'message': 'Model name is not found'}, 404

    def post(self, model_name=None):
        '''
        Add new variables to model
        '''

        if model_name in models:
            m = models[model_name]
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
        variables[v._name] = v

        return {
            'name': v._name}, 201


class Expressions(Resource):

    def get(self):
        '''
        Returns a list of expressions
        '''
        return {'expressions':
                {i: str(expressions[i]) for i in expressions}}, 200

    def post(self, model_name=None):
        '''
        Creates a new expression
        '''
        if model_name is not None and model_name not in models:
            return {
                'message': 'Model name is not found'}, 404
        elif model_name is not None:
            m = models[model_name]
        else:
            m = None

        parser = reqparse.RequestParser()
        parser.add_argument('expression', type=str, help='Expression')
        parser.add_argument('sense', type=str, help='Sense if an objective')
        parser.add_argument('name', type=str, help='Name of the expression')
        args = parser.parse_args()

        combined = {**variables, **variable_groups}
        exec(args['name'] + ' = ' + args['expression'], globals(), combined)

        e = combined[args['name']]

        if m is not None:
            e = m.set_objective(e, sense=args['sense'], name=args['name'])
        else:
            e.set_name(args['name'])

        expressions[e._name] = e

        return {
            'name': e._name,
            'expression': str(e)
            }, 201


class Constraints(Resource):

    def get(self):
        '''
        Returns a list of constraints
        '''

        return {'constraints':
                {i: str(constraints[i]) for i in constraints}}, 200

    def post(self, model_name=None):
        '''
        Creates a new constraint

        Parameters
        ----------
        model_name : string, optional
            Name of the model
        '''

        if model_name is not None and model_name not in models:
            return {
                'message': 'Model name is not found'}, 404
        elif model_name is not None:
            m = models[model_name]
        else:
            m = None

        parser = reqparse.RequestParser()
        parser.add_argument('expression', type=str, help='Constraint')
        parser.add_argument('name', type=str, help='Name of the constraint')
        args = parser.parse_args()

        combined = {**variables, **variable_groups}

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
            m = models[model_name]
            m.include(c)
            return {
                'name': c._name,
                'model': model_name,
                'expression': str(c)
            }, 201


class Solutions(Resource):

    def get(self, model_name):

        if model_name not in models:
            return {
                'message': 'Model name is not found'}, 404
        else:
            m = models[model_name]

        varvalues = {i._name: m.get_variable_value(name=i._name)
                     for i in m.get_variables()}

        return {'model': m._name,
                'solutions': varvalues}, 200

    def post(self, model_name):

        if model_name not in models:
            return {
                'message': 'Model name is not found'}, 404
        else:
            m = models[model_name]

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
    '''
    A custom standard out for streaming processes like :meth:`Model.solve`.

    Parameters
    ----------
    stdout : Object, optional
        Original sys.stdout instance if simultaneous printing is needed
    '''

    def __init__(self, stdout=None):
        self.stdout = stdout
        self.buffer = list()

    def write(self, text):
        '''
        Appends the text into buffer and writes to sys.stdout if exists
        '''
        if self.stdout is not None:
            self.stdout.write(text)
        self.buffer.append(text)
        if len(self.buffer) > 5:
            self.flush()

    def read(self):
        '''
        Yields the first element in the buffer
        '''
        while len(self.buffer) > 0:
            yield self.buffer.pop(0)
        return

    def flush(self):
        if self.stdout is not None:
            self.stdout.flush()

    def close(self):
        '''
        Cleans the buffer and returns the original stdout object if exists
        '''
        self.buffer = list()
        return self.stdout


api.add_resource(Entry, '/')
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
