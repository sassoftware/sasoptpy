
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
        cofor_loop, sasoptpy.abstract.statement.CoForLoopStatement.cofor_loop)
    register_to_function_container(
        if_condition, sasoptpy.abstract.statement.IfElseStatement.if_condition)
    register_to_function_container(
        switch_conditions, sasoptpy.abstract.statement.if_else.SwitchStatement.switch_condition)
    register_to_function_container(
        set_value, sasoptpy.abstract.statement.Assignment.set_value)
    register_to_function_container(
        fix, sasoptpy.abstract.statement.FixStatement.fix)
    register_to_function_container(
        unfix, sasoptpy.abstract.statement.UnfixStatement.unfix)
    register_to_function_container(
        set_objective, sasoptpy.abstract.statement.ObjectiveStatement.set_objective)
    register_to_function_container(
        print_item, sasoptpy.abstract.statement.PrintStatement.print_item)
    register_to_function_container(
        expand, sasoptpy.abstract.statement.LiteralStatement.expand)
    register_to_function_container(
        drop, sasoptpy.abstract.statement.DropStatement.drop_constraint)
    register_to_function_container(
        put_item, sasoptpy.abstract.statement.PrintStatement.put_item)
    register_to_function_container(
        union, sasoptpy.abstract.statement.LiteralStatement.union)
    register_to_function_container(
        diff, sasoptpy.abstract.statement.LiteralStatement.diff)
    register_to_function_container(
        substring, sasoptpy.abstract.statement.LiteralStatement.substring)
    register_to_function_container(
        use_problem, sasoptpy.abstract.statement.LiteralStatement.use_problem)


@sasoptpy.containable
def read_data(table, index, columns):
    return sasoptpy.abstract.ReadDataStatement(table, index, columns)


@sasoptpy.containable(standalone=False)
def create_data(**kwargs):
    pass


@sasoptpy.containable(standalone=False)
def solve(*args, **kwargs):
    pass


@sasoptpy.containable(standalone=False)
def for_loop(*args):
    pass


@sasoptpy.containable(standalone=False)
def cofor_loop(*args):
    pass


@sasoptpy.containable(standalone=False)
def if_condition(logic_expression, if_statement, else_statement=None):
    pass


@sasoptpy.containable(standalone=False)
def switch_conditions(**args):
    pass


@sasoptpy.containable(standalone=False)
def set_value(left, right):
    pass


@sasoptpy.containable(standalone=False)
def fix(*args):
    pass


@sasoptpy.containable(standalone=False)
def unfix(*args):
    pass


@sasoptpy.containable(standalone=False)
def set_objective(*args, name, sense):
    pass


@sasoptpy.containable(standalone=False)
def print_item(*args, **kwargs):
    pass


@sasoptpy.containable(standalone=False)
def put_item(*args, **kwargs):
    pass


@sasoptpy.containable(standalone=False)
def expand():
    pass


@sasoptpy.containable(standalone=False)
def drop(*args):
    pass


@sasoptpy.containable(standalone=False)
def union(*args):
    pass


@sasoptpy.containable(standalone=False)
def diff(*args):
    pass


@sasoptpy.containable(standalone=False)
def substring(main_string, first_pos, last_pos):
    pass


@sasoptpy.containable(standalone=False)
def use_problem(problem):
    pass


condition = sasoptpy.structure.under_condition
inline_condition = sasoptpy.structure.inline_condition
