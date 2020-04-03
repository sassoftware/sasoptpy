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
Unit tests for implicit variables.
"""

import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
from util import assert_equal_wo_temps

from tests.swat_config import create_cas_connection



class TestImplicitVariable(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.abstract.ImplicitVar` objects
    """

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
        from swat import CAS, SWATError
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
        pass

    def test_impvar_defn(self):
        x = so.ImplicitVar(0, name='x')
        self.assertEqual(str(x), 'x')
        self.assertEqual(x.get_name(), 'x')
        self.assertEqual(so.to_definition(x), 'impvar x = 0;')

    def test_impvar_setitem(self):
        # Regular assignment
        x = so.Variable(name='x')
        y = so.ImplicitVar((i * x for i in range(3)), name='y')
        self.assertEqual(so.to_expression(y[2]), "2 * x")
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 = 0;
            impvar y_1 = x;
            impvar y_2 = 2 * x;
            """))

        p = so.Parameter(name='p', value=4)
        z = so.ImplicitVar((i * p for i in so.exp_range(1, 5)), name='z')
        self.assertEqual(so.to_definition(z), cleandoc("""
            impvar z_1 = p;
            impvar z_2 = 2 * p;
            impvar z_3 = 3 * p;
            impvar z_4 = 4 * p;
            """))

        t = so.ImplicitVar(p, name='t')
        self.assertEqual(so.to_definition(t), 'impvar t = p;')

    def test_impvar_combinations(self):
        # Constant
        x = so.ImplicitVar(4, name='x')
        self.assertEqual(so.to_definition(x), 'impvar x = 4;')

        # Single N
        y = so.ImplicitVar((i ** 2 for i in range(3)), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 = 0;
            impvar y_1 = 1;
            impvar y_2 = 4;
            """))

        # Single S
        so.reset()
        S = so.Set(name='S')
        y = so.ImplicitVar((2 * i for i in S), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y {o2 in S} = 2.0 * o2;
            """))

        # Double NN
        y = so.ImplicitVar((i + j for i in range(3) for j in range(2)), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0_0 = 0;
            impvar y_0_1 = 1;
            impvar y_1_0 = 1;
            impvar y_1_1 = 2;
            impvar y_2_0 = 2;
            impvar y_2_1 = 3;
            """))

        # Double NS
        so.reset()
        y = so.ImplicitVar((i + j for i in range(3) for j in S), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0 {o1 in S} = o1;
            impvar y_1 {o2 in S} = o2 + 1;
            impvar y_2 {o3 in S} = o3 + 2;
            """))

        # Double SN
        so.reset()
        y = so.ImplicitVar((i + j for i in S for j in range(2)), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 {o1 in S} = o1;
            impvar y_1 {o1 in S} = o1 + 1;
            """))

        # Double SS
        id = so.itemid
        y = so.ImplicitVar((i + j for i in S for j in S), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y {o8 in S, o11 in S} = o8 + o11;
            """))

        # Triple NNN
        y = so.ImplicitVar((i + 2*j for i in range(1) for j in range(2) for k in ['A', 'B']), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0_0_A = 0;
            impvar y_0_0_B = 0;
            impvar y_0_1_A = 2;
            impvar y_0_1_B = 2;
            """))

        # Triple NNS
        so.reset()
        id = so.itemid
        y = so.ImplicitVar((i + j + k for i in range(2) for j in range(3) for k in S), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0_0 {o2 in S} = o2;
            impvar y_0_1 {o6 in S} = o6 + 1;
            impvar y_0_2 {o10 in S} = o10 + 2;
            impvar y_1_0 {o14 in S} = o14 + 1;
            impvar y_1_1 {o18 in S} = o18 + 2;
            impvar y_1_2 {o22 in S} = o22 + 3;
            """))

        # Triple NSN
        so.reset()
        y = so.ImplicitVar((i + j + k for i in range(2) for j in S for k in range(3)), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0_0 {o2 in S} = o2;
            impvar y_0_1 {o2 in S} = o2 + 1;
            impvar y_0_2 {o2 in S} = o2 + 2;
            impvar y_1_0 {o10 in S} = o10 + 1;
            impvar y_1_1 {o10 in S} = o10 + 2;
            impvar y_1_2 {o10 in S} = o10 + 3;
            """))

        # Triple NSS
        so.reset()
        y = so.ImplicitVar((i + j + k for i in range(2) for j in S for k in S), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0 {o2 in S, o4 in S} = o2 + o4;
            impvar y_1 {o8 in S, o10 in S} = o8 + o10 + 1;
            """))

        # Triple SNN
        so.reset()
        y = so.ImplicitVar((i + j + k for i in S for j in range(3) for k in range(3)), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0_0 {o1 in S} = o1;
            impvar y_0_1 {o1 in S} = o1 + 1;
            impvar y_0_2 {o1 in S} = o1 + 2;
            impvar y_1_0 {o1 in S} = o1 + 1;
            impvar y_1_1 {o1 in S} = o1 + 2;
            impvar y_1_2 {o1 in S} = o1 + 3;
            impvar y_2_0 {o1 in S} = o1 + 2;
            impvar y_2_1 {o1 in S} = o1 + 3;
            impvar y_2_2 {o1 in S} = o1 + 4;
            """))

        # Triple SNS
        so.reset()
        y = so.ImplicitVar((i + j + k for i in S for j in range(3) for k in S), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0 {o1 in S, o4 in S} = o1 + o4;
            impvar y_1 {o1 in S, o8 in S} = o1 + o8 + 1;
            impvar y_2 {o1 in S, o12 in S} = o1 + o12 + 2;
            """))

        # Triple SSN
        so.reset()
        y = so.ImplicitVar((i + j + k for i in S for j in S for k in range(2)), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y_0 {o1 in S, o4 in S} = o1 + o4;
            impvar y_1 {o1 in S, o4 in S} = o1 + o4 + 1;
            """))

        # Triple SSS
        so.reset()
        y = so.ImplicitVar((i + j + k + 2 for i in S for j in S for k in S), name='y')
        assert_equal_wo_temps(self, so.to_definition(y), cleandoc("""
            impvar y {o1 in S, o4 in S, o6 in S} = o1 + o4 + o6 + 2;
            """))

    def test_impvar_power(self):
        p = so.Parameter(name='p')
        y = so.ImplicitVar((i + p for i in range(2)), name='y')
        e = y[0] ** 2 + y[1] ** 2
        self.assertEqual(str(e), '(p) ** (2) + (p + 1) ** (2)')
        f = y[0] / p + y[1] / p
        self.assertEqual(str(f), '(p) / (p) + (p + 1) / (p)')

    def test_impvar_shadow(self):
        p = so.Parameter(name='p', value=5)
        x = so.ImplicitVar((p ** i for i in range(3)), name='x')
        S = so.Set(name='S')
        for i in S:
            a = x[i]
            assert_equal_wo_temps(self, str(x[i]), 'x[o13]')

    def test_impvar_keys(self):
        x = so.ImplicitVar(0, name='x')
        self.assertEqual(list(x.get_keys()), [('',)])

        y = so.ImplicitVar((i for i in range(3)), name='y')
        self.assertEqual(list(y.get_keys()), [(0,), (1,), (2,)])

        S = so.Set(name='S')
        z = so.ImplicitVar((2 * i for i in S), name='z')
        first_key = list(z.get_keys())[0][0]
        self.assertTrue(isinstance(first_key, so.SetIterator))

        for i in y:
            self.assertTrue(isinstance(y[i], so.Expression))

    def test_impvar_expr(self):
        x = so.VariableGroup(2, name='x')
        y = so.ImplicitVar((1 - x[i] for i in range(1)), name='y')
        self.assertEqual(so.to_definition(y),
                         'impvar y_0 = - x[0] + 1;')
        e = x[1] + 100 - y[0]
        self.assertEqual(so.to_expression(e),
                         'x[1] - (- x[0] + 1) + 100')

    def tearDown(self):
        pass
