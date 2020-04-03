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
Test for set class
"""

import unittest
import sasoptpy as so
from inspect import cleandoc

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
from util import assert_equal_wo_temps

class TestSet(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.abstract.Set` objects
    """

    def setUp(self):
        so.reset()

    def test_initialization(self):
        with so.Workspace('w') as w:
            S = so.Set(name='S')
            T = so.Set(name='T', init=range(11))
            V = so.Set(name='V', value=[1, 2, 4])
            W = so.Set(name='W', settype=[so.STR, so.NUM])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set S;
               set T init 0..10;
               set V = {1,2,4};
               set <str, num> W;
            quit;'''))

        self.assertEqual(repr(S),
                         'sasoptpy.abstract.Set(name=S, settype=[\'num\'])')
        self.assertEqual(
            repr(T),
            'sasoptpy.abstract.Set(name=T, settype=[\'num\'], init=range(0, 11))')
        self.assertEqual(
            repr(V),
            'sasoptpy.abstract.Set(name=V, settype=[\'num\'], value=[1, 2, 4])'
        )
        self.assertEqual(
            repr(W),
            'sasoptpy.abstract.Set(name=W, settype=[\'str\', \'num\'])'
        )

    def test_in_set(self):

        e = so.Parameter(name='e', value=1)
        S = so.Set(name='S')
        if e.sym in S:
            self.assertEqual(e.sym.get_conditions_str(), 'e IN S')
        x = so.Variable(name='x')
        def incorrect_type():
            if x in S:
                print('x is in S')
        self.assertRaises(RuntimeError, incorrect_type)

    def test_inline_set(self):
        from sasoptpy.actions import inline_condition, for_loop
        from sasoptpy.abstract.math import mod

        with so.Workspace('w') as w:
            p = so.Parameter(name='p')
            S = so.Set(name='S', value=so.exp_range(1, 11))
            iset = so.InlineSet(lambda: (x for x in S
                                if inline_condition(mod(x, 3) == 0)))
            for i in for_loop(iset):
                p.set_value(i)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num p;
               set S = 1..10;
               for {TEMP2 in {TEMP1 in S: mod(TEMP1 , 3) = 0}} do;
                  p = TEMP2;
               end;
            quit;'''))

        assert_equal_wo_temps(self, repr(iset),
                              'sasoptpy.InlineSet({o4 in S: mod(o4 , 3) = 0}}')