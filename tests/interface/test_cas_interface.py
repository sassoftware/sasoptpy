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

from inspect import cleandoc
import os
import unittest
import warnings

from swat import CAS, SWATError

import sasoptpy as so

from tests.swat_config import create_cas_connection


class Arbitrary:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockCASResponse:

    def __init__(self, **kwargs):
        self.status = kwargs.get('status', 'OK')
        self.solutionStatus = kwargs.get('solutionStatus', 'OPTIMAL')

    def get_tables(self, *args):
        return [self.status]

    def keys(self):
        return list()


class MockCASServer:
    """
    Represents CAS Server for unit tests.
    """

    def __init__(self, **kwargs):
        so.util.get_session_type = self.get_session_type
        so.util.package_utils.get_session_type = self.get_session_type
        self.response = kwargs.get('response', MockCASResponse())
        self.optimization = Arbitrary()

    def get_session_type(self, *args, **kwargs):
        return 'CAS'

    def loadactionset(self, *args, **kwargs):
        pass

    def upload_frame(self, *args, **kwargs):
        return Arbitrary(name='name')

    def runOptmodel(self, *args, **kwargs):
        return self.response

    def solveLp(self, *args, **kwargs):
        return self.response

    def solveMilp(self, *args, **kwargs):
        return self.response


