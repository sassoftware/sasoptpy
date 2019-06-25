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

import sys
import unittest
import tests.responses as expected
import sasoptpy as so
import hashlib


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
        pass


def mock_solve(model, *args, **kwargs):
    """
    Overrides :meth:`Model.solve` method to be used in unittests.

    Parameters
    ----------
    model : :class:`Model` object
        Model to be used in unittest
    args
        Arguments
    kwargs
        Keyword arguments
    ctr : integer
        Counter for the multi-response tests
    expected : list
        List of hash values of the generated OPTMODEL strings

    Returns
    -------
    boolean
        Success (True) or Failure (False) for the current test
    """
    global ctr
    global expected_response
    global tests
    global records
    success = True
    print('Mock solve is called!')
    if 'verbose' in kwargs:
        del kwargs['verbose']
    optmodel_code = model.to_optmodel(**kwargs)
    obtained = hashlib.sha256(optmodel_code.encode()).hexdigest()
    records.append(obtained)
    if obtained == expected_response[ctr]:
        print('Success!', obtained, expected_response[ctr])
    else:
        success = False
        print('Failed!')
        print(obtained, expected_response[ctr])
    ctr += 1
    tests.append(success)
    return success


class TestGenerators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = MockCASServer()

    def setUp(self):
        self.old_stdout = sys.stdout
        sys.stdout = NullWriter()
        sys.stderr = NullWriter()

    def tearDown(self):
        so.reset()

    def check_results(self):
        sys.stdout = self.old_stdout
        print('Problem:', self.problem)
        for i, v in enumerate(self.results):
            print('Model', i, v, records[i])
            self.assertTrue(v)

    def set_expectation(self, problem, test):
        global ctr
        global expected_response
        global tests
        global records
        ctr = 0
        expected_response = test
        self.results = tests = []
        self.problem = problem
        self.records = records = []

    def test_fm1(self):
        self.set_expectation('Food Manufacture 1', expected.fm1)
        from examples.food_manufacture_1 import test
        test(TestGenerators.server)
        self.check_results()

    def test_fm2(self):
        self.set_expectation('Food Manufacture 2', expected.fm2)
        from examples.food_manufacture_2 import test
        test(TestGenerators.server)
        self.check_results()

    def test_fp1(self):
        self.set_expectation('Factory Planning 1', expected.fp1)
        from examples.factory_planning_1 import test
        test(TestGenerators.server)
        self.check_results()

    def test_fp2(self):
        self.set_expectation('Factory Planning 2', expected.fp2)
        from examples.factory_planning_2 import test
        test(TestGenerators.server)
        self.check_results()

    def test_mp(self):
        self.set_expectation('Manpower Planning', expected.mp)
        from examples.manpower_planning import test
        test(TestGenerators.server)
        self.check_results()

    def test_ro(self):
        self.set_expectation('Refinery Optimization', expected.ro)
        from examples.refinery_optimization import test
        test(TestGenerators.server)
        self.check_results()

    def test_mo(self):
        self.set_expectation('Mining Optimization', expected.mo)
        from examples.mining_optimization import test
        try:
            test(TestGenerators.server)
        except ZeroDivisionError:
            pass
        self.check_results()

    def test_farmp(self):
        self.set_expectation('Farm Planning', expected.farmp)
        from examples.farm_planning import test
        test(TestGenerators.server)
        self.check_results()

    def test_econ(self):
        self.set_expectation('Economic Planning', expected.econ)
        from examples.economic_planning import test
        test(TestGenerators.server)
        self.check_results()

    def test_dc(self):
        self.set_expectation('Decentralization', expected.dc)
        from examples.decentralization import test
        test(TestGenerators.server)
        self.check_results()

    def test_ow(self):
        self.set_expectation('Optimal Wedding', expected.ow)
        from examples.sas_optimal_wedding import test
        test(TestGenerators.server)
        self.check_results()

    def test_kx(self):
        self.set_expectation('Kidney Exchange', expected.kx)
        from examples.sas_kidney_exchange import test
        test(TestGenerators.server)
        self.check_results()

    def test_multiobj(self):
        self.set_expectation('Multiobjective', expected.multiobj)
        from examples.multiobjective import test
        test(TestGenerators.server)
        self.check_results()

    #def test_cf(self):
    #    self.set_expectation('Curve Fitting', expected.cf)
    #    from examples.curve_fitting import test
    #    test(TestGenerators.server)
    #    self.check_results()

    def test_nl1(self):
        self.set_expectation('Nonlinear 1', expected.nl1)
        from examples.nonlinear_1 import test
        try:
            test(TestGenerators.server)
        except ZeroDivisionError:
            pass
        self.check_results()

    def test_nl2(self):
        self.set_expectation('Nonlinear 2', expected.nl2)
        from examples.nonlinear_2 import test
        test(TestGenerators.server)
        self.check_results()

if __name__ == '__main__':
    globals()['so'].Model.solve = mock_solve
    unittest.main()


