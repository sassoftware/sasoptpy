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
from inspect import cleandoc

import sasoptpy as so


class TestPackageUtils(unittest.TestCase):

    def setUp(self):
        so.reset()

    def test_extract_arguments(self):
        x = so.VariableGroup(['a', 'b', 'c'], [1, 2, 3], name='x')
        def1 = so.to_definition(x)

        y = so.VariableGroup(('a', 'b', 'c'), (1, 2, 3), name='x')
        def2 = so.to_definition(y)

        self.assertEqual(def1, def2)

    def test_extract_list_value(self):
        m = so.Model(name='test_extract_list_vals')
        S = ['a', 'b', 'c']
        lb_values = {'a': 1, 'b': 0, 'c': 2}
        ub_values = {'a': 5, 'b': 10}
        init_values = {'b': 2, 'c': 3}
        x = m.add_variables(S, name='x', ub=ub_values, lb=lb_values,
                             init=init_values)
        self.assertEqual(so.to_optmodel(m), cleandoc('''
            proc optmodel;
               min test_extract_list_vals_obj = 0;
               var x {{'a','b','c'}};
               x['a'].lb = 1;
               x['a'].ub = 5;
               x['b'] = 2;
               x['b'].lb = 0;
               x['b'].ub = 10;
               x['c'] = 3;
               x['c'].lb = 2;
               solve;
            quit;
            '''))

        def produce_error():
            from collections import OrderedDict
            ind = ['a', 'b', 'c']
            y_lb = set([0, 1, 2])
            y = m.add_variables(ind, name='y', lb=y_lb)
        self.assertRaises(ValueError, produce_error)

    def test_deprecation(self):
        def call_tuple_unpack():
            so.util.tuple_unpack((1,2,))
        self.assertWarns(DeprecationWarning, call_tuple_unpack)
        def call_tuple_pack():
            so.util.tuple_pack(1)
        self.assertWarns(DeprecationWarning, call_tuple_pack)
        def call_list_pack():
            so.util.list_pack((1,2,3))
        self.assertWarns(DeprecationWarning, call_list_pack)
        def call_wrap():
            so.util.wrap(5)
        self.assertWarns(DeprecationWarning, call_wrap)

    def test_sum_wrap(self):
        x = so.Variable(name='x')
        e = so.expr_sum(x for _ in range(3))
        self.assertEqual(so.to_expression(e), '3 * x')

    def test_sum_wrap_abstract(self):
        I = so.Set(name='I')
        x = so.Variable(name='x')
        e = so.expr_sum(x for i in I)
        self.assertEqual(so.to_expression(e), 'sum {i in I} (x)')

    def test_comparable(self):
        self.assertTrue(so.util.is_comparable(4))
        self.assertFalse(so.util.is_comparable(dict()))
        self.assertTrue(so.util.is_comparable('abc'))

    def test_flatten_tuple(self):
        tp = (3, 4, (5, (1, 0), 2))
        self.assertEqual(list(so.util.flatten_tuple(tp)),
                         [3, 4, 5, 1, 0, 2])

    def test_sas_string(self):
        S = so.exp_range(1, 11, 2)
        self.assertEqual(so.util.package_utils._to_sas_string(S), '1..10 by 2')

        def invalid_type():
            from collections import OrderedDict
            so.util.package_utils._to_sas_string(OrderedDict(a=4))
        self.assertRaises(TypeError, invalid_type)
