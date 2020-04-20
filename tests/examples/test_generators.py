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
This test file generates intermediate forms to run optimization models using SAS/OR or SAS Viya Optimization solvers.
"""

import os
import sys
import unittest
import tests.examples.responses as expected
import sasoptpy as so
import hashlib

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../../examples/client_side')))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../../examples/server_side')))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

from util import get_generic_form


class NullWriter:
    """
    Imitates system writer to hide print statements.
    """

    def write(self, text): pass

    def flush(self): pass


class MockCASServer:
    """
    Represents CAS Server for unit tests.
    """

    def __init__(self):
        pass

    def upload_frame(self, *args, **kwargs):
        try:
            return kwargs.get('casout').get('name').upper()
        except IndexError:
            pass


def mock_solve(model, **kwargs):
    """
    Overrides :meth:`Model.solve` method to be used in unittests.

    Parameters
    ----------
    model : :class:`Model` object
        Model to be used in unittest
    kwargs
        Keyword arguments

    Returns
    -------
    boolean
        Success (True) or Failure (False) for the current test
    """
    global ctr
    global expected_response
    global records
    if 'verbose' in kwargs:
        del kwargs['verbose']
    optmodel_code = model.to_optmodel(**kwargs)
    records.append([optmodel_code, expected_response[ctr]])
    ctr += 1
    if so.core.util.is_model(model):
        if model._objval is None:
            model.set_objective_value(0)
    return None


class TestGenerators(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = MockCASServer()
        global real_solve
        global real_submit
        global realstdout
        real_solve = so.Model.solve
        real_submit = so.Workspace.submit
        globals()['so'].Model.solve = mock_solve
        globals()['so'].Workspace.submit = mock_solve
        realstdout = sys.stdout
        unittest.util._MAX_LENGTH = 1e+6

    def setUp(self):
        #sys.stdout = NullWriter()
        self.maxDiff = None

    def tearDown(self):
        so.reset()

    def check_results(self):
        sys.stdout = realstdout
        print('Problem:', self.problem)
        for i, solve in enumerate(self.records):
            string0 = get_generic_form(solve[0])
            string1 = get_generic_form(solve[1])
            self.assertMultiLineEqual(string0, string1, string0)
            print('Solve', i, ': True')

    def set_expectation(self, problem, test):
        global ctr
        global expected_response
        global records
        ctr = 0
        expected_response = test
        self.problem = problem
        self.records = records = []


    def test_fm1(self):
        self.set_expectation('Food Manufacture 1', expected.fm1)
        from food_manufacture_1 import test
        test(TestGenerators.server)
        self.check_results()

    def test_fm2(self):
        self.set_expectation('Food Manufacture 2', expected.fm2)
        from food_manufacture_2 import test
        test(TestGenerators.server)
        self.check_results()

    def test_fp1(self):
        self.set_expectation('Factory Planning 1', expected.fp1)
        from factory_planning_1 import test
        test(TestGenerators.server)
        self.check_results()

    def test_fp2(self):
        self.set_expectation('Factory Planning 2', expected.fp2)
        from factory_planning_2 import test
        test(TestGenerators.server)
        self.check_results()

    def test_mp(self):
        self.set_expectation('Manpower Planning', expected.mp)
        from manpower_planning import test
        test(TestGenerators.server)
        self.check_results()

    def test_ro(self):
        self.set_expectation('Refinery Optimization', expected.ro)
        from refinery_optimization import test
        test(TestGenerators.server)
        self.check_results()

    def test_mo(self):
        self.set_expectation('Mining Optimization', expected.mo)
        from mining_optimization import test
        try:
            test(TestGenerators.server)
        except ZeroDivisionError:
            pass
        self.check_results()

    def test_farmp(self):
        self.set_expectation('Farm Planning', expected.farmp)
        from farm_planning import test
        test(TestGenerators.server)
        self.check_results()

    def test_econ(self):
        self.set_expectation('Economic Planning', expected.econ)
        from economic_planning import test
        test(TestGenerators.server)
        self.check_results()

    def test_dc(self):
        self.set_expectation('Decentralization', expected.dc)
        from decentralization import test
        test(TestGenerators.server)
        self.check_results()

    def test_ow(self):
        self.set_expectation('Optimal Wedding', expected.ow)
        from sas_optimal_wedding import test
        test(TestGenerators.server)
        self.check_results()

    def test_kx(self):
        self.set_expectation('Kidney Exchange', expected.kx)
        from sas_kidney_exchange import test
        test(TestGenerators.server)
        self.check_results()

    def test_multiobj(self):
        self.set_expectation('Multiobjective', expected.multiobj)
        from multiobjective import test
        test(TestGenerators.server)
        self.check_results()

    def test_cf(self):
        so.reset()
        self.set_expectation('Curve Fitting', expected.cf)
        from curve_fitting import test
        test(TestGenerators.server)
        self.check_results()

    def test_nl1(self):
        self.set_expectation('Nonlinear 1', expected.nl1)
        from nonlinear_1 import test
        try:
            test(TestGenerators.server)
        except ZeroDivisionError:
            pass
        self.check_results()

    def test_nl2(self):
        self.set_expectation('Nonlinear 2', expected.nl2)
        from nonlinear_2 import test
        test(TestGenerators.server)
        self.check_results()

    def test_least_squares(self):
        self.set_expectation('Least Squares', expected.least_squares)
        from least_squares import test
        test(TestGenerators.server)
        self.check_results()

    def test_efficiency_analysis(self):
        self.set_expectation('Efficiency Analysis', expected.efficiency_analysis)
        from efficiency_analysis import test
        test(TestGenerators.server)
        self.check_results()

    @classmethod
    def tearDownClass(cls):
        global real_solve
        global real_submit
        globals()['so'].Model.solve = real_solve
        globals()['so'].Workspace.submit = real_submit


