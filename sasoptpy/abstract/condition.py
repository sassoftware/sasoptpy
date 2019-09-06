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
Condition for symbolic expressions
"""

import sasoptpy

class Condition:

    def __init__(self, left, c_type, right):
        self._left = left
        self._type = c_type
        self._right = right

    def _expr(self):
        left = sasoptpy.to_expression(self._left)
        right = sasoptpy.to_expression(self._right)
        return '{} {} {}'.format(left, self._type, right)