class TestCASInterface(unittest.TestCase):
    """
    Unit tests for the CAS interface
    """

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
        try:
            cls.conn = create_cas_connection()
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            cls.conn.close()

    def setUp(self):
        self.original_get_type = so.util.get_session_type
        self.original_package_get_type = so.util.package_utils.get_session_type

    def tearDown(self):
        so.util.get_session_type = self.original_get_type
        so.util.package_utils.get_session_type = self.original_package_get_type

    def test_unbounded(self):
        if not TestCASInterface.conn:
            self.skipTest('No session is available')

        m = so.Model(name='m', session=TestCASInterface.conn)
        x = m.add_variable(name='x', lb=0)
        m.set_objective(x, sense=so.MAX, name='obj')
        def warn_user():
            m.solve(frame=True, name='unbounded_test')
        self.assertWarns(UserWarning, warn_user)


    def test_forced_optmodel(self):
        if not TestCASInterface.conn:
            self.skipTest('No session is available')

        # Forced to OPTMODEL due abstract elements
        m = so.Model(name='test_forced_optmodel', session=TestCASInterface.conn)
        S = so.Set(name='S')
        m.include(S)
        x = m.add_variable(name='x', ub=1)
        m.set_objective(2*x, sense=so.MAX, name='obj')
        def warn_abstract():
            response = m.solve(mps=True, submit=False)
            self.assertIn('set S;', response)
        self.assertWarns(UserWarning, warn_abstract)

        # Uploaded MPS Table
        m.drop(S)
        response = m.solve(mps=True, submit=False)
        self.assertIn('CASTable', str(response))

        # Forced to OPTMODEL due nonlinearity
        m.set_objective(x**2, sense=so.MAX, name='obj2')
        def warn_nonlinear():
            response = m.solve(mps=True, submit=False)
            self.assertIn('var x', response)
        self.assertWarns(UserWarning, warn_nonlinear)

        # Forced to give error
        def force_decomp():
            m.solve(mps=True, options={'decomp': 'USER'})
        self.assertRaises(RuntimeError, force_decomp)

        # No objective
        m.solve(mps=True, verbose=True, name='no_obj')

    def test_regular_lp(self):
        if not TestCASInterface.conn:
            self.skipTest('No session is available')
        m = so.Model(name='test_regular_lp', session=TestCASInterface.conn)
        x = m.add_variable(name='x', lb=1)
        c = m.add_constraint(x <= 3, name='c')
        m.set_objective(x, sense=so.MIN, name='obj')
        m.solve(name='simple_lp')
        self.assertEqual(m.get_solution_summary().loc['Solver', 'Value'], 'LP')
        self.assertEqual(x.get_value(), 1)

    def test_primalin(self):
        if TestCASInterface.conn is None:
            self.skipTest('No session is available.')
        session = TestCASInterface.conn

        from sasoptpy import integer, minimize

        m = so.Model(name='test_primalin_mps', session=session)
        x = m.add_variable(name='x', vartype=integer, ub=9.5, lb=0)
        y = m.add_variable(name='y', vartype=integer, ub=5, lb=2)
        m.add_constraint(x + 2 * y >= 1, name='c1')
        m.add_constraint(x - 2 * y >= 2, name='c2')
        o = m.set_objective(x + y, sense=minimize, name='obj')
        m.solve(mps=True)

        self.assertEqual(so.get_value_table(x, y).to_string(), cleandoc('''
                 x    y
            -  6.0  2.0
            '''))

        m.set_objective(x + 1.1 * y, sense=minimize, name='obj2')
        m.solve(mps=True, primalin=True)
        self.assertEqual(
            session.CASTable('PRIMALINTABLE').to_frame().to_string(), cleandoc(
                '''
                  _VAR_  _VALUE_
                0     x      6.0
                1     y      2.0
                '''
            ))

        # Drop option
        m.solve(mps=True, primalin=True, drop=True)
        def deleted_table():
            s = session.CASTable('PRIMALINTABLE').to_frame()
        self.assertRaises(SWATError, deleted_table)

    def test_response(self):
        if TestCASInterface.conn is None:
            self.skipTest('No session is available.')
        from sasoptpy import maximize, integer
        m = so.Model(name='test_response', session=TestCASInterface.conn)
        x = so.Variable(name='x', lb=1)
        o = so.Objective(x ** 2, sense=maximize, name='obj')
        m.include(x, o)
        m.solve(verbose=True)
        self.assertEqual(str(m.response.solutionStatus), 'UNBOUNDED')
        self.assertEqual(m._objval, None)

    def test_lp(self):
        if TestCASInterface.conn is None:
            self.skipTest('No session is available.')

        m = so.Model(name='model_lp', session=TestCASInterface.conn)
        x = m.add_variable(name='x', lb=1, ub=4)
        y = m.add_variable(name='y', lb=4, ub=10)
        m.add_constraint(x + y == 8, name='c1')
        m.set_objective(x-y, sense=so.MIN, name='obj')
        m.solve(mps=True, verbose=True)
        self.assertEqual(x.get_value(), 1)

    def test_workspace(self):
        if not TestCASInterface.conn:
            self.skipTest('No session is available')

        with so.Workspace('w', session=TestCASInterface.conn) as w:
            x = so.VariableGroup(3, name='x')
            c = so.ConstraintGroup((x[i] <= i for i in range(3)), name='c')
            o = so.Objective(x[1], name='obj', sense=so.MAX)
            s = so.actions.solve()

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x {{0,1,2}};
               con c_0 : x[0] <= 0;
               con c_1 : x[1] <= 1;
               con c_2 : x[2] <= 2;
               max obj = x[1];
               solve;
            quit;'''))
        r = w.submit()
        self.assertIsNotNone(s.get_solution_summary())
        self.assertIsNotNone(s.get_problem_summary())

        self.assertEqual(s.get_solution_summary().loc['Solver', 'Value'], 'LP')

        self.assertEqual(r.to_string(), cleandoc('''
             i   var  value             lb             ub   rc
        0  1.0  x[0]    0.0 -1.797693e+308  1.797693e+308  0.0
        1  2.0  x[1]    1.0 -1.797693e+308  1.797693e+308  0.0
        2  3.0  x[2]    2.0 -1.797693e+308  1.797693e+308  0.0'''))

        self.assertEqual(x[1].get_value(), 1)

    def test_workspace_errors(self):

        mockResponse = MockCASResponse(status='Syntax Error')
        mockSession = MockCASServer(response=mockResponse)

        with so.Workspace('w', session=mockSession) as w:
            x = so.Variable(name='x')

        def produce_syntax_error():
            r = w.submit()
        self.assertRaises(SyntaxError, produce_syntax_error)

        mockResponse = MockCASResponse(status='Semantic Error')
        mockSession = MockCASServer(response=mockResponse)
        mockSession.optimization = Arbitrary(runoptmodel=True)
        m = so.Model(name='test_runtime', session=mockSession)
        m.add_variable(name='x')
        def produce_runtime_error():
            m.solve()
        self.assertRaises(RuntimeError, produce_runtime_error)

        with so.Workspace('w', session=mockSession) as w:
            x = so.Variable(name='x')
        def produce_runtime_error_for_ws():
            r = w.submit()
        self.assertRaises(RuntimeError, produce_runtime_error_for_ws)

    def test_errors_and_warnings(self):

        s = MockCASServer()
        m = so.Model(name='test_errors_for_cas', session=s)
        x = m.add_variable(name='x', lb=0)
        m.set_objective(x ** 2, name='obj', sense=so.MIN)

        def produce_runtime_error():
            m.solve(frame=False)
        self.assertRaises(RuntimeError, produce_runtime_error)

        m.set_objective(x, name='obj', sense=so.MIN)

        s = MockCASServer(response=MockCASResponse(status=['ERROR']))
        m.set_session(s)
        def produce_error_status():
            m.solve(frame=True)
        self.assertRaises(RuntimeError, produce_error_status)

    def test_tuner(self):

        import pandas as pd

        if TestCASInterface.conn is None:
            self.skipTest('No session is available')

        m = so.Model(name='knapsack_with_tuner', session=TestCASInterface.conn)
        data = [
            ['clock', 8, 4, 3],
            ['mug', 10, 6, 5],
            ['headphone', 15, 7, 2],
            ['book', 20, 12, 10],
            ['pen', 1, 1, 15]
        ]
        df = pd.DataFrame(data, columns=['item', 'value', 'weight',
                                         'limit']).set_index(['item'])
        ITEMS = df.index
        value = df['value']
        weight = df['weight']
        limit = df['limit']
        total_weight = 55
        # Variables
        get = m.add_variables(ITEMS, name='get', vartype=so.INT)
        # Constraints
        m.add_constraints((get[i] <= limit[i] for i in ITEMS), name='limit_con')
        m.add_constraint(
            so.expr_sum(weight[i] * get[i] for i in ITEMS) <= total_weight,
            name='weight_con')
        # Objective
        total_value = so.expr_sum(value[i] * get[i] for i in ITEMS)
        m.set_objective(total_value, name='total_value', sense=so.MAX)

        results = m.tune_parameters(tunerParameters={'maxConfigs': 10})

        self.assertEqual(len(results), 10)

        self.assertTrue('Configuration' in results.iloc[0].index)
