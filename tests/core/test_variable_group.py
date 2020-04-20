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
Unit tests for core classes.
"""

import unittest
import sasoptpy as so
import pandas as pd

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
from util import assert_equal_wo_temps


class TestVariableGroup(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.VariableGroup` objects
    """

    def setUp(self):
        pass

    def test_constructor(self):
        idx = [1, 2, 3]
        v = so.VariableGroup(idx, name='vg_1')
        self.assertEqual(repr(v),
                         "sasoptpy.VariableGroup([1, 2, 3], name='vg_1')")

        u = so.VariableGroup(5, name='u')
        self.assertEqual(repr(u),
                         "sasoptpy.VariableGroup([0, 1, 2, 3, 4], name='u')")

        # w = so.VariableGroup([('a', 1), ('a', 2), ('b', 1), ('b', 2)], name='w')
        # self.assertEqual(repr(w),
        #                  "sasoptpy.VariableGroup(['a', 'b'], [1, 2], name='w')")

        def pass_error():
            z = so.VariableGroup(name='z')
        self.assertRaises(ValueError, pass_error)

    def test_get_name(self):
        # Test regular name
        u = so.VariableGroup(4, name='myvargroup')
        self.assertEqual(u.get_name(), 'myvargroup')

        # Test default name
        v = so.VariableGroup(5, name=None)
        self.assertEqual(v.get_name(), v._name)

    def test_abstract(self):
        u = so.VariableGroup(4, name='u')
        self.assertFalse(u._abstract)
        u.set_abstract(True)
        self.assertTrue(u._abstract)

        I = so.Set(name='I')
        v = so.VariableGroup(I, name='v')
        self.assertTrue(v._abstract)
        v.set_abstract(False)
        self.assertFalse(v._abstract)

    def test_get_item(self):
        I = so.Set(name='I')
        v = so.VariableGroup(I, name='v')

        for i in I:
            individual_variable = v[i]
            self.assertEqual(str(individual_variable), 'v[{}]'.format(i))
            same_variable = v[i]
            self.assertEqual(str(same_variable), 'v[{}]'.format(i))

        idx1 = [1, 2, 3]
        idx2 = ['a', 'b', 'c']
        x = so.VariableGroup(idx1, idx2, name='x')
        self.assertEqual(len(x[1,]), 3)
        self.assertEqual(type(x[1]), list)

        for e, i in enumerate(x['*', 'a']):
            self.assertEqual(str(i), 'x[{}, a]'.format(e+1))

        def empty_list():
            a = x['*', 'd']
        self.assertWarns(RuntimeWarning, empty_list)

    def test_defn(self):
        idx1 = [1, 2, 3]
        idx2 = ['a', 'b', 'c']
        x = so.VariableGroup(idx1, idx2, name='x')
        self.assertEqual(x._defn(), "var x {{1,2,3}, {'a','b','c'}};")

        from sasoptpy.abstract import Set, Parameter
        idx3 = Set(name='I')
        y = so.VariableGroup(idx3, name='y')
        self.assertEqual(y._defn(), "var y {{I}};")

        z = so.VariableGroup(4, vartype=so.INT, name='z', lb=1)
        self.assertEqual(z._defn(), "var z {{0,1,2,3}} integer >= 1;")
        z.set_bounds(ub=10)
        self.assertEqual(z._defn(), "var z {{0,1,2,3}} integer >= 1 <= 10;")
        z.set_init(5)
        self.assertEqual(z._defn(), "var z {{0,1,2,3}} integer >= 1 <= 10 init 5;")

        u = so.VariableGroup(5, vartype=so.BIN, name='u')
        self.assertEqual(u._defn(), "var u {{0,1,2,3,4}} binary;")

        t = so.VariableGroup(idx3, name='t', init=10)
        self.assertEqual(t._defn(), "var t {{I}} init 10;")

        #         w = so.VariableGroup(2, name='w', lb=0, ub=10)
        #         w[0].set_bounds(lb=2, ub=8)
        #         w[1].set_bounds(lb=1, ub=7)
        #         expected_def = """var w {{0,1}} >= 0 <= 10;
        # w[0].lb = 2;
        # w[0].ub = 8;
        # w[1].lb = 1;
        # w[1].ub = 7;"""
        #         self.assertEqual(w._defn(), expected_def)
        #         w[0].set_init(4)
        #         expected_def = """var w {{0,1}} >= 0 <= 10;
        # w[0].lb = 2;
        # w[0].ub = 8;
        # w[0] = 4;
        # w[1].lb = 1;
        # w[1].ub = 7;"""
        #         self.assertEqual(w._defn(), expected_def)

    def test_add_member(self):
        from sasoptpy.abstract import Set
        I = Set(name='I')
        x = so.VariableGroup(I, name='x')
        x.add_member(key=0, init=5)
        self.assertEqual(str(x[0]), "x[0]")

        y = so.Variable(name='y')
        x.include_member('y', var=y)
        self.assertEqual(id(y), id(x['y']))

    def test_sum(self):
        I = so.Set(name='I')
        x = so.VariableGroup(I, name='x')
        e = x.sum('*')
        key = e._iterkey[0]
        self.assertEqual(e._expr(), "sum {{{k} in I}} (x[{k}])".format(k=key))

        z = so.VariableGroup(3, 4, name='z')
        e = z.sum(0, (1, 2))
        self.assertEqual(e._expr(), "z[0, 1] + z[0, 2]")

        idx1 = ['a', 'b', 'c']
        y = so.VariableGroup(I, idx1, name='y')
        e = y.sum('*', 'a')
        key = e._iterkey[0]
        self.assertEqual(e._expr(), "sum {{{k} in I}} (y[{k}, 'a'])".format(
            k=key
        ))

        e = y.sum('*', ('a', 'b'))
        key = e._iterkey[0]
        self.assertEqual(
            e._expr(),
            "sum {{{k} in I}} (y[{k}, 'a'] + y[{k}, 'b'])".format(k=key))

        e = y.sum(1, '*')
        self.assertEqual(e._expr(), "y[1, 'a'] + y[1, 'b'] + y[1, 'c']")

        w = so.VariableGroup([1, 2, 3], ['a', 'b'], name='w')
        e = w.sum([1, 3], '*')
        self.assertEqual(e._expr(), "w[1, 'a'] + w[1, 'b'] + w[3, 'a'] + w[3, 'b']")

    def test_mult(self):
        x = so.VariableGroup(3, name='x')
        m1 = [2, 3, 4]
        e = x.mult(m1)
        self.assertEqual(e._expr(), "2 * x[0] + 3 * x[1] + 4 * x[2]")

        m2 = pd.Series(m1)
        e = x.mult(m2)
        self.assertEqual(e._expr(), "2 * x[0] + 3 * x[1] + 4 * x[2]")

        data = [['a', 1, 3, 7], ['b', 4, 5, 6]]
        df = pd.DataFrame(
            data, columns=['idx', 'low', 'med', 'high']).set_index(['idx'])
        y = so.VariableGroup(df.index, df.columns, name='y')
        e = y.mult(df)
        self.assertEqual(
            e._expr(),
            "y['a', 'low'] + 3 * y['a', 'med'] + 7 * y['a', 'high'] + 4 * y['b', 'low'] + 5 * y['b', 'med'] + 6 * y['b', 'high']"
        )

        idx = ['a', 'b', 'c']
        z = so.VariableGroup(idx, name='z')
        data_dict = {'a': 1, 'b': 2, 'c': -4}
        e = z.mult(data_dict)
        self.assertEqual(e._expr(), "z['a'] + 2 * z['b'] - 4 * z['c']")

        idx = [1, 2]
        w = so.VariableGroup(idx, idx, name='w')
        data_dict = {(1, 1): 3, (1,2): 4, (2,1): 7, (2,2): 2}
        e = w.mult(data_dict)
        self.assertEqual(
            e._expr(), "3 * w[1, 1] + 4 * w[1, 2] + 7 * w[2, 1] + 2 * w[2, 2]")

        def unknown_key():
            data_dict = {(1, 1): 3, (3, 3): 9}
            e = w.mult(data_dict)
            e._expr()
        self.assertRaises(KeyError, unknown_key)

    def test_init(self):
        x = so.VariableGroup(3, name='x', init=4)
        self.assertTrue(all(i._init == 4 for i in x))
        x.set_init(5)
        self.assertTrue(all(i._init == 5 for i in x))

        from sasoptpy.abstract import Set
        I = Set(name='I')
        y = so.VariableGroup(I, name='y')
        y[0].set_init(5)
        self.assertEqual(y[0]._init, 5)
        y.set_init(4)
        self.assertEqual(y[0]._init, 4)

    def test_str(self):
        x = so.VariableGroup(2, name='x')
        self.assertEqual(
            str(x), "Variable Group (x) [\n  [0: x[0]]\n  [1: x[1]]\n]"
        )

    def test_set_bounds(self):
        x = so.VariableGroup(2, name='x')
        x.set_bounds(ub=2)
        self.assertEqual(x._ub, 2)
        self.assertEqual(so.to_definition(x), "var x {{0,1}} <= 2;")
        x.set_bounds(lb=1)
        self.assertEqual(x._lb, 1)
        self.assertEqual(so.to_definition(x), "var x {{0,1}} >= 1 <= 2;")
        x[0].set_bounds(lb=5)
        self.assertEqual(so.to_definition(x), "var x {{0,1}} >= 1 <= 2;")
        self.assertEqual(x._member_defn(), "x[0].lb = 5;")
        x[1].set_bounds(ub=10)
        self.assertEqual(x._member_defn(), "x[0].lb = 5;\nx[1].ub = 10;")

    def test_shadow(self):
        I = so.Set(name='I')
        x = so.VariableGroup(I, name='x')
        j = so.SetIterator(I, name='j')
        self.assertEqual(so.to_expression(x[j]), 'x[j]')
        y = so.VariableGroup(I, I, name='y')

        from sasoptpy.util import iterate

        with iterate([I, I], name='i') as i:
            z = y[i]
            self.assertEqual(so.to_expression(z), 'y[i]')

        J = so.Set(name='J', settype=[so.string, so.string])
        w = so.VariableGroup(J, name='w')
        for j in J:
            assert_equal_wo_temps(self, so.to_expression(w[j]), 'w[o1, o2]')

    def tearDown(self):
        so.reset()
