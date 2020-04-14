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

from collections import OrderedDict
from difflib import SequenceMatcher
import inspect
import os
import unittest
import warnings
from inspect import cleandoc

import sasoptpy as so
from tests.swat_config import create_cas_connection


class MockSASconfig:

    def __init__(self, name):
        self.name = name

class SASsession:

    def __init__(self, cfgname):
        import saspy
        self.sascfg = MockSASconfig(name=cfgname)

class TestModel(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.Model` objects
    """

    @classmethod
    def setUpClass(cls):
        cls.conn = None
        from swat import CAS, SWATError
        try:
            cls.conn = create_cas_connection()
        except SWATError:
            warnings.warn('CAS connection is not available',
                          RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available',
                          RuntimeWarning)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            cls.conn.close()

    def setUp(self):
        pass

    @classmethod
    def get_standard_model(cls, name):
        m = so.Model(name=name)
        x = m.add_variable(name='x')
        y = m.add_variables(2, name='y')
        c1 = m.add_constraint(x <= 5, name='c1')
        c2 = m.add_constraints((y[i] <= 3 for i in range(2)), name='c2')
        return m

    def test_initialize(self):
        m = so.Model(name='test_initialize', session=None)
        self.assertEqual(type(m), so.Model)

    def test_comparison(self):
        model1 = so.Model(name='test_equal_1', session=None)
        model2 = so.Model(name='test_equal_2', session=None)
        self.assertFalse(model1 == model2)

        model3 = model1
        self.assertTrue(model1 == model3)

        def invalid_comparison():
            _ = model1 == list()
        self.assertWarns(RuntimeWarning, invalid_comparison)

    def test_get_name(self):
        m = so.Model(name='m')
        self.assertEqual(m.get_name(), 'm')

    def test_adding_variable(self):
        m = so.Model(name='test_add_variable')

        x = m.add_variable(name='x')
        y = m.add_variable(name='y', vartype=so.INT)
        z = m.add_variable(name='z', lb=1, ub=10)
        w = m.add_variable(name='w', init=5)
        u = so.Variable(name='u')
        m.include(u)
        self.assertEqual(m.get_variables(), [x, y, z, w, u])
        self.assertEqual(m.get_variable_dict(), {'x': x, 'y': y, 'z': z,
                                                 'w': w, 'u': u})
        self.assertIs(m.get_variable('x'), x)
        self.assertIs(m.get_variable('t'), None)

    def test_duplicate_variables(self):

        m = so.Model(name='test_duplicate_variables')

        def add_multi_var():
            x = m.add_variable(name='x', lb=2)
            x2 = m.add_variable(name='x', lb=1)

        self.assertWarns(UserWarning, add_multi_var)
        self.assertEqual(m.to_optmodel(), cleandoc("""
            proc optmodel;
               min test_duplicate_variables_obj = 0;
               var x >= 1;
               solve;
            quit;"""))

    def test_dropping_variable(self):
        m = so.Model(name='test_drop_variable')
        x = m.add_variable(name='x')
        self.assertIs(m.get_variables()[0], x)
        self.assertIs(m.get_variable_dict()['x'], x)
        m.drop_variable(x)
        self.assertEqual(m.get_variables(), [])
        self.assertEqual(m.get_variable_dict(), {})
        m.include(x)
        self.assertIs(m.get_variable_dict()['x'], x)
        m.drop(x)
        self.assertEqual(m.get_variable_dict(), {})

    def test_drop_restore_var(self):
        m = so.Model(name='test_drop_restore')
        x = m.add_variable(name='x')
        y = m.add_variables(5, name='y')
        m.set_objective(y[3], sense=so.minimize, name='obj')
        self.assertEqual(m.to_optmodel(), cleandoc('''
            proc optmodel;
               var x;
               var y {{0,1,2,3,4}};
               min obj = y[3];
               solve;
            quit;'''))
        m.drop_variable(x)
        m.drop_variable(y[1])
        m.drop_variable(y[2])
        self.assertEqual(m.to_optmodel(), cleandoc('''
            proc optmodel;
               var y {{0,1,2,3,4}};
               min obj = y[3];
               drop y[1] y[2];
               solve;
            quit;'''))
        m.restore_variable(x)
        m.restore_variable(y[2])
        self.assertEqual(m.to_optmodel(), cleandoc('''
            proc optmodel;
               var x;
               var y {{0,1,2,3,4}};
               min obj = y[3];
               drop y[1];
               solve;
            quit;'''))

    def test_adding_vargroup(self):
        m = so.Model(name='test_add_vg')

        x = m.add_variables(2, name='x')
        y = m.add_variables(['a', 'b'], name='y', vartype=so.BIN)
        I = so.abstract.Set(name='I')
        z = m.add_variables(I, name='z', lb=1, ub=10, init=5)
        w = so.VariableGroup(5, name='w')
        m.include(w)
        vars = [('x', x), ('y', y), ('z', z), ('w', w)]
        self.assertEqual(m.get_grouped_variables(), OrderedDict(vars))
        self.assertIs(m.get_variable('x')[0], x[0])

    def test_dropping_vargroup(self):
        m = so.Model(name='test_drop_vg')
        x = m.add_variables(2, name='x')
        self.assertEqual(m.get_grouped_variables(), OrderedDict([('x', x)]))
        m.drop_variables(x)
        self.assertEqual(m.get_grouped_variables(), OrderedDict())
        m.include(x)
        self.assertEqual(m.get_grouped_variables(), OrderedDict([('x', x)]))
        m.drop(x)
        self.assertEqual(m.get_grouped_variables(), OrderedDict())

    def test_adding_constraint(self):
        m = so.Model(name='test_add_constraint')
        x = m.add_variable(name='x')

        c1 = m.add_constraint(x <= 5, name='c1')
        c2 = m.add_constraint(2 * x + x ** 5 >= 1, name='c2')
        self.assertEqual([c1, c2], m.get_constraints())
        self.assertEqual({'c1': c1, 'c2': c2}, m.get_constraints_dict())

        def invalid_constraint():
            from math import inf
            c3 = m.add_constraint(x <= inf, name='c3')
        self.assertRaises(ValueError, invalid_constraint)

        cx = m.get_constraint('c1')
        self.assertEqual(cx, c1)
        cy = m.get_constraint('c3')
        self.assertEqual(cy, None)

    def test_duplicate_constraints(self):

        m = so.Model(name='test_duplicate_constraints')

        def add_multi_con():
            x = m.add_variable(name='x')

            c1 = m.add_constraint(x <= 5, name='c')
            c2 = m.add_constraint(x <= 5, name='c')

        self.assertWarns(UserWarning, add_multi_con)
        self.assertEqual(m.to_optmodel(), cleandoc("""
            proc optmodel;
               min test_duplicate_constraints_obj = 0;
               var x;
               con c : x <= 5;
               solve;
            quit;"""))

    def test_drop_restore_cons(self):
        m = so.Model(name='test_drop_restore_constraints')
        x = m.add_variable(name='x')
        y = m.add_variables(5, name='y')
        m.set_objective(y[3], sense=so.minimize, name='obj')

        c1 = m.add_constraint(x <= 5, name='c1')
        c2 = m.add_constraints((y[i] <= i for i in range(5)), name='c2')
        self.assertEqual(m.to_optmodel(), cleandoc("""
            proc optmodel;
               var x;
               var y {{0,1,2,3,4}};
               min obj = y[3];
               con c1 : x <= 5;
               con c2_0 : y[0] <= 0;
               con c2_1 : y[1] <= 1;
               con c2_2 : y[2] <= 2;
               con c2_3 : y[3] <= 3;
               con c2_4 : y[4] <= 4;
               solve;
            quit;"""))
        m.drop_constraint(c1)
        m.drop_constraint(c2[1])
        m.drop_constraint(c2[2])
        self.assertEqual(m.to_optmodel(), cleandoc("""
            proc optmodel;
               var x;
               var y {{0,1,2,3,4}};
               min obj = y[3];
               con c2_0 : y[0] <= 0;
               con c2_1 : y[1] <= 1;
               con c2_2 : y[2] <= 2;
               con c2_3 : y[3] <= 3;
               con c2_4 : y[4] <= 4;
               drop c2_1 c2_2;
               solve;
            quit;"""))
        m.restore_constraint(c1)
        m.restore_constraint(c2[2])
        self.assertEqual(m.to_optmodel(), cleandoc("""
            proc optmodel;
               var x;
               var y {{0,1,2,3,4}};
               min obj = y[3];
               con c1 : x <= 5;
               con c2_0 : y[0] <= 0;
               con c2_1 : y[1] <= 1;
               con c2_2 : y[2] <= 2;
               con c2_3 : y[3] <= 3;
               con c2_4 : y[4] <= 4;
               drop c2_1;
               solve;
            quit;"""))

    def test_dropping_constraint(self):
        m = so.Model(name='test_drop_constraint')
        x = m.add_variable(name='x')
        c1 = m.add_constraint(x <= 5, name='c1')
        self.assertEqual({'c1': c1}, m.get_constraints_dict())
        m.drop_constraint(c1)
        self.assertEqual({}, m.get_constraints_dict())
        m.include(c1)
        self.assertEqual({'c1': c1}, m.get_constraints_dict())
        m.drop(c1)
        self.assertEqual({}, m.get_constraints_dict())

    def test_adding_constraints(self):
        m = so.Model(name='test_add_cg')
        x = m.add_variables(5, name='x')

        c1 = m.add_constraints((x[i] >= i for i in range(5)), name='c1')
        self.assertEqual(OrderedDict([('c1', c1)]), m.get_grouped_constraints())
        self.assertEqual(c1, m.get_constraint('c1'))

        c2 = so.ConstraintGroup((i * x[i] <= 10 for i in range(5)), name='c2')
        m.include(c2)
        grouped_con_dict = OrderedDict([('c1', c1), ('c2', c2)])
        self.assertEqual(grouped_con_dict, m.get_grouped_constraints())

        def warn_user_single_constraint():
            c3 = m.add_constraints(x[0] >= 1, name='c3')
        self.assertWarns(UserWarning, warn_user_single_constraint)

    def test_dropping_constraints(self):
        m = so.Model(name='test_drop_cg')
        x = m.add_variables(2, name='x')
        c1 = m.add_constraints((x[i] <= i for i in range(2)), name='c1')
        self.assertEqual(m.get_grouped_constraints(), OrderedDict([('c1', c1)]))
        m.drop_constraints(c1)
        self.assertEqual(m.get_grouped_constraints(), OrderedDict())
        m.include(c1)
        self.assertEqual(m.get_grouped_constraints(), OrderedDict([('c1', c1)]))
        m.drop(c1)
        self.assertEqual(m.get_grouped_constraints(), OrderedDict())

    def test_add_set(self):
        m = so.Model(name='test_add_set')
        I = m.add_set(name='I', init=2)
        self.assertEqual(m.get_sets(), [I])
        self.assertEqual(so.to_definition(m.get_sets()[0]), "set I init 2;")

    def test_add_parameter(self):
        m = so.Model(name='test_add_parameter')
        p = m.add_parameter(name='p', init=10)
        I = m.add_set(name='I')
        r = m.add_parameter(I, name='r', init=5)
        self.assertEqual([p, r], m.get_parameters())
        m.drop(r)
        self.assertEqual([p], m.get_parameters())

    def test_add_implicit_var(self):
        m = so.Model(name='test_add_impvar')
        x = m.add_variables(5, name='x')
        y = m.add_implicit_variable((i * x[i] + x[i] ** 2 for i in range(5)),
                                    name='y')
        self.assertEqual([y], m.get_implicit_variables())

    def test_add_literal_statement(self):
        m = so.Model(name='test_add_literal_statement')
        m.set_objective(0, name='empty_obj')
        m.add_statement('var x {0,1};')
        m.add_statement('solve;')
        self.assertEqual(
            m.to_optmodel(solve=False),
            inspect.cleandoc('''
            proc optmodel;
               min empty_obj = 0;
               var x {0,1};
               solve;
            quit;'''))
        s = so.abstract.LiteralStatement('print x;')
        m.include(s)
        self.assertEqual(
            m.to_optmodel(solve=False),
            inspect.cleandoc('''
            proc optmodel;
               min empty_obj = 0;
               var x {0,1};
               solve;
               print x;
            quit;'''))
        m.drop(s)
        self.assertEqual(
            m.to_optmodel(solve=False),
            inspect.cleandoc('''
            proc optmodel;
               min empty_obj = 0;
               var x {0,1};
               solve;
            quit;'''))


    def test_add_abstract_statement(self):
        m = so.Model(name='m')
        x = m.add_variable(name='x')
        m.set_objective(x ** 2, sense=so.MIN, name='obj')
        s = so.abstract.LiteralStatement('expand;')
        m.add_statement(s)
        self.assertEqual(so.to_optmodel(m), inspect.cleandoc("""
            proc optmodel;
               var x;
               min obj = (x) ^ (2);
               expand;
               solve;
            quit;
            """))

    def test_postsolve_statement(self):
        m = so.Model(name='test_postsolve_statement')
        x = m.add_variable(name='x')
        c1 = m.add_constraint(x <= 10, name='c1')
        self.assertEqual(m.to_optmodel(), inspect.cleandoc("""
            proc optmodel;
               min test_postsolve_statement_obj = 0;
               var x;
               con c1 : x <= 10;
               solve;
            quit;"""))

        m.add_postsolve_statement('print x;')
        self.assertEqual(m.to_optmodel(), inspect.cleandoc("""
        proc optmodel;
           min test_postsolve_statement_obj = 0;
           var x;
           con c1 : x <= 10;
           solve;
           print x;
        quit;"""))

        m.add_postsolve_statement(so.abstract.LiteralStatement('expand;'))
        self.assertEqual(m.to_optmodel(), inspect.cleandoc("""
        proc optmodel;
           min test_postsolve_statement_obj = 0;
           var x;
           con c1 : x <= 10;
           solve;
           print x;
           expand;
        quit;"""))

    def test_include_model(self):
        m1 = so.Model(name='test_copy_model_1')
        x = m1.add_variable(name='x')
        y = m1.add_variables(2, name='y')
        c1 = m1.add_constraint(x + y[0] >= 2, name='c1')
        c2 = m1.add_constraints((x - y[i] <= 10 for i in range(2)), name='c2')
        m1.set_objective(2 * x + y[0] + 3 * y[1], name='model_obj')

        m2 = so.Model(name='test_copy_model_2')
        m2.include(m1)
        vars = OrderedDict([('x', x), ('y', y)])
        self.assertEqual(m2.get_grouped_variables(), vars)
        cons = OrderedDict([('c1', c1), ('c2', c2)])
        self.assertEqual(m2.get_grouped_constraints(), cons)
        self.assertEqual(m2.to_optmodel(),inspect.cleandoc("""
            proc optmodel;
               var x;
               var y {{0,1}};
               con c1 : x + y[0] >= 2;
               con c2_0 : x - y[0] <= 10;
               con c2_1 : x - y[1] <= 10;
               min model_obj = 2 * x + y[0] + 3 * y[1];
               solve;
            quit;"""))

    def test_set_get_objective(self):
        m = so.Model(name='test_set_get_objective')
        x = m.add_variable(name='x')

        # Regular objective
        obj1 = m.set_objective(2 * x, sense=so.MIN, name='obj1')
        self.assertIs(obj1, m.get_objective())

        # Multi objective
        obj2 = m.set_objective(5 * x, sense=so.MIN, name='obj2')
        self.assertIs(obj2, m.get_objective())
        obj3 = m.append_objective(10 * x, sense=so.MIN, name='obj3')
        self.assertEqual([obj2, obj3], m.get_all_objectives())
        self.assertEqual(
            m.to_optmodel(),
            inspect.cleandoc("""
            proc optmodel;
               var x;
               min obj2 = 5 * x;
               min obj3 = 10 * x;
               solve;
            quit;"""))

    def test_get_objective_value(self):
        m = so.Model(name='test_objective_value')
        x = m.add_variable(name='x')
        m.set_objective(x ** 2 - 4 * x + 5, sense=so.MIN, name='nonlinear')
        x.set_value(3)
        self.assertEqual(m.get_objective_value(), 2)

        if TestModel.conn:
            m.set_session(TestModel.conn)
            m.solve()
            self.assertEqual(m.get_objective_value(), 1)
            self.assertEqual(x.get_value(), 2)
        else:
            self.skipTest('No CAS connection available, skipping ' +
                              'objective value test')

        def zero_div_error():
            m.set_objective(x / x, sense=so.MIN, name='nonlinear2')
            x.set_value(0)
            m.clear_solution()
            m.get_objective_value()
        self.assertRaises(ZeroDivisionError, zero_div_error)

    def test_variable_coef(self):
        m = so.Model(name='test_get_variable_coef')
        x = m.add_variable(name='x')
        m.set_objective(5 * x, sense=so.MIN, name='obj1')

        self.assertEqual(m.get_variable_coef(x), 5)
        self.assertEqual(m.get_variable_coef('x'), 5)

        y = so.Variable(name='y')
        def variable_not_in_model():
            return m.get_variable_coef(y)
        self.assertRaises(RuntimeError, variable_not_in_model)

        m.set_objective(2 * x + y ** 2, sense=so.MIN, name='obj1')
        self.assertEqual(m.get_variable_coef('x'), 2)
        def nonlinear_objective():
            return m.get_variable_coef('y')
        self.assertWarns(RuntimeWarning, nonlinear_objective)

    def test_get_variable_value(self):

        if TestModel.conn is None:
            self.skipTest('Session is not available')

        m = so.Model(name='test_get_var_value')
        x = m.add_variable(name='x', lb=1.5, ub=10, vartype=so.INT)
        m.set_objective(x, sense=so.MIN, name='obj1')
        m.set_session(TestModel.conn)
        m.solve(verbose=True)
        self.assertEqual(m.get_variable_value(x), 2)

        I = m.add_set(name='I', value=range(2))
        y = m.add_variables(I, name='y', lb=0.5)
        m.set_objective(x + y[0] + y[1], sense=so.MIN, name='obj1')
        m.solve()
        self.assertEqual(m.get_variable_value(y[0]), 0.5)
        def get_variable_warning():
            self.assertEqual(m.get_variable_value('z'), None)
        self.assertWarns(UserWarning, get_variable_warning)

        m2 = so.Model(name='test_get_var_value_copy')
        m2.include(m)
        z = so.Variable(name='z')
        def raise_solution_error():
            return m2.get_variable_value(z)
        self.assertRaises(RuntimeError, raise_solution_error)

        m.add_variable(name='var with invalid name')
        def raise_syntax_error():
            return m.solve()
        self.assertRaises(SyntaxError, raise_syntax_error)

    def test_get_variable_value_abstract(self):
        if TestModel.conn is None:
            self.skipTest('Session is not available')

        import pandas as pd
        so.reset()

        m = so.Model(name='abstract_model')
        df = pd.DataFrame([
            ['a', 1],
            ['b', 2]
        ], columns=['tag', 'val'])
        idx = so.Set(name='idx', settype=so.STR)
        varlb = so.ParameterGroup(idx, name='varlb')
        m.include(idx, varlb)

        table = TestModel.conn.upload_frame(df, casout='server_data')
        from sasoptpy.actions import read_data
        r = read_data(
            table=table,
            index={'target': idx, 'key': 'tag'},
            columns=[
                {'target': varlb, 'column': 'val'}
            ]
        )
        m.include(r)
        y = so.VariableGroup(idx, name='y')
        c = so.ConstraintGroup((y[i] >= varlb[i] for i in idx), name='c')
        m.include(y, c)
        self.assertEqual(m.to_optmodel(), inspect.cleandoc("""
            proc optmodel;
               min abstract_model_obj = 0;
               set <str> idx;
               num varlb {idx};
               read data SERVER_DATA into idx=[tag] varlb=val;
               var y {{idx}};
               con c {o8 in idx} : y[o8] - varlb[o8] >= 0;
               solve;
            quit;
            """))
        m.set_session(TestModel.conn)
        m.solve()
        self.assertEqual(m.get_variable_value(y['a']), 1)
        self.assertEqual(m.get_statements(), [r])


    def test_get_summaries(self):
        if not TestModel.conn:
            self.skipTest('Session is not available')
        m = so.Model(name='test_get_summaries', session=TestModel.conn)
        x = m.add_variable(name='x', lb=1)
        y = m.add_variables(2, name='y', lb=1)
        m.set_objective(x + y[0], sense=so.MIN, name='obj1')
        m.add_constraint(x + 2 *y[0] + 3*y[1] >= 10, name='con1')
        m.solve()
        self.assertEqual(m.get_problem_summary().to_string(),
                         inspect.cleandoc("""
                                                            Value
                            Label                                
                            Objective Sense          Minimization
                            Objective Function               obj1
                            Objective Type                 Linear
                                                                 
                            Number of Variables                 3
                            Bounded Above                       0
                            Bounded Below                       3
                            Bounded Below and Above             0
                            Free                                0
                            Fixed                               0
                                                                 
                            Number of Constraints               1
                            Linear LE (<=)                      0
                            Linear EQ (=)                       0
                            Linear GE (>=)                      1
                            Linear Range                        0
                                                                 
                            Constraint Coefficients             3"""))

        seq = SequenceMatcher(None, m.get_solution_summary().to_string(),
                              inspect.cleandoc(
            """
                                         Value
            Label                             
            Solver                          LP
            Algorithm             Dual Simplex
            Objective Function            obj1
            Solution Status            Optimal
            Objective Value                  2
                                              
            Primal Infeasibility             0
            Dual Infeasibility               0
            Bound Infeasibility              0
                                              
            Iterations                       0
            Presolve Time                 0.00
            Solution Time                 0.00"""
        ))
        # There is a chance that the solution time is slightly different
        self.assertTrue(seq.ratio() > 0.99)

    def test_get_solution(self):
        if not TestModel.conn:
            self.skipTest('No session is defined, skipping get solution test')
        import pandas as pd
        m = so.Model(name='test_get_soln', session=TestModel.conn)
        data = [
            ['pen', 1, 3, 11],
            ['mug', 15, 10, 5],
            ['watch', 50, 2, 2],
            ['pc', 1500, 200, 1]
        ]
        data = pd.DataFrame(data, columns=['item', 'value', 'weight', 'ub'])
        data = data.set_index(['item'])
        items = data.index
        get = m.add_variables(items, name='get', vartype=so.INT, lb=0)
        value = data['value']
        weight = data['weight']
        ub = data['ub']
        m.set_objective(so.expr_sum(get[i] * value[i] for i in items),
                        sense=so.MAX, name='obj1')
        m.add_constraint(so.expr_sum(get[i] * weight[i] for i in items)
                         <= 210, name='value_total')
        m.add_constraints((get[i] <= ub[i] for i in items), name='upper_bound')

        # Regular solve and regular get
        m.solve(verbose=True)
        self.assertEqual(m.get_solution().to_string(), inspect.cleandoc(
            """
                 i         var  value   lb             ub  rc
            0  1.0    get[pen]    2.0 -0.0  1.797693e+308 NaN
            1  2.0    get[mug]   -0.0 -0.0  1.797693e+308 NaN
            2  3.0  get[watch]    2.0 -0.0  1.797693e+308 NaN
            3  4.0     get[pc]    1.0 -0.0  1.797693e+308 NaN
            """
        ))

        self.assertEqual(m.get_solution(vtype='dual').to_string(),
                         inspect.cleandoc(
            """
                 j                con  value  dual
            0  1.0        value_total  210.0   NaN
            1  2.0    upper_bound_pen    2.0   NaN
            2  3.0    upper_bound_mug   -0.0   NaN
            3  4.0  upper_bound_watch    2.0   NaN
            4  5.0     upper_bound_pc    1.0   NaN
            """
        ))

        m.solve(mps=True, options={'maxpoolsols': 3}, verbose=True)
        self.assertEqual(m.get_solution().to_string(), inspect.cleandoc(
            """
                       var   lb             ub  value  solution
            0     get[pen]  0.0  1.797693e+308    2.0       1.0
            1     get[mug]  0.0  1.797693e+308    0.0       1.0
            2   get[watch]  0.0  1.797693e+308    2.0       1.0
            3      get[pc]  0.0  1.797693e+308    1.0       1.0
            4     get[pen]  0.0  1.797693e+308    1.0       2.0
            5     get[mug]  0.0  1.797693e+308    0.0       2.0
            6   get[watch]  0.0  1.797693e+308    1.0       2.0
            7      get[pc]  0.0  1.797693e+308    1.0       2.0
            8     get[pen]  0.0  1.797693e+308    0.0       3.0
            9     get[mug]  0.0  1.797693e+308    0.0       3.0
            10  get[watch]  0.0  1.797693e+308    0.0       3.0
            11     get[pc]  0.0  1.797693e+308    0.0       3.0
            """
        ))
        self.assertEqual(m.get_solution('dual').to_string(), inspect.cleandoc(
            """
                                 con  value  solution
            0            value_total  210.0       1.0
            1     upper_bound['pen']    2.0       1.0
            2     upper_bound['mug']    0.0       1.0
            3   upper_bound['watch']    2.0       1.0
            4      upper_bound['pc']    1.0       1.0
            5            value_total  205.0       2.0
            6     upper_bound['pen']    1.0       2.0
            7     upper_bound['mug']    0.0       2.0
            8   upper_bound['watch']    1.0       2.0
            9      upper_bound['pc']    1.0       2.0
            10           value_total    0.0       3.0
            11    upper_bound['pen']    0.0       3.0
            12    upper_bound['mug']    0.0       3.0
            13  upper_bound['watch']    0.0       3.0
            14     upper_bound['pc']    0.0       3.0
            """
        ))
        self.assertEqual(m.get_solution(pivot=True).to_string(),
                         inspect.cleandoc(
            """
            solution    1.0  2.0  3.0
            var                      
            get[mug]    0.0  0.0  0.0
            get[pc]     1.0  1.0  0.0
            get[pen]    2.0  1.0  0.0
            get[watch]  2.0  1.0  0.0
            """
        ))
        self.assertEqual(m.get_solution('dual', pivot=True).to_string(),
                         inspect.cleandoc(
            """
            solution                1.0    2.0  3.0
            con                                    
            upper_bound['mug']      0.0    0.0  0.0
            upper_bound['pc']       1.0    1.0  0.0
            upper_bound['pen']      2.0    1.0  0.0
            upper_bound['watch']    2.0    1.0  0.0
            value_total           210.0  205.0  0.0
            """
        ))
        self.assertEqual(m.get_solution('primal', solution=2).to_string(),
                         inspect.cleandoc(
            """
                      var   lb             ub  value  solution
            4    get[pen]  0.0  1.797693e+308    1.0       2.0
            5    get[mug]  0.0  1.797693e+308    0.0       2.0
            6  get[watch]  0.0  1.797693e+308    1.0       2.0
            7     get[pc]  0.0  1.797693e+308    1.0       2.0
            """
                         ))
        self.assertEqual(m.get_solution('dual', solution=3).to_string(),
                         inspect.cleandoc(
            """
                                 con  value  solution
            10           value_total    0.0       3.0
            11    upper_bound['pen']    0.0       3.0
            12    upper_bound['mug']    0.0       3.0
            13  upper_bound['watch']    0.0       3.0
            14     upper_bound['pc']    0.0       3.0
            """
                         ))
        m.print_solution()

        def third_type():
            m.get_solution('x')
        self.assertRaises(ValueError, third_type)

    def test_set_coef(self):
        m = so.Model(name='test_set_coef')
        x = m.add_variable(name='x')
        y = m.add_variables(2, name='y')
        z = m.add_variable(name='z')
        obj = m.set_objective(2*x + 3*y[0] + 2*y[1], name='obj', sense=so.MIN)
        c1 = m.add_constraint(2* x + 5 * y[0] + 7 * y[1] <= 15, name='c1')
        self.assertEqual(m.get_variable_coef(x), 2)
        m.set_variable_coef(x, 3)
        self.assertEqual(m.get_variable_coef(x), 3)
        self.assertEqual(m.get_variable_coef(z), 0)
        m.set_variable_coef(z, 1)
        self.assertEqual(m.get_variable_coef(z), 1)

    def test_to_mps(self):
        m = so.Model(name='test_to_mps')
        x = m.add_variable(name='x', lb=0, ub=5, vartype=so.INT)
        y = m.add_variables(2, name='y', lb=1)
        m.set_objective(x + y[0], sense=so.MIN, name='xyobj')
        self.assertEqual(m.to_mps().to_string(), inspect.cleandoc(
            """
                 Field1    Field2       Field3  Field4    Field5  Field6  _id_
            0      NAME            test_to_mps     0.0               0.0     1
            1      ROWS                            NaN               NaN     2
            2       MIN     xyobj                  NaN               NaN     3
            3   COLUMNS                            NaN               NaN     4
            4            MARK0000     'MARKER'     NaN  'INTORG'     NaN     5
            5                   x        xyobj     1.0               NaN     6
            6            MARK0001     'MARKER'     NaN  'INTEND'     NaN     7
            7                y[0]        xyobj     1.0               NaN     8
            8                y[1]        xyobj     0.0               NaN     9
            9       RHS                            NaN               NaN    10
            10   RANGES                            NaN               NaN    11
            11   BOUNDS                            NaN               NaN    12
            12       LO       BND            x     0.0               NaN    13
            13       UP       BND            x     5.0               NaN    14
            14       LO       BND         y[0]     1.0               NaN    15
            15       LO       BND         y[1]     1.0               NaN    16
            16   ENDATA                            0.0               0.0    17
            """
        ))
        m.set_objective(x + 10, name='o', sense=so.MAX)
        self.assertEqual(m.to_mps(constant=True).to_string(),
                         inspect.cleandoc(
        """
             Field1        Field2        Field3  Field4    Field5  Field6  _id_
        0      NAME                 test_to_mps     0.0               0.0     1
        1      ROWS                                 NaN               NaN     2
        2       MAX    o_constant                   NaN               NaN     3
        3   COLUMNS                                 NaN               NaN     4
        4                MARK0000      'MARKER'     NaN  'INTORG'     NaN     5
        5                       x    o_constant     1.0               NaN     6
        6                MARK0001      'MARKER'     NaN  'INTEND'     NaN     7
        7                    y[0]    o_constant     0.0               NaN     8
        8                    y[1]    o_constant     0.0               NaN     9
        9            obj_constant    o_constant     1.0               NaN    10
        10      RHS                                 NaN               NaN    11
        11   RANGES                                 NaN               NaN    12
        12   BOUNDS                                 NaN               NaN    13
        13       LO           BND             x     0.0               NaN    14
        14       UP           BND             x     5.0               NaN    15
        15       LO           BND          y[0]     1.0               NaN    16
        16       LO           BND          y[1]     1.0               NaN    17
        17       FX           BND  obj_constant    10.0               NaN    18
        18   ENDATA                                 0.0               0.0    19
        """
                         ))

        # Add invalid constraints for the frame
        c1 = m.add_constraint(y[0] + x >= 0, name='zero_lb')
        c2 = m.add_constraint(y[0] <= 100, name='inf_ub')
        from math import inf
        c2.set_rhs(inf)
        self.assertEqual(m.to_mps().to_string(), inspect.cleandoc(
        """
             Field1        Field2        Field3  Field4    Field5  Field6  _id_
        0      NAME                 test_to_mps     0.0               0.0     1
        1      ROWS                                 NaN               NaN     2
        2       MAX    o_constant                   NaN               NaN     3
        3         G       zero_lb                   NaN               NaN     4
        4         L        inf_ub                   NaN               NaN     5
        5   COLUMNS                                 NaN               NaN     6
        6                MARK0000      'MARKER'     NaN  'INTORG'     NaN     7
        7                       x    o_constant     1.0   zero_lb     1.0     8
        8                MARK0001      'MARKER'     NaN  'INTEND'     NaN     9
        9                    y[0]       zero_lb     1.0    inf_ub     1.0    10
        10                   y[1]    o_constant     0.0               NaN    11
        11           obj_constant    o_constant     1.0               NaN    12
        12      RHS                                 NaN               NaN    13
        13   RANGES                                 NaN               NaN    14
        14   BOUNDS                                 NaN               NaN    15
        15       LO           BND             x     0.0               NaN    16
        16       UP           BND             x     5.0               NaN    17
        17       LO           BND          y[0]     1.0               NaN    18
        18       LO           BND          y[1]     1.0               NaN    19
        19       FX           BND  obj_constant    10.0               NaN    20
        20   ENDATA                                 0.0               0.0    21
        """
        ))

        u = m.add_variable(name='u')
        t = m.add_variable(name='t', vartype=so.BIN)
        m.drop_constraints(c1, c2)
        m.add_constraint(x + 2*y[0] == [3, 8], name='range_con')
        self.assertEqual(m.to_mps().to_string(), inspect.cleandoc(
        """
             Field1        Field2        Field3  Field4     Field5  Field6  _id_
        0      NAME                 test_to_mps     0.0                0.0     1
        1      ROWS                                 NaN                NaN     2
        2       MAX    o_constant                   NaN                NaN     3
        3         E     range_con                   NaN                NaN     4
        4   COLUMNS                                 NaN                NaN     5
        5                MARK0000      'MARKER'     NaN   'INTORG'     NaN     6
        6                       x    o_constant     1.0  range_con     1.0     7
        7                MARK0001      'MARKER'     NaN   'INTEND'     NaN     8
        8                    y[0]     range_con     2.0                NaN     9
        9                    y[1]    o_constant     0.0                NaN    10
        10           obj_constant    o_constant     1.0                NaN    11
        11                      u    o_constant     0.0                NaN    12
        12                      t    o_constant     0.0                NaN    13
        13      RHS                                 NaN                NaN    14
        14                    RHS     range_con     3.0                NaN    15
        15   RANGES                                 NaN                NaN    16
        16                    rng     range_con     5.0                NaN    17
        17   BOUNDS                                 NaN                NaN    18
        18       LO           BND             x     0.0                NaN    19
        19       UP           BND             x     5.0                NaN    20
        20       LO           BND          y[0]     1.0                NaN    21
        21       LO           BND          y[1]     1.0                NaN    22
        22       FX           BND  obj_constant    10.0                NaN    23
        23       FR           BND             u     NaN                NaN    24
        24       BV           BND             t     1.0                NaN    25
        25   ENDATA                                 0.0                0.0    26
        """
        ))

        def get_frame_warning():
            r = m.to_frame()
        self.assertWarns(DeprecationWarning, get_frame_warning)

    def test_to_optmodel(self):
        m = so.Model(name='test_to_optmodel')
        self.assertEqual(m.to_optmodel(), inspect.cleandoc(
            """
            proc optmodel;
               min test_to_optmodel_obj = 0;
               solve;
            quit;
            """
        ))
        x = m.add_variable(name='x', init=5)
        e1 = m.set_objective(x, sense=so.MIN, name='e1')
        e2 = m.append_objective(x**2, sense=so.MAX, name='e2')
        response = m.to_optmodel(options={
            'with': 'blackbox',
            'relaxint': True,
            'obj': (e1, e2),
            'primalin': True,
        }, ods=True, primalin=True, parse=False)
        self.assertEqual(response, inspect.cleandoc(
            """
            proc optmodel;
               var x init 5;
               min e1 = x;
               max e2 = (x) ^ (2);
               solve with blackbox relaxint obj (e1 e2) / primalin;
               ods output PrintTable=primal_out;
               ods output PrintTable=dual_out;
               create data allsols from [s]=(1.._NVAR_) name=_VAR_[s].name {j in 1.._NSOL_} <col('sol_'||j)=_VAR_[s].sol[j]>;
            quit;
            """
        ))

        response = m.to_optmodel(options={
            'with': 'nlp',
            'multistart': {'loglevel': 3, 'maxstarts': 30}
        })
        self.assertEqual(response, inspect.cleandoc(
            """
            proc optmodel;
               var x init 5;
               min e1 = x;
               max e2 = (x) ^ (2);
               solve with nlp / multistart=(loglevel=3,maxstarts=30);
            quit;
            """
        ))

    def test_str(self):
        m = TestModel.get_standard_model(name='test_model_str')

        response = str(m)
        self.assertEqual(response, inspect.cleandoc(
            """
            Model: [
              Name: test_model_str
              Objective: MIN [0]
              Variables (3): [
                x
                y[0]
                y[1]
              ]
              Constraints (3): [
                x <=  5
                y[0] <=  3
                y[1] <=  3
              ]
            ]
            """
        ))
        if TestModel.conn:
            m.set_session(TestModel.conn)
            response = str(m)
            self.assertEqual(response, inspect.cleandoc(
                """
                Model: [
                  Name: test_model_str
                  Session: {}:{}
                  Objective: MIN [0]
                  Variables (3): [
                    x
                    y[0]
                    y[1]
                  ]
                  Constraints (3): [
                    x <=  5
                    y[0] <=  3
                    y[1] <=  3
                  ]
                ]
                """.format(os.environ.get('CASHOST'), os.environ.get('CASPORT'))
            ))

    def test_model_repr(self):
        m = so.Model(name='test_model_repr')
        self.assertEqual(repr(m), "sasoptpy.Model(name='test_model_repr')")
        s = SASsession(cfgname='winlocal')
        m.set_session(s)
        self.assertEqual(
            repr(m),
            "sasoptpy.Model(name='test_model_repr', "
            "session=saspy.SASsession(cfgname='winlocal'))")

        if TestModel.conn:
            m.set_session(TestModel.conn)
            cas_repr = repr(m.get_session())
            self.assertEqual(
                repr(m), "sasoptpy.Model(name='test_model_repr', session=" +
                cas_repr + ')')

        def invalid_session_type():
            w = 5
            m.set_session(w)
            rp = repr(m)
        self.assertRaises(TypeError, invalid_session_type)

    def test_defn(self):
        m = TestModel.get_standard_model('test_model_defn')
        self.assertEqual(so.to_definition(m), "problem test_model_defn "
                                              "include x y c1 c2;")

    def test_expr(self):
        m = TestModel.get_standard_model('test_model_expr')
        self.assertEqual(m.to_optmodel(), so.to_expression(m))

    def test_is_linear(self):
        m = TestModel.get_standard_model('test_model_linearity')
        self.assertEqual(so.is_linear(m), True)
        x = m.get_variable('x')
        qbound = m.add_constraint(x ** 2 + x <= 10, name='qbound')
        self.assertEqual(so.is_linear(m), False)
        m.drop_constraint(qbound)
        self.assertEqual(so.is_linear(m), True)
        m.set_objective(x ** 2, sense=so.MIN, name='x_squared')
        self.assertEqual(so.is_linear(m), False)

    def test_session_type(self):
        m = TestModel.get_standard_model('test_model_session_type')
        self.assertEqual(m.get_session_type(), None)
        if TestModel.conn:
            m.set_session(TestModel.conn)
            self.assertEqual(m.get_session_type(), 'CAS')

    def test_ub_set(self):
        m = so.Model(name='test_model_var_ub')
        x = m.add_variable(name='x')
        self.assertEqual(so.to_optmodel(m), cleandoc('''
            proc optmodel;
               min test_model_var_ub_obj = 0;
               var x;
               solve;
            quit;'''))
        x.set_bounds(ub=5)
        self.assertEqual(so.to_optmodel(m), cleandoc('''
            proc optmodel;
               min test_model_var_ub_obj = 0;
               var x <= 5;
               solve;
            quit;'''))

    def test_model_add(self):
        m = so.Model(name='test_add')
        x = so.Variable(name='x')
        self.assertEqual(m.get_variables(), [])
        m.add(x)
        self.assertEqual(m.get_variables(), [x])

    def test_model_session(self):
        m = so.Model(name='m')
        s = m.get_session()
        self.assertEqual(s, None)
        if TestModel.conn:
            m.set_session(TestModel.conn)
            self.assertEqual(m.get_session(), TestModel.conn)
            self.assertEqual(m.get_session_type(), 'CAS')

    def test_names(self):
        if TestModel.conn is None:
            self.skipTest('Session is not available')

        m = so.Model(name='test_var_names', session=TestModel.conn)
        a = ['apple', 'apple juice']
        x = m.add_variables(a, name='amount', lb=1)
        m.set_objective(so.expr_sum(x[i] for i in a), name='obj', sense=so.minimize)

        m.solve()
        for i in a:
            self.assertEqual(x[i].get_value(), 1.0)

    def tearDown(self):
        so.reset()


