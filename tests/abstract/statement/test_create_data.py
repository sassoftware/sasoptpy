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
Unit test for create data statement.
"""

import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc
from sasoptpy.actions import create_data
from sasoptpy.util import concat


class TestAssignment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
        from swat import CAS, SWATError
        try:
            cls.conn = CAS(os.environ.get('CASHOST'),
                           int(os.environ.get('CASPORT')),
                           authinfo=os.environ.get('AUTHINFO'))
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)


    def test_various_col_types(self):
        # Regular
        with so.Workspace('w') as w:
            m = so.Parameter(name='m', value=7)
            n = so.Parameter(name='n', value=5)
            create_data(table='example', index={}, columns=[m, n])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
        proc optmodel;
            num m = 7;
            num n = 5;
            create data example from m n;
        quit;'''))

        # Column name
        with so.Workspace('w') as w:
            m = so.Parameter(name='m', value=7)
            n = so.Parameter(name='n', value=5)
            create_data(table='example', index={}, columns=[
                {'name': 'ratio', 'expression': m/n}
            ])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
        proc optmodel;
            num m = 7;
            num n = 5;
            create data example from ratio=((m) / (n));
        quit;'''))

        # Custom column name
        with so.Workspace('w') as w:
            m = so.Parameter(name='m', value=7)
            n = so.Parameter(name='n', value=5)
            create_data(table='example', index={}, columns=[
                {'name': concat('s', n), 'expression': m+n}
            ])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
        proc optmodel;
            num m = 7;
            num n = 5;
            create data example from col('s' || n)=(m + n);
        quit;'''))

        # Combined
        with so.Workspace('w') as w:
            m = so.Parameter(name='m', value=7)
            n = so.Parameter(name='n', value=5)
            create_data(table='example', index={}, columns=[
                m, n,
                {'name': 'ratio', 'expression': m/n},
                {'name': concat('s', n), 'expression': m+n}
            ])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
        proc optmodel;
            num m = 7;
            num n = 5;
            create data example from m n ratio=((m) / (n)) col('s' || n)=(m + n);
        quit;'''))

    def test_index(self):
        with so.Workspace('w') as w:
            m = so.ParameterGroup(
                so.exp_range(1, 5), so.exp_range(1, 3), name='m', init=0)
            m[1, 1] = 1
            m[4, 1] = 1
            S = so.Set(name='ISET', value=[i**2 for i in range(1, 3)])
            create_data(
                table='example',
                index={'key': ['i', 'j'], 'set': [S, [1, 2]]},
                columns=[m]
            )

        self.assertEqual(so.to_optmodel(w), cleandoc('''
        proc optmodel;
            num m {1..5, 1..3} init 0;
            m[1, 1] = 1;
            m[4, 1] = 1;
            set ISET = {1,4};
            create data example from [i j] = {{ISET,{1,2}}} m;
        quit;'''))

    def test_regular_index(self):
        with so.Workspace('w') as w:
            s = so.Set(name='S', value=so.exp_range(1, 5))
            x = so.VariableGroup(s, name='x')
            create_data(table='example', index={'key': ['i']}, columns=[x])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                set S = 1..5;
                var x {{S}};
                create data example from [i] x;
            quit;'''))

    def test_custom_index(self):
        with so.Workspace('w') as w:
            s = so.Set(name='S', value=so.exp_range(1, 5))
            x = so.VariableGroup(s, name='x')
            x[1] = 1
            create_data(table='example', index={'key': ['i'], 'set': so.exp_range(1, 3)}, columns=[x])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                set S = 1..5;
                var x {{S}};
                x[1] = 1;
                create data example from [i] = {1..3} x;
            quit;'''))

    def test_subset_index(self):
        with so.Workspace('w') as w:
            s = so.Set(name='S', value=so.exp_range(1, 5))
            x = so.VariableGroup(s, name='x')
            x[1] = 1
            z = so.Set(name='Z', value=[1, 3, 5])
            create_data(table='example', index={'key': ['i'], 'set': z}, columns=[x])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                set S = 1..5;
                var x {{S}};
                x[1] = 1;
                set Z = {1,3,5};
                create data example from [i] = {Z} x;
            quit;'''))

    def test_multi_index(self):
        with so.Workspace('w') as w:
            s = so.Set(name='S', value=so.exp_range(1, 5))
            t = so.Set(name='T', value=so.exp_range(1, 3))
            x = so.VariableGroup(s, t, name='x')
            x[1, 3] = 1
            create_data(
                table='example',
                index={'key': ['i', 'j'], 'set': [s, t]},
                columns=[x])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                set S = 1..5;
                set T = 1..3;
                var x {{S}, {T}};
                x[1, 3] = 1;
                create data example from [i j] = {{S,T}} x;
            quit;'''))

    def test_subset_in_call(self):
        with so.Workspace('w') as w:
            s = so.Set(name='S', value=so.exp_range(1, 5))
            t = so.Set(name='T', value=so.exp_range(1, 3))
            x = so.VariableGroup(s, t, name='x')
            x[1, 3] = 1
            create_data(
                table='example',
                index={'key': ['i', 'j'], 'set': [s, [1, 3]]},
                columns=[x])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                set S = 1..5;
                set T = 1..3;
                var x {{S}, {T}};
                x[1, 3] = 1;
                create data example from [i j] = {{S,{1,3}}} x;
            quit;'''))
