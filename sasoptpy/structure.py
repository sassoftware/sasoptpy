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


from contextlib import contextmanager

import sasoptpy


def containable(func):
    def wrapper(*args, **kwargs):
        if sasoptpy.container:
            try:
                statement_func = sasoptpy.statement_dictionary[wrapper]
            except KeyError:
                raise NotImplementedError(
                    'Container support for {} is not implemented'.format(
                        func.__name__))
            statements = statement_func(*args, **kwargs)
            if isinstance(statements, list):
                for st in statements:
                    sasoptpy.container.append(st)
            else:
                sasoptpy.container.append(statements)
            return statements
        else:
            return func(*args, **kwargs)
    return wrapper


def class_containable(func):
    def class_append(*args, **kwargs):
        func(*args, **kwargs)
        if sasoptpy.container and not kwargs.get('internal'):
            sasoptpy.container.append(args[0])

    return class_append


@contextmanager
def under_condition(c):
    if type(c) == bool:
        yield c
        return True
    original = sasoptpy.conditions
    if original is None:
        sasoptpy.conditions = []
    sasoptpy.conditions = sasoptpy.conditions + [c]
    yield
    sasoptpy.conditions = original
