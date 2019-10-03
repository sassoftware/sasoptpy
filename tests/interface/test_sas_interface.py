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

import unittest
import os
import sasoptpy as so
import saspy


current_dir = os.path.dirname(os.path.abspath(__file__))


class TestSASInterface(unittest.TestCase):

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
            so.quick_sum(i * x[i] for i in range(vs)) <= 1, name='c')
        o = m.set_objective(
            so.quick_sum(x[i] for i in range(vs)), sense=so.MAX, name='obj')

        def raise_runtime():
            m.solve()

        self.assertRaises(RuntimeError, raise_runtime)

        m.solve(limit_names=True)
        print(m.get_solution())
        self.assertEqual(x[0].get_value(), 2)

        m.set_objective(x[0], sense=so.MIN, name='obj2')
        m.solve(limit_names=True, submit=False)
        self.assertEqual(x[0].get_value(), 2)

    def test_long_lines(self):
        if TestSASInterface.conn is None:
            self.skipTest('SAS session is not available')

        vs = 1000
        m = so.Model(name='test_long_line', session=TestSASInterface.conn)
        x = m.add_variables(vs, name='averylongvariablename', ub=2, lb=0)
        c = m.add_constraint(
            so.quick_sum(i * x[i] for i in range(vs)) <= 1, name='c')
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
