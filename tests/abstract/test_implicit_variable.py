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
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc


class TestImplicitVariable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        so.reset()
        from swat import CAS, SWATError
        try:
            cls.conn = CAS(os.environ.get('CASHOST'),
                           int(os.environ.get('CASPORT')),
                           authinfo=os.environ.get('AUTHINFO'))
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)

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
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 {o2 in S} = o2;
            impvar y_1 {o5 in S} = o5 + 1;
            impvar y_2 {o8 in S} = o8 + 2;
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
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y {{o{id1} in S, o{id2} in S}} = o{id1} + o{id2};
            """.format(id1=id+1, id2=id+4)))

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
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0_0 {{o{a} in S}} = o{a};
            impvar y_0_1 {{o{b} in S}} = o{b} + 1;
            impvar y_0_2 {{o{c} in S}} = o{c} + 2;
            impvar y_1_0 {{o{d} in S}} = o{d} + 1;
            impvar y_1_1 {{o{e} in S}} = o{e} + 2;
            impvar y_1_2 {{o{f} in S}} = o{f} + 3;
            """.format(a=id+2, b=id+5, c=id+8, d=id+11, e=id+14, f=id+17)))

        # Triple NSN
        so.reset()
        y = so.ImplicitVar((i + j + k for i in range(2) for j in S for k in range(3)), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0_0 {o2 in S} = o2;
            impvar y_0_1 {o2 in S} = o2 + 1;
            impvar y_0_2 {o2 in S} = o2 + 2;
            impvar y_1_0 {o7 in S} = o7 + 1;
            impvar y_1_1 {o7 in S} = o7 + 2;
            impvar y_1_2 {o7 in S} = o7 + 3;
            """))

        # Triple NSS
        so.reset()
        y = so.ImplicitVar((i + j + k for i in range(2) for j in S for k in S), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 {o2 in S, o4 in S} = o2 + o4;
            impvar y_1 {o7 in S, o9 in S} = o7 + o9 + 1;
            """))

        # Triple SNN
        so.reset()
        y = so.ImplicitVar((i + j + k for i in S for j in range(3) for k in range(3)), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
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
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 {o1 in S, o4 in S} = o1 + o4;
            impvar y_1 {o1 in S, o7 in S} = o1 + o7 + 1;
            impvar y_2 {o1 in S, o10 in S} = o1 + o10 + 2;
            """))

        # Triple SSN
        so.reset()
        y = so.ImplicitVar((i + j + k for i in S for j in S for k in range(2)), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y_0 {o1 in S, o4 in S} = o1 + o4;
            impvar y_1 {o1 in S, o4 in S} = o1 + o4 + 1;
            """))

        # Triple SSS
        so.reset()
        y = so.ImplicitVar((i + j + k + 2 for i in S for j in S for k in S), name='y')
        self.assertEqual(so.to_definition(y), cleandoc("""
            impvar y {o1 in S, o4 in S, o6 in S} = o1 + o4 + o6 + 2;
            """))


    def tearDown(self):
        pass
