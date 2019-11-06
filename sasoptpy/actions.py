
from contextlib import contextmanager

import sasoptpy
from sasoptpy.util import register_to_function_container


def register_actions():
    register_to_function_container(
        read_data, sasoptpy.abstract.statement.ReadDataStatement.read_data)
    register_to_function_container(
        create_data, sasoptpy.abstract.statement.CreateDataStatement.create_data)
    register_to_function_container(
        solve, sasoptpy.abstract.statement.SolveStatement.solve)
    register_to_function_container(
        for_loop, sasoptpy.abstract.statement.ForLoopStatement.for_loop)
    register_to_function_container(
        set_value, sasoptpy.abstract.statement.Assignment.set_value)
    register_to_function_container(
        set_objective, sasoptpy.abstract.statement.ObjectiveStatement.set_objective)
    register_to_function_container(
        print_item, sasoptpy.abstract.statement.PrintStatement.print_item)
    register_to_function_container(
        expand, sasoptpy.abstract.statement.LiteralStatement.expand)
    register_to_function_container(
        drop, sasoptpy.abstract.statement.DropStatement.drop_constraint)


@sasoptpy.containable
def read_data(**kwargs):
    return sasoptpy.abstract.ReadDataStatement(**kwargs)


@sasoptpy.containable
def create_data(**kwargs):
    pass


@sasoptpy.containable
def solve(*args, **kwargs):
    pass


@sasoptpy.containable
def for_loop(*args):
    pass


@sasoptpy.containable
def set_value(left, right):
    pass


@sasoptpy.containable
def set_objective(*args, name, sense):
    pass


@sasoptpy.containable
def print_item(*args, **kwargs):
    pass


@sasoptpy.containable
def expand():
    pass


@sasoptpy.containable
def drop(*args):
    pass


condition = sasoptpy.structure.under_condition
