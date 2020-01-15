
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
    """
    Reads data tables inside Set and Parameter objects

    Parameters
    ----------
    table : string or :class:`swat.cas.table.CASTable`
        Table object or name to be read, case insensitive
    index : dict
        Index properties of the table
        Has two main members:

        - target : :class:`sasoptpy.abstract.Set`
            Target Set object to be read into
        - key : string, list or None
            Column name that will be read from
            For multiple indices it should be a list of string or
            :class:`sasoptpy.abstract.SetIterator` objects

        For a given Set `YEAR` and column name `year_no`, the index dictionary
        should be written as:

        >>> {'target': YEAR, 'key': 'year_no'}

        If index is simply the row number, use `'key': so.N` which is equivalent
        to special `_N_` character at SAS language.
    columns : list
        A list of dictionaries, each holding column properties
        Columns are printed in given order. Each column should be represented as
        a dictionary with following fields:

        - target : :class:`sasoptpy.abstract.ParameterGroup`
            Target parameter object to be read into
        - column : string
            Column name to be read from
        - index : :class:`sasoptpy.SetIterator`, optional
            Sub-index for specific column, needed for complex operations

        If the name of the :class:`sasoptpy.abstract.Parameter` object is same
        as the column name, calling

        >>> p = so.Parameter(name='price')
        >>> read_data(..., columns=[{'target': p}])

        is enough. For reading a different column name, `column` field should be
        given:

        >>> {'target': p, 'column': 'price_usd'}

        When working with Parameter Group objects, sometimes a secondary loop is
        needed. This is achieved by using `index` field, along with
        :meth:`sasoptpy.abstract.statement.ReadDataStatement.append` method.

    Returns
    -------
    r : :class:`sasoptpy.abstract.statement.ReadDataStatement`
        Read data statement object, that includes all properties

        Additional columns can be added using
        :meth:`sasoptpy.abstract.statement.ReadDataStatement.append`
        function.

    Examples
    --------

    Reading a regular set

    >>> with Workspace('test_workspace') as ws:
    >>>     ITEMS = Set(name='ITEMS')
    >>>     value = ParameterGroup(ITEMS, name='value', init=0)
    >>>     get = VariableGroup(ITEMS, name='get', vartype=so.INT, lb=0)
    >>>     read_data(
    ...         table="values",
    ...         index={'target': ITEMS, 'key': None},
    ...         columns=[{'target': value}])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set ITEMS;
        num value {ITEMS} init 0;
        var get {{ITEMS}} integer >= 0;
        read data values into ITEMS value;
    quit;

    Reading with row index

    >>> with so.Workspace('test_read_data_n') as ws:
    >>>     ASSETS = so.Set(name='ASSETS')
    >>>     ret = so.ParameterGroup(ASSETS, name='return', ptype=so.NUM)
    >>>     read_data(
    ...         table='means',
    ...         index={'target': ASSETS, 'key': so.N},
    ...         columns=[{'target': ret}]
    ...     )
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set ASSETS;
        num return {ASSETS};
        read data means into ASSETS=[_N_] return;
    quit;

    Reading with no index set and subindex

    >>> with so.Workspace('test_read_data_no_index_expression') as ws:
    >>>     ASSETS = so.Set(name='ASSETS')
    >>>     cov = so.ParameterGroup(ASSETS, ASSETS, name='cov', init=0)
    >>>     with iterate(ASSETS, 'asset1') as asset1, iterate(ASSETS, 'asset2') as asset2:
    >>>         read_data(
    ...             table='covdata',
    ...             index={'key': [asset1, asset2]},
    ...             columns=[
    ...                 {'target': cov},
    ...                 {'target': cov[asset2, asset1],
    ...                 'column': 'cov'}])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set ASSETS;
        num cov {ASSETS, ASSETS} init 0;
        read data covdata into [asset1 asset2] cov cov[asset2, asset1]=cov;
    quit;

    Reading a column with multiple indices

    >>> with so.Workspace(name='test_read_data_idx_col') as ws:
    >>>     dow = so.Set(name='DOW', value=so.exp_range(1, 6))
    >>>     locs = so.Set(name='LOCS', settype=so.STR)
    >>>     demand = so.ParameterGroup(locs, dow, name='demand')
    >>>     with iterate(locs, name='loc') as loc:
    >>>         r = read_data(
    ...             table='dmnd',
    ...             index={'target': locs, 'key': loc}
    ...         )
    >>>         with iterate(dow, name='d') as d:
    >>>             r.append({
    ...                 'index': d,
    ...                 'target': demand[loc, d],
    ...                 'column': concat('day', d)
    ...             })
    >>> optmodel_code = so.to_optmodel(ws)
    proc optmodel;
        set DOW = 1..5;
        set <str> LOCS;
        num demand {LOCS, DOW};
        read data dmnd into LOCS=[loc] {d in DOW} < demand[loc, d]=col('day' || d) >;
    quit;

    See also
    --------
    :class:`tests.abstract.statement.test_read_data.TestReadData`

    """
    return sasoptpy.abstract.ReadDataStatement(table, index, columns)


