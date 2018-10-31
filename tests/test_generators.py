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

import unittest
import os
import sasoptpy
import tests.responses as expected
import hashlib
hash = hashlib.sha256


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


class TestGenerators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = MockCASServer()

    def tearDown(self):
        sasoptpy.reset_globals()

    def test_fm1(self):
        from examples.food_manufacture_1 import test
        st = test(TestGenerators.server, solve=False)
        print(hash(st))
        #print('***', st, '***')
        #print('***', expected.fm1, '***')
        #self.assertMultiLineEqual(st, expected.fm1)

if __name__ == '__main__':
    unittest.main()
