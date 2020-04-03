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
from functools import wraps, partial
import warnings

import sasoptpy


def containable(func=None, standalone=True):
    if func is None:
        return partial(containable, standalone=standalone)

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not standalone and not sasoptpy.container:
            warnings.warn('This function is not intended to be used without any'
                          ' container', UserWarning)

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
                    append_to_container(st)
            else:
                append_to_container(statements)
            return statements
        else:
            return func(*args, **kwargs)
    return wrapper


def class_containable(func):
    def class_append(*args, **kwargs):
        is_internal = kwargs.pop('internal', None)
        func(*args, **kwargs)
        if sasoptpy.container and is_internal is None:
            sasoptpy.container.append(args[0])

    return class_append


def append_to_container(statement):
    if hasattr(statement, 'is_internal') and statement.is_internal():
        pass
    else:
        sasoptpy.container.append(statement)


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


def inline_condition(c):
    if sasoptpy.container_conditions:
        sasoptpy.container.sym.add_condition(c)
        return True
    return False


@contextmanager
def set_container(s, conditions=False):
    original = sasoptpy.container
    sasoptpy.container = s
    cond_original = None
    if conditions:
        cond_original = sasoptpy.container_conditions
        sasoptpy.container_conditions = True

    yield

    sasoptpy.container = original
    if conditions:
        sasoptpy.container_conditions = cond_original

