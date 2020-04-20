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

from tests.swat_config import create_cas_connection


class TestCreateData(unittest.TestCase):
    """
    Unit tests for CREATE DATA statements
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
                so.exp_range(1, 6), so.exp_range(1, 4), name='m', init=0)
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
            s = so.Set(name='S', value=so.exp_range(1, 6))
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
            s = so.Set(name='S', value=so.exp_range(1, 6))
            x = so.VariableGroup(s, name='x')
            x[1] = 1
            create_data(table='example', index={'key': ['i'], 'set': so.exp_range(1, 4)}, columns=[x])

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set S = 1..5;
               var x {{S}};
               x[1] = 1;
               create data example from [i] = {1..3} x;
            quit;'''))

    def test_subset_index(self):
        with so.Workspace('w') as w:
            s = so.Set(name='S', value=so.exp_range(1, 6))
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
            s = so.Set(name='S', value=so.exp_range(1, 6))
            t = so.Set(name='T', value=so.exp_range(1, 4))
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
            s = so.Set(name='S', value=so.exp_range(1, 6))
            t = so.Set(name='T', value=so.exp_range(1, 4))
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

    def test_index_with_iterate(self):
        if TestCreateData.conn is None:
            self.skipTest('Session is not available')


        from sasoptpy.util import iterate, concat
        with so.Workspace('w') as w:
            alph = so.Set(name='alph', settype=so.string, value=['a', 'b', 'c'])
            x = so.VariableGroup([1, 2, 3], alph, name='x', init=2)
            with iterate(so.exp_range(1, 4), name='i') as i:
                c = create_data(
                    table='example',
                    index={'key': [i], 'set': [i.get_set()]},
                )

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set <str> alph = {'a','b','c'};
               var x {{1,2,3}, {alph}} init 2;
               create data example from [i] = {{1..3}} ;
            quit;'''))

        # Append column with index
        session = TestCreateData.conn
        with so.Workspace('w', session=session) as w:
            alph = so.Set(name='alph', settype=so.string, value=['a', 'b', 'c'])
            x = so.VariableGroup([1, 2, 3], alph, name='x', init=2)
            with iterate(so.exp_range(1, 4), name='i') as i:
                c = create_data(
                    table='example',
                    index={'key': [i], 'set': [i.get_set()]},
                )
                with iterate(alph, name='j') as j:
                    c.append(
                        {'name': concat('x', j),
                         'expression': x[i, j],
                         'index': j}
                    )

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set <str> alph = {'a','b','c'};
               var x {{1,2,3}, {alph}} init 2;
               create data example from [i] = {{1..3}} {j in alph} < col('x' || j)=(x[i, j]) >;
            quit;'''))

        w.submit()
        self.assertEqual(
            session.CASTable('example').to_frame().to_string(), cleandoc('''
                 i   xa   xb   xc
            0  1.0  2.0  2.0  2.0
            1  2.0  2.0  2.0  2.0
            2  3.0  2.0  2.0  2.0'''))

    def test_multiple_iterator(self):
        from sasoptpy.util import concat, iterate
        with so.Workspace('w') as w:
            S = so.Set(name='S', value=[1, 2, 3])
            T = so.Set(name='T', value=[1, 3, 5])
            x = so.VariableGroup(S, T, name='x', init=1)
            with iterate(S, name='i') as i, iterate(T, name='j') as j:
                create_data(
                    table='out',
                    index={},
                    columns=[
                        {'name': concat('x', concat(i, j)),
                         'expression': x[i, j],
                         'index': [i, j]}
                    ]
                )
        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set S = {1,2,3};
               set T = {1,3,5};
               var x {{S}, {T}} init 1;
               create data out from {i in S, j in T} < col('x' || i || j)=(x[i, j]) >;
            quit;'''))

    def test_full_example(self):
        if TestCreateData.conn is None:
            self.skipTest('Session is not available')
        session = TestCreateData.conn
        from sasoptpy.util import concat, iterate

        with so.Workspace('w', session=session) as w:
            m = so.Parameter(name='m', value=3)
            n = so.Parameter(name='n', value=4)
            with iterate(so.exp_range(1, m), 'i') as i, iterate(so.exp_range(1, n), 'j') as j:
                a = so.ParameterGroup(i, j, name='a', value=i * j)
                b = so.ParameterGroup(i, name='b', value=i**2)
            subset = so.Set(name='subset', value=so.exp_range(2, m))
            with iterate(subset, 'i') as i, iterate(so.exp_range(1, n), 'j') as j:
                cd = create_data(
                    table='out',
                    index={'key': [i], 'set': [i.get_set()]},
                    columns=[
                        {'name': concat('a', j), 'expression': a[i, j],
                         'index': j},
                        {'expression': b}
                    ]
                )

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num m = 3;
               num n = 4;
               num a {i in 1..m, j in 1..n} = i * j;
               num b {i in 1..m} = (i) ** (2);
               set subset = 2..m;
               create data out from [i] = {{subset}} {j in 1..n} < col('a' || j)=(a[i, j]) > b;
            quit;'''))

        w.submit()
        response = session.CASTable('out').to_frame()
        self.assertEqual(response.to_string(), cleandoc('''
                 i   a1   a2   a3    a4    b
            0  2.0  2.0  4.0  6.0   8.0  4.0
            1  3.0  3.0  6.0  9.0  12.0  9.0'''))

        response2 = cd.get_response()
        self.assertEqual(response2.to_string(), cleandoc('''
                 i   a1   a2   a3    a4    b
            0  2.0  2.0  4.0  6.0   8.0  4.0
            1  3.0  3.0  6.0  9.0  12.0  9.0'''))