@sasoptpy.containable(standalone=False)
def create_data(table, index, columns):
    """
    Creates data tables from variables, parameters and expressions

    Parameters
    ----------
    table : string
        Name of the table to be created
    index : dict
        Table index properties

        This dictionary can be empty if no index is needed. It can have
        following fields:

        - key : list
            List of index keys. Keys can be string or
            :class:`sasoptpy.abstract.SetIterator` objects
        - set : list
            List of sets, that is being assigned to keys
    columns : list
        List of columns. Columns can be :class:`sasoptpy.abstract.Parameter`,
        :class:`sasoptpy.abstract.ParameterGroup` objects or dictionaries. If
        given as a dictionary, each can have following keys:

        - name : string
            Name of the column in output table
        - expression : :class:`sasoptpy.core.Expression`
            Any expression
        - index : list or :class:`sasoptpy.abstract.SetIterator`
            Index for internal loops

        The `index` field can be used when a subindex is needed. When given as
        a list, members should be :class:`sasoptpy.abstract.SetIterator`
        objects. See examples for more details.

    Examples
    --------

    Regular column

    >>> with so.Workspace('w') as w:
    >>>     m = so.Parameter(name='m', value=7)
    >>>     n = so.Parameter(name='n', value=5)
    >>>     create_data(table='example', index={}, columns=[m, n])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        num m = 7;
        num n = 5;
        create data example from m n;
    quit;

    Column with name

    >>> with so.Workspace('w') as w:
    >>>     m = so.Parameter(name='m', value=7)
    >>>     n = so.Parameter(name='n', value=5)
    >>>     create_data(table='example', index={}, columns=[
    ...         {'name': 'ratio', 'expression': m/n}
    ...     ])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        num m = 7;
        num n = 5;
        create data example from ratio=((m) / (n));
    quit;

    Column name with concat

    >>> from sasoptpy.util import concat
    >>> with so.Workspace('w') as w:
    >>>     m = so.Parameter(name='m', value=7)
    >>>     n = so.Parameter(name='n', value=5)
    >>>     create_data(table='example', index={}, columns=[
    ...         {'name': concat('s', n), 'expression': m+n}
    ...     ])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        num m = 7;
        num n = 5;
        create data example from col('s' || n)=(m + n);
    quit;

    Table with index

    >>> with so.Workspace('w') as w:
    >>>     m = so.ParameterGroup(
    >>>         so.exp_range(1, 6), so.exp_range(1, 4), name='m', init=0)
    >>>     m[1, 1] = 1
    >>>     m[4, 1] = 1
    >>>     S = so.Set(name='ISET', value=[i**2 for i in range(1, 3)])
    >>>     create_data(
    ...         table='example',
    ...         index={'key': ['i', 'j'], 'set': [S, [1, 2]]},
    ...         columns=[m]
    ...     )
    >>> print(so.to_optmodel(w))
    proc optmodel;
        num m {1..5, 1..3} init 0;
        m[1, 1] = 1;
        m[4, 1] = 1;
        set ISET = {1,4};
        create data example from [i j] = {{ISET,{1,2}}} m;
    quit;

    Index over Python range

    >>> with so.Workspace('w') as w:
    >>>     s = so.Set(name='S', value=so.exp_range(1, 6))
    >>>     x = so.VariableGroup(s, name='x')
    >>>     x[1] = 1
    >>>     create_data(table='example',
    ...         index={'key': ['i'], 'set': so.exp_range(1, 4)}, columns=[x])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set S = 1..5;
        var x {{S}};
        x[1] = 1;
        create data example from [i] = {1..3} x;
    quit;

    Append column with index

    >>> from sasoptpy.util import iterate, concat
    >>> with so.Workspace('w', session=session) as w:
    >>>     alph = so.Set(name='alph', settype=so.string, value=['a', 'b', 'c'])
    >>>     x = so.VariableGroup([1, 2, 3], alph, name='x', init=2)
    >>>     with iterate(so.exp_range(1, 4), name='i') as i:
    >>>         c = create_data(
    ...             table='example',
    ...             index={'key': [i], 'set': [i.get_set()]})
    >>>         with iterate(alph, name='j') as j:
    >>>             c.append(
    ...                 {'name': concat('x', j),
    ...                  'expression': x[i, j],
    ...                  'index': j})
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set <str> alph = {'a','b','c'};
        var x {{1,2,3}, {alph}} init 2;
        create data example from [i] = {{1..3}} {j in alph} < col('x' || j)=(x[i, j]) >;
    quit;

    Multiple column indices

    >>> from sasoptpy.util import concat, iterate
    >>> with so.Workspace('w') as w:
    >>>     S = so.Set(name='S', value=[1, 2, 3])
    >>>     T = so.Set(name='T', value=[1, 3, 5])
    >>>     x = so.VariableGroup(S, T, name='x', init=1)
    >>>     with iterate(S, name='i') as i, iterate(T, name='j') as j:
    >>>         create_data(
    ...             table='out',
    ...             index={},
    ...             columns=[
    ...                 {'name': concat('x', concat(i, j)), 'expression': x[i, j],
    ...                  'index': [i, j]}])
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set S = {1,2,3};
        set T = {1,3,5};
        var x {{S}, {T}} init 1;
        create data out from {i in S, j in T} < col('x' || i || j)=(x[i, j]) >;
    quit;

    See also
    --------
    :class:`tests.abstract.statement.test_create_data.TestCreateData`

    """
    pass


@sasoptpy.containable(standalone=False)
def solve(options=None, primalin=False):
    """
    Solves the active optimization problem and generates results

    Parameters
    ----------
    options : dict, optional
        Solver options

        This dictionary can have several fields. Notably:

        - with : string
            Name of the solver, possible values are

            - `lp` : Linear programming
            - `milp` : Mixed integer linear programming
            - `nlp` : General nonlinear programming
            - `qp` : Quadratic programming
            - `blackbox` : Black-box optimization

            SAS Optimization also has Constraint Programming (clp) and Network
            Solver (network) but they are not currently supported.
        - 

    primalin : bool, optional
        Switch for using existing variable values as an initial point in MILP
        solver

    :param options:
    :param primalin:
    :return:
    """
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
