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
Unit test for literal statements.
"""

import unittest
import sasoptpy as so
from inspect import cleandoc


class TestLiteral(unittest.TestCase):
    """
    Unit tests for literal statements
    """

    def test_literal_expr(self):
        literal = so.LiteralStatement('expand;')
        self.assertEqual(so.to_expression(literal), 'expand;')

    def test_use_problem(self):
        from sasoptpy.actions import use_problem
        with so.Workspace('w') as w:
            m = so.Model(name='m')
            m2 = so.Model(name='m2')
            use_problem(m)
            x = so.Variable(name='x')
            use_problem(m2)
            m.solve()
            m2.solve()

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               problem m;
               problem m2;
               use problem m;
               var x;
               use problem m2;
               use problem m;
               solve;
               use problem m2;
               solve;
            quit;'''))

    def test_union(self):
        from sasoptpy.actions import union, put_item
        with so.Workspace('w') as w:
            n = so.Parameter(name='n', value=11)
            S = so.Set(name='S', value=so.exp_range(1, n))
            T = so.Set(name='T', value=so.exp_range(n+1, 20))
            U = so.Set(name='U', value=union(S, T))
            put_item(U, names=True)

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num n = 11;
               set S = 1..n;
               set T = n+1..20;
               set U = S union T;
               put U=;
            quit;'''))

    def test_diff(self):
        from sasoptpy.actions import diff, put_item
        with so.Workspace('w') as w:
            S = so.Set(name='S', value=so.exp_range(1, 20))
            T = so.Set(name='T', value=so.exp_range(1, 15))
            U = so.Set(name='U', value=diff(S, T))
            put_item(U, names=True)

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set S = 1..19;
               set T = 1..14;
               set U = S diff T;
               put U=;
            quit;'''))

    def test_substring(self):
        from sasoptpy.actions import substring, put_item
        with so.Workspace('w') as w:
            p = so.Parameter(name='p', value='random_string', ptype=so.STR)
            r = so.Parameter(name='r', value=substring(p, 1, 6), ptype=so.STR)
            put_item(r)

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               str p = 'random_string';
               str r = substr(p, 1, 6);
               put r;
            quit;'''))
