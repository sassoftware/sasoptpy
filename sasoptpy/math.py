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

'''
Math includes the definition of mathematical operations

'''

import sasoptpy.utils

def sin(exp):
    try:
        exp = sasoptpy.utils.get_mutable(exp)
        exp._operator = 'sin'
        return exp
    except AttributeError:
        print('ERROR: sin function can only be used with Expression objects.')
