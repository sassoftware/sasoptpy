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
import unittest
import os
import sasoptpy as so
import saspy


current_dir = os.path.dirname(os.path.abspath(__file__))


class TestSASInterface(unittest.TestCase):
    """
    Unit tests for the SAS interface
    """

    @classmethod
    def setUpClass(cls):
        cls.conn = None
        try:
            cls.conn = None
            if os.name == 'nt':
                cls.conn = saspy.SASsession(cfgname='winlocal')
            else:
                cfg_file = os.path.join(
                    current_dir, '../examples/saspy_config.py')
                cls.conn = saspy.SASsession(cfgfile=cfg_file)
            print('Connected to SAS')
        except TypeError:
            raise unittest.SkipTest('Environment variable may not be defined')

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            cls.conn.endsas()
            cls.conn = None

    def setUp(self):
        so.reset()

    def test_long_names(self):
        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        vs = 10
        m = so.Model(name='test_long_name', session=TestSASInterface.conn)
        x = m.add_variables(
            vs, name='averylongvariablenamethatdoesnotwork', ub=2, lb=0)
        c = m.add_constraint(
            so.expr_sum(i * x[i] for i in range(vs)) <= 1, name='c')
        o = m.set_objective(
            so.expr_sum(x[i] for i in range(vs)), sense=so.MAX, name='obj')

        def raise_runtime():
            m.solve()

        self.assertRaises(RuntimeError, raise_runtime)

        m.solve(limit_names=True)
        m.get_solution()
        self.assertEqual(x[0].get_value(), 2)

        m.set_objective(x[0], sense=so.MIN, name='obj2')
        m.solve(limit_names=True, submit=False)
        self.assertEqual(x[0].get_value(), 2)

    def test_long_lines(self):
        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        vs = 2000
        m = so.Model(name='test_long_line', session=TestSASInterface.conn)
        x = m.add_variables(vs, name='averylongvariablename', ub=2, lb=0)
        c = m.add_constraint(
            so.expr_sum(i * x[i] for i in range(vs)) <= 1, name='c')
        o = m.set_objective(x[0], sense=so.MAX, name='obj')

        m.solve(wrap_lines=True)

        self.assertEqual(x[0].get_value(), 2)

    def test_mps_on_sas(self):
        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        m = so.Model(name='test_mps_on_sas', session=TestSASInterface.conn)
        x = m.add_variables(10, name='x', lb=0)
        m.add_constraints((x[i] >= i for i in range(10)), name='c')
        m.set_objective(
            so.expr_sum(x[i] for i in range(10)), sense=so.MIN, name='obj')

        m.solve(mps=True, verbose=True)
        self.assertEqual(x[2].get_value(), 2)

    def test_workspace_post_value(self):

        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        with so.Workspace('test_ws_var_value',
                          session=TestSASInterface.conn) as w:
            x = so.Variable(name='x')
            c = so.Constraint(x <= 5, name='c')
            o = so.Objective(x, sense=so.MAX, name='obj')
            so.actions.solve()
        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               con c : x <= 5;
               max obj = x;
               solve;
            quit;'''))
        w.submit()
        self.assertEqual(x.get_value(), 5)

    def test_forced_optmodel(self):
        if not TestSASInterface.conn:
            self.skipTest('No session is available')

        # Forced to OPTMODEL due abstract elements
        m = so.Model(name='test_forced_optmodel', session=TestSASInterface.conn)
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

    def test_postprocess_optmodel_string(self):

        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        with so.Workspace('w', session=TestSASInterface.conn) as w:
            x = so.Variable(name='x')
            o = so.Objective((x-1)**2, sense=so.MIN, name='obj')
            so.actions.solve()
        w.submit(limit_names=True, wrap_lines=True)
        self.assertEqual(x.get_value(), 1)

    def test_optmodel_error(self):

        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        with so.Workspace('w', session=TestSASInterface.conn) as w:
            so.abstract.LiteralStatement('abc')
        def produce_error():
            w.submit(verbose=True)
        self.assertRaises(RuntimeError, produce_error)
