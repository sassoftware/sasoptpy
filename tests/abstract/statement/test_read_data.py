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


import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc
from sasoptpy.actions import read_data

from tests.swat_config import create_cas_connection


class TestReadData(unittest.TestCase):
    """
    Unit tests for READ DATA statements
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

    def test_read_regular_existing(self):

        from sasoptpy import Workspace, VariableGroup
        from sasoptpy.abstract import Set, ParameterGroup
        from sasoptpy.actions import solve

        with Workspace('test_workspace') as ws:

            ITEMS = Set(name='ITEMS')
            value = ParameterGroup(ITEMS, name='value', init=0)
            get = VariableGroup(ITEMS, name='get', vartype=so.INT, lb=0)

            read_data(
                table="values",
                index={'target': ITEMS, 'key': None},
                columns=[{'target': value}])

            solve(options={'with': so.BLACKBOX, 'maxgen': 10})

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               set ITEMS;
               num value {ITEMS} init 0;
               var get {{ITEMS}} integer >= 0;
               read data values into ITEMS value;
               solve with blackbox / maxgen=10;
            quit;
            """))

    def test_read_data_index(self):

        with so.Workspace('test_read_data_n') as ws:
            ASSETS = so.Set(name='ASSETS')
            ret = so.ParameterGroup(ASSETS, name='return', ptype=so.NUM)
            read_data(
                table='means',
                index={'target': ASSETS, 'key': so.N},
                columns=[{'target': ret}]
            )
        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               set ASSETS;
               num return {ASSETS};
               read data means into ASSETS=[_N_] return;
            quit;
            """))

    def test_read_data_no_index_expression(self):

        from sasoptpy.util import iterate

        with so.Workspace('test_read_data_no_index_expression') as ws:
            ASSETS = so.Set(name='ASSETS')
            cov = so.ParameterGroup(ASSETS, ASSETS, name='cov', init=0)
            with iterate(ASSETS, 'asset1') as asset1, iterate(ASSETS, 'asset2') as asset2:
                read_data(
                    table='covdata',
                    index={'key': [asset1, asset2]},
                    columns=[
                        {'target': cov},
                        {'target': cov[asset2, asset1],
                         'column': 'cov'}
                    ]
                )

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               set ASSETS;
               num cov {ASSETS, ASSETS} init 0;
               read data covdata into [asset1 asset2] cov cov[asset2, asset1]=cov;
            quit;
            """))

    def test_read_data_col(self):

        from sasoptpy.util import concat

        with so.Workspace('test_read_data_col') as ws:
            n = so.Parameter(name='n', init=2)
            indx = so.Set(name='indx', settype=['num'])
            p = so.ParameterGroup(indx, name='p')
            q = so.ParameterGroup(indx, name='q')

            read_data(
                table='exdata',
                index={
                    'target': indx,
                    'key': so.N
                },
                columns=[
                    {'target': p, 'column': 'column1'},
                    {'target': q, 'column': concat('column', n)}
                ]
            )

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               num n init 2;
               set indx;
               num p {indx};
               num q {indx};
               read data exdata into indx=[_N_] p=column1 q=col('column' || n);
            quit;
            """))

    def test_read_data_indexed_column(self):

        from sasoptpy.util import iterate, concat

        with so.Workspace(name='test_read_data_idx_col') as ws:
            dow = so.Set(name='DOW', value=so.exp_range(1, 6))
            locs = so.Set(name='LOCS', settype=so.STR)
            demand = so.ParameterGroup(locs, dow, name='demand')

            with iterate(locs, name='loc') as loc:
                r = read_data(
                    table='dmnd',
                    index={'target': locs, 'key': loc}
                )
                with iterate(dow, name='d') as d:
                    r.append({
                        'index': d,
                        'target': demand[loc, d],
                        'column': concat('day', d)
                    })

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               set DOW = 1..5;
               set <str> LOCS;
               num demand {LOCS, DOW};
               read data dmnd into LOCS=[loc] {d in DOW} < demand[loc, d]=col('day' || d) >;
            quit;"""))

    def test_with_cas_data(self):
        if TestReadData.conn is None:
            self.skipTest('No session is available')

        from sasoptpy.util import concat
        import pandas as pd
        df = pd.DataFrame([
            [1, 2], [3, 4]
        ], columns=['column1', 'column2'])

        s = TestReadData.conn
        exdata = s.upload_frame(df, casout='exdata')

        with so.Workspace('test_read_data_col', session=s) as ws:
            n = so.Parameter(name='n', init=2)
            indx = so.Set(name='indx', settype=['num'])
            p = so.ParameterGroup(indx, name='p')
            q = so.ParameterGroup(indx, name='q')

            read_data(
                table=exdata,
                index={
                    'target': indx,
                    'key': so.N
                },
                columns=[
                    {'target': p, 'column': 'column1'},
                    {'target': q, 'column': concat('column', n)}
                ]
            )

            from sasoptpy.actions import print_item
            print_item(p, q)

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               num n init 2;
               set indx;
               num p {indx};
               num q {indx};
               read data EXDATA into indx=[_N_] p=column1 q=col('column' || n);
               print p q;
            quit;
            """))

        ws.submit(verbose=True)
        self.assertEqual(ws.response['Print1.PrintTable'].to_string(), cleandoc(
            """
               COL1    p    q
            0   1.0  1.0  2.0
            1   2.0  3.0  4.0
            """
        ))

    def test_read_data_no_index_target(self):

        with so.Workspace('test_no_index_target') as ws:
            NODES = so.Set(name='NODES', settype=so.STR)
            nodesByPri = so.ParameterGroup(NODES, name='nodesByPri')

            read_data(table='temppri',
                      index={'key': so.N},
                      columns=[
                          {'target': nodesByPri, 'column': 'id'}
                      ])

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               set <str> NODES;
               num nodesByPri {NODES};
               read data temppri into [_N_] nodesByPri=id;
            quit;
            """))

    def test_read_data_same_name_cols(self):

        from sasoptpy.actions import set_objective, solve

        with so.Workspace('test_same_name_cols') as ws:
            x = so.Variable(name='x')
            y = so.Variable(name='y')
            c_xx = so.Parameter(name='c_xx')
            c_x = so.Parameter(name='c_x')
            c_y = so.Parameter(name='c_y')
            c_xy = so.Parameter(name='c_xy')
            c_yy = so.Parameter(name='c_yy')
            read_data(table='coeff',
                      index={},
                      columns=[
                          {'target': c_xx, 'column': 'c_xx'},
                          {'target': c_x},
                          {'column': 'c_y'},
                          {'target': c_xy, 'column': 'c_xy'},
                          {'target': c_yy}
                      ])
            set_objective(c_xx * x**2 + c_x * x + c_xy * x * y + c_yy * y**2,
                          name='z', sense=so.MIN)
            solve()

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               var x;
               var y;
               num c_xx;
               num c_x;
               num c_y;
               num c_xy;
               num c_yy;
               read data coeff into c_xx c_x c_y c_xy c_yy;
               MIN z = c_xx * (x) ^ (2) + c_x * x + c_xy * x * y + c_yy * (y) ^ (2);
               solve;
            quit;
            """))

    def test_read_data_var_bound(self):

        from sasoptpy.util import iterate

        with so.Workspace('test_read_data_var_bound') as ws:
            plants = so.Set(name='plants', settype=so.STR)
            prod = so.VariableGroup(plants, name='prod', lb=0)
            cost = so.Parameter(name='cost', ptype=so.NUM)
            p = so.SetIterator(plants, name='p')
            r = read_data(
                table='pdat',
                index={'target': plants, 'key': p},
                columns=[
                    {'target': prod[p].ub, 'column': 'maxprod'},
                    {'target': cost}
                ])

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               set <str> plants;
               var prod {{plants}} >= 0;
               num cost;
               read data pdat into plants=[p] prod[p].ub=maxprod cost;
            quit;
            """))

    def test_read_data_with_exp(self):

        with so.Workspace('test_read_data_with_exp') as ws:

            ss = so.Set(name='subscripts', value=so.exp_range(1, 5), settype=so.NUM)
            letter = so.ParameterGroup(ss, name='letter', ptype=so.STR)
            read_data(
                table='abcd',
                index={'key': so.N},
                columns=[
                    {'target': letter[5-so.N]}
                ]
            )

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               set subscripts = 1..4;
               str letter {subscripts};
               read data abcd into [_N_] letter[- _N_ + 5];
            quit;
            """))

    def test_read_data_append_later(self):

        from sasoptpy.util import concat, iterate

        with so.Workspace('let') as ws:
            actors = so.Set(name='ACTORS')
            actor_name = so.ParameterGroup(actors, ptype=so.STR,
                                           name='actor_name')
            daily_fee = so.ParameterGroup(actors, name='daily_fee')
            most_scenes = so.Parameter(name='most_scenes', value=9)
            scene_list = so.ParameterGroup(actors, so.exp_range(1, most_scenes),
                                           name='scene_list')

            r = read_data(
                table='scene',
                index={
                    'target': actors,
                    'key': so.N
                },
                columns=[
                    {
                        'target': actor_name,
                        'column': 'Actor'
                    },
                    {
                        'target': daily_fee,
                        'column': 'DailyFee'
                    }
                ]
            )
            with iterate(so.exp_range(1, most_scenes), name='j') as j:
                r.append({
                    'index': j,
                    'target': scene_list[so.N, j],
                    'column': concat('S_Var', j)
                })

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               set ACTORS;
               str actor_name {ACTORS};
               num daily_fee {ACTORS};
               num most_scenes = 9;
               num scene_list {ACTORS, 1..most_scenes};
               read data scene into ACTORS=[_N_] actor_name=Actor daily_fee=DailyFee {j in 1..most_scenes} < scene_list[_N_, j]=col('S_Var' || j) >;
            quit;
            """))

    def test_read_data_multi_index(self):

        with so.Workspace('test_read_data_multi_index') as ws:
            arcs = so.Set(name='ARCS', settype=[so.STR, so.STR])
            arc_lower = so.ParameterGroup(arcs, name='arcLower')
            arc_upper = so.ParameterGroup(arcs, name='arcUpper')
            arc_cost = so.ParameterGroup(arcs, name='arcCost')

            read_data(
                table='arcdata',
                index={
                    'target': arcs,
                    'key': ['_tail_', '_head_']
                },
                columns=[
                    {'target': arc_lower, 'column': '_lo_'},
                    {'target': arc_upper, 'column': '_capac_'},
                    {'target': arc_cost, 'column': '_cost_'}
                ]
            )

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               set <str, str> ARCS;
               num arcLower {ARCS};
               num arcUpper {ARCS};
               num arcCost {ARCS};
               read data arcdata into ARCS=[_tail_ _head_] arcLower=_lo_ arcUpper=_capac_ arcCost=_cost_;
            quit;
            """))

    def test_read_data_single_col(self):

        from sasoptpy.util import concat, iterate

        with so.Workspace('test_read_data_single_col') as ws:
            daily_employee_slots = so.Set(
                name='DailyEmployeeSlots', settype=[so.STR, so.NUM])
            weekdays = so.Set(
                name='WeekDays', value=['mon', 'tue', 'wed', 'thu', 'fri'])
            preference_weights = so.ParameterGroup(
                daily_employee_slots, weekdays, name='PreferenceWeights')

            with iterate(daily_employee_slots, name=['name', 'slot']) as keys:
                r = read_data(
                    table='preferences',
                    index={
                        'target': daily_employee_slots,
                        'key': keys
                    }
                )
                with iterate(weekdays, name='day') as day:
                    r.append({
                        'index': day,
                        'target': preference_weights[keys['name'], keys['slot'], day],
                        'column': day
                    })

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
            proc optmodel;
               set <str, num> DailyEmployeeSlots;
               set WeekDays = {'mon','tue','wed','thu','fri'};
               num PreferenceWeights {DailyEmployeeSlots, WeekDays};
               read data preferences into DailyEmployeeSlots=[name slot] {day in WeekDays} < PreferenceWeights[name, slot, day]=col(day) >;
            quit;
            """))

    def test_read_data_N_in_index(self):

        from sasoptpy.util import concat

        with so.Workspace('read_data_N_as_index') as ws:
            tasks = so.Set(name='TASKS', value=so.exp_range(1, 25))
            machines = so.Set(name='MACHINES', value=so.exp_range(1, 9))
            profit = so.ParameterGroup(machines, tasks, name='profit')
            j = so.SetIterator(tasks, name='j')
            read_data(
                table='profit_data',
                index={'key': so.N},
                columns=[
                    {'index': j, 'target': profit[so.N, j], 'column': concat('p', j)}
                ]
            )

        self.assertEqual(so.to_optmodel(ws), cleandoc("""
            proc optmodel;
               set TASKS = 1..24;
               set MACHINES = 1..8;
               num profit {MACHINES, TASKS};
               read data profit_data into [_N_] {j in TASKS} < profit[_N_, j]=col('p' || j) >;
            quit;
            """))

    def test_with_model(self):

        m = so.Model(name='m')
        ITEMS = m.add_set(name='ITEMS')
        value = m.add_parameter(ITEMS, name='value', init=0)
        weight = m.add_parameter(ITEMS, name='weight')
        limit = m.add_parameter(ITEMS, name='limit')
        get = m.add_variables(ITEMS, name='get', vartype=so.INT, lb=0)
        m.set_objective(so.expr_sum(get[i] for i in ITEMS), name='max_get', sense=so.MAX)

        m.include(read_data(table='values', index={'target': ITEMS, 'key': None},
                            columns=[value, weight, limit]))

        self.assertEqual(
            so.to_optmodel(m, options={'with': so.BLACKBOX, 'maxgen': 10}),
            cleandoc('''
            proc optmodel;
               set ITEMS;
               num value {{ITEMS}} init 0;
               num weight {{ITEMS}};
               num limit {{ITEMS}};
               var get {{ITEMS}} integer >= 0;
               max max_get = sum {i in ITEMS} (get[i]);
               read data values into ITEMS value weight limit;
               solve with blackbox / maxgen=10;
            quit;'''))


    def tearDown(self):
        pass
