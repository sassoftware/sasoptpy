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
