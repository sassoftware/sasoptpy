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


class TestCASInterface(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
        try:
            cls.conn = CAS(os.environ.get('CASHOST'),
                           int(os.environ.get('CASPORT')),
                           authinfo=os.environ.get('AUTHINFO'))
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)

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
        m.solve(mps=True, verbose=True)

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
            print(s, type(s))
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
