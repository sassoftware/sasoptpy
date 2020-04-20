
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
        restore, sasoptpy.abstract.statement.RestoreStatement.restore_constraint)
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
        Table object or name to be read, case-insensitive
    index : dict
        Index properties of the table

        Has two main members:

        - target : :class:`sasoptpy.abstract.Set`
            Target Set object to be read into
        - key : string, list or None
            Column name to be be read from.

            For multiple indices, key should be a list of string or
            :class:`sasoptpy.abstract.SetIterator` objects

        For a given set `YEAR` and column name `year_no`, the index dictionary
        should be written as:

        >>> {'target': YEAR, 'key': 'year_no'}

        If index is simply the row number, use `'key': so.N` which is equivalent
        to the special `_N_` character in the SAS language.
    columns : list
        A list of dictionaries, each holding column properties.

        Columns are printed in the specified order. Each column should be
        represented as a dictionary with following fields:

        - target : :class:`sasoptpy.abstract.ParameterGroup`
            Target parameter object to be read into
        - column : string
            Column name to be read from
        - index : :class:`sasoptpy.SetIterator`, optional
            Subindex for specific column, needed for complex operations

        If the name of the :class:`sasoptpy.abstract.Parameter` object is same
        as the column name, the following call is enough:

        >>> p = so.Parameter(name='price')
        >>> read_data(..., columns=[{'target': p}])

        For reading a different column name, `column` field should be
        specified:

        >>> {'target': p, 'column': 'price_usd'}

        When working with :class:`ParameterGroup` objects, sometimes a secondary
        loop is needed. This is achieved by using the `index` field, along with
        the :meth:`sasoptpy.abstract.statement.ReadDataStatement.append` method.

    Returns
    -------
    r : :class:`sasoptpy.abstract.statement.ReadDataStatement`
        Read data statement object, which includes all properties

        Additional columns can be added using the
        :meth:`sasoptpy.abstract.statement.ReadDataStatement.append`
        function.

    Examples
    --------

    Reading a regular set:

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

    Reading with row index:

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

    Reading with no index set and subindex:

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

    Reading a column with multiple indices:

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
    Creates data tables from variables, parameters, and expressions

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
            List of sets that is being assigned to keys
    columns : list
        List of columns. Columns can be :class:`sasoptpy.abstract.Parameter`,
        :class:`sasoptpy.abstract.ParameterGroup` objects or dictionaries. If
        specified as a dictionary, each can have following keys:

        - name : string
            Name of the column in output table
        - expression : :class:`sasoptpy.core.Expression`
            Any expression
        - index : list or :class:`sasoptpy.abstract.SetIterator`
            Index for internal loops

        The `index` field can be used when a subindex is needed. When
        specified as a list, members should be
        :class:`sasoptpy.abstract.SetIterator` objects.
        See examples for more details.

    Examples
    --------

    Regular column:

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

    Column with name:

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

    Column name with concat:

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

    Table with index:

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

    Index over Python range:

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

    Append column with index:

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

    Multiple column indices:

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

        This dictionary can have several fields.

        - with : string
            Name of the solver, see possible values under Notes.

        See :ref:`solver-options` for a list of solver options. All fields in
        options (except `with`) is passed directly to the solver.

    primalin : bool, optional
        When set to `True`, uses existing variable values as an initial point
        in MILP solver

    Notes
    -----

    Possible solver names for `with` parameter:

    * `lp` : Linear programming
    * `milp` : Mixed integer linear programming
    * `nlp` : General nonlinear programming
    * `qp` : Quadratic programming
    * `blackbox` : Black-box optimization

    SAS Optimization also has a constraint programming solver (clp), and network
    solver (network) but they are not currently supported by sasoptpy.

    Returns
    -------
    ss : :class:`sasoptpy.abstract.statement.SolveStatement`
        Solve statement object.

        Contents of the response can be retrieved using `get_response` function.

    Examples
    --------

    Regular solve:

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x', lb=1, ub=10)
    >>>     o = so.Objective(2*x, sense=so.maximize, name='obj')
    >>>     s = solve()
    >>>     p = print_item(x)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x >= 1 <= 10;
        max obj = 2 * x;
        solve;
        print x;
    quit;

    Option alternatives:

    >>> with so.Workspace('w') as w:
    >>>     # Problem declaration, etc..
    >>>     solve()
    >>>     solve(options={'with': 'milp'})
    >>>     solve(options={'with': 'milp'}, primalin=True)
    >>>     solve(options={'with': 'milp', 'presolver': None, 'feastol': 1e-6,
    >>>                    'logfreq': 2, 'maxsols': 3, 'scale': 'automatic',
    >>>                    'restarts': None, 'cutmir': 'aggressive'})
    >>> print(so.to_optmodel(w))
    proc optmodel;
        solve;
        solve with milp;
        solve with milp / primalin;
        solve with milp / presolver=None feastol=1e-06 logfreq=2 maxsols=3 scale=automatic restarts=None cutmir=aggressive;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def for_loop(*args):
    """
    Creates a for-loop container to be executed on the server

    Parameters
    ----------
    args : :class:`sasoptpy.abstract.Set` objects
        Any number of :class:`sasoptpy.abstract.Set` objects can be given

    Returns
    -------
    set_iterator : :class:`sasoptpy.abstract.SetIterator`, :class:`sasoptpy.abstract.SetIteratorGroup`
        Set iterators to be used inside for-loop

    Examples
    --------

    Regular for loop:

    >>> with so.Workspace('w') as w:
    >>>     r = so.exp_range(1, 11)
    >>>     x = so.VariableGroup(r, name='x')
    >>>     for i in for_loop(r):
    >>>         x[i] = 1
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x {{1,2,3,4,5,6,7,8,9,10}};
        for {o13 in 1..10} do;
            x[o13] = 1;
        end;
    quit;

    Nested for loops:

    >>> from sasoptpy.actions import put_item
    >>> with so.Workspace('w') as w:
    >>>     for i in for_loop(range(1, 3)):
    >>>         for j in for_loop(['a', 'b']):
    >>>             put_item(i, j)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        for {o2 in 1..2} do;
            for {o5 in {'a','b'}} do;
                put o2 o5;
            end;
        end;
    quit;

    Multiple set for-loops:

    >>> with so.Workspace('w') as w:
    >>>     r = so.Set(name='R', value=range(1, 11))
    >>>     c = so.Set(name='C', value=range(1, 6))
    >>>     a = so.ParameterGroup(r, c, name='A', ptype=so.number)
    >>>     for (i, j) in for_loop(r, c):
    >>>         a[i, j] = 1
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set R = 1..10;
        set C = 1..5;
        num A {R, C};
        for {o5 in R, o7 in C} do;
            A[o5, o7] = 1;
        end;
    quit;

    See also
    --------
    :func:`sasoptpy.actions.cofor_loop`

    Notes
    -----

    For tasks that can be run concurrently, consider using
    :func:`sasoptpy.actions.cofor_loop`

    """
    pass


@sasoptpy.containable(standalone=False)
def cofor_loop(*args):
    """
    Creates a cofor-loop to be executed on the server concurrently

    Parameters
    ----------
    args : :class:`sasoptpy.abstract.Set` objects
        Any number of :class:`sasoptpy.abstract.Set` objects can be specified

    Returns
    -------
    set_iterator : :class:`sasoptpy.abstract.SetIterator`, :class:`sasoptpy.abstract.SetIteratorGroup`
        Set iterators to be used inside cofor-loop

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     x = so.VariableGroup(6, name='x', lb=0)
    >>>     so.Objective(
    >>>         so.expr_sum(x[i] for i in range(6)), name='z', sense=so.MIN)
    >>>     a1 = so.Constraint(x[1] + x[2] + x[3] <= 4, name='a1')
    >>>     for i in cofor_loop(so.exp_range(3, 6)):
    >>>         fix(x[1], i)
    >>>         solve()
    >>>         put_item(i, x[1], so.Symbol('_solution_status_'), names=True)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x {{0,1,2,3,4,5}} >= 0;
        min z = x[0] + x[1] + x[2] + x[3] + x[4] + x[5];
        con a1 : x[1] + x[2] + x[3] <= 4;
        cofor {o13 in 3..5} do;
            fix x[1]=o13;
            solve;
            put o13= x[1]= _solution_status_=;
        end;
    quit;

    See also
    --------
    :func:`sasoptpy.actions.for_loop`

    Notes
    -----

    A cofor-loop runs its content concurrently. For tasks that depend on each
    other, consider using :func:`sasoptpy.actions.for_loop`
    """
    pass


@sasoptpy.containable(standalone=False)
def if_condition(logic_expression, if_statement, else_statement=None):
    """
    Creates an if-else block

    Parameters
    ----------
    logic_expression : :class:`sasoptpy.Constraint` or :class:`sasoptpy.abstract.Condition`
        Logical condition for the True case

        For the condition, it is possible to combine constraints, such as

        >>> a = so.Parameter(value=5)
        >>> if_condition((a < 3) | (a > 6), func1, func2)

        Constraints should be combined using bitwise operators
        (& for `and`, | for `or`).
    if_statement : function or :class:`IfElseStatement`
        Python function or if-else statement to be called if the condition is True
    else_statement : function or :class:`IfElseStatement`, optional
        Python function or if-else statement to be called if the condition is False

    Examples
    --------

    Regular condition:

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x')
    >>>     x.set_value(0.5)
    >>>     def func1():
    >>>         x.set_value(1)
    >>>     def func2():
    >>>         x.set_value(0)
    >>>     if_condition(x > 1e-6, func1, func2)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x;
        x = 0.5;
        if x > 1e-06 then do;
            x = 1;
        end;
        else do;
            x = 0;
        end;
    quit;

    Combined conditions:

    >>> with so.Workspace('w') as w:
    >>>     p = so.Parameter(name='p')
    >>>     def case1():
    >>>         p.set_value(10)
    >>>     def case2():
    >>>         p.set_value(20)
    >>>     r = so.Parameter(name='r', value=10)
    >>>     if_condition((r < 5) | (r > 10), case1, case2)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        num p;
        num r = 10;
        if (r < 5) or (r > 10) then do;
            p = 10;
        end;
        else do;
            p = 20;
        end;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def switch_conditions(**args):
    """
    Creates several if-else blocks by using the specified arguments

    Parameters
    ----------
    args :
        Several arguments can be passed to the function

        Each case should follow a condition.
        You can use :class:`sasoptpy.Constraint` objects as conditions, and
        Python functions for the cases.

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x')
    >>>     p = so.Parameter(name='p')
    >>>     x.set_value(2.5)
    >>>     def func1():
    >>>         p.set_value(1)
    >>>     def func2():
    >>>         p.set_value(2)
    >>>     def func3():
    >>>         p.set_value(3)
    >>>     def func4():
    >>>         p.set_value(0)
    >>>     switch_conditions(x < 1, func1, x < 2, func2, x < 3, func3, func4)
    >>> print(to.optmodel(w))
    proc optmodel;
        var x;
        num p;
        x = 2.5;
        if x < 1 then do;
            p = 1;
        end;
        else if x < 2 then do;
            p = 2;
        end;
        else if x < 3 then do;
            p = 3;
        end;
        else do;
            p = 0;
        end;
    quit;
    """
    pass


@sasoptpy.containable(standalone=False)
def set_value(left, right):
    """
    Creates an assignment statement

    Parameters
    ----------
    left : :class:`sasoptpy.Expression`
        Any expression (variable or parameter)
    right : :class:`sasoptpy.Expression` or float
        Right-hand-side expression

    Examples
    --------

    >>> with so.Workspace('ex_9_1_matirx_sqrt', session=None) as w:
    >>>     so.LiteralStatement('call streaminit(1);')
    >>>     n = so.Parameter(name='n', value=5)
    >>>     rn = so.Set(name='RN', value=so.exp_range(1, n))
    >>>     A = so.ParameterGroup(rn, rn, name='A', value="10-20*rand('UNIFORM')")
    >>>     P = so.ParameterGroup(rn, rn, name='P')
    >>>     for i in for_loop(rn):
    >>>         for j in for_loop(so.exp_range(i, n)):
    >>>             set_value(P[i, j], so.expr_sum(A[i, k] * A[j, k] for k in rn))
    >>> print(so.to_optmodel(w))
    proc optmodel;
        call streaminit(1);
        num n = 5;
        set RN = 1..n;
        num A {RN, RN} = 10-20*rand('UNIFORM');
        num P {RN, RN};
        for {o7 in RN} do;
            for {o10 in o7..n} do;
                P[o7, o10] = sum {k in RN} (A[o7, k] * A[o10, k]);
            end;
        end;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def fix(*args):
    """
    Fixes values of variables to the specified values

    Parameters
    ----------
    args : :class:`sasoptpy.Variable`, float, :class:`sasoptpy.Expression`, tuple
        Set of arguments to be fixed

        Arguments get paired (if not given in tuples) to allow several fix
        operations

    Examples
    --------

    Regular fix statement:

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x')
    >>>     fix(x, 1)
    >>>     solve()
    >>>     unfix(x)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x;
        fix x=1;
        solve;
        unfix x;
    quit;

    Multiple fix-unfix:

    >>> with so.Workspace('w') as w:
    >>>     x = so.VariableGroup(4, name='x')
    >>>     for i in cofor_loop(range(4)):
    >>>         fix((x[0], i), (x[1], 1))
    >>>         solve()
    >>>         unfix(x[0], (x[1], 2))
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x {{0,1,2,3}};
        cofor {o7 in 0..3} do;
            fix x[0]=o7 x[1]=1;
            solve;
            unfix x[0] x[1]=2;
        end;
    quit;

    See also
    --------
    :func:`sasoptpy.actions.unfix`,
    :class:`tests.abstract.statement.test_fix_unfix.TestFix`

    """
    pass


@sasoptpy.containable(standalone=False)
def unfix(*args):
    """
    Unfixes values of variables

    Parameters
    ----------
    args : :class:`sasoptpy.Variable` objects
        Set of arguments to be unfixed

    Examples
    --------

    Regular unfix statement:

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x')
    >>>     fix(x, 1)
    >>>     solve()
    >>>     unfix(x)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x;
        fix x=1;
        solve;
        unfix x;
    quit;

    Multiple fix-unfix:

    >>> with so.Workspace('w') as w:
    >>>     x = so.VariableGroup(4, name='x')
    >>>     for i in cofor_loop(range(4)):
    >>>         fix((x[0], i), (x[1], 1))
    >>>         solve()
    >>>         unfix(x[0], (x[1], 2))
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x {{0,1,2,3}};
        cofor {o7 in 0..3} do;
            fix x[0]=o7 x[1]=1;
            solve;
            unfix x[0] x[1]=2;
        end;
    quit;

    See also
    --------
    :func:`sasoptpy.actions.fix`,
    :class:`tests.abstract.statement.test_fix_unfix.TestFix`

    """
    pass


@sasoptpy.containable(standalone=False)
def set_objective(expression, name, sense):
    """
    Specifies the objective function

    Parameters
    ----------
    expression : :class:`sasoptpy.Expression`
        Objective function
    name : string
        Name of the objective function
    sense : string
        Direction of the objective function, `so.MAX` or `so.MIN`

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x', lb=1)
    >>>     set_objective(x ** 3, name='xcube', sense=so.minimize)
    >>>     solve()
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x >= 1;
        MIN xcube = (x) ^ (3);
        solve;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def print_item(*args):
    """
    Prints the specified argument list on server

    Parameters
    ----------
    args : :class:`sasoptpy.Variable`, :class:`sasoptpy.Expression`
        Arbitrary number of arguments to be printed

        These values are printed on the server, but can be retrieved after
        execution

    Returns
    -------
    ps : :class:`sasoptpy.abstract.statement.PrintStatement`
        Print statement object.

        Contents of the response can be retrieved using `get_response` function.

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x', lb=1, ub=10)
    >>>     o = so.Objective(2*x, sense=so.maximize, name='obj')
    >>>     s = solve()
    >>>     p = print_item(x)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x >= 1 <= 10;
        max obj = 2 * x;
        solve;
        print x;
    quit;
    >>> print(p.get_response())
          x
    0  10.0

    """
    pass


@sasoptpy.containable(standalone=False)
def put_item(*args, names=None):
    """
    Prints the specified item values to the output log

    Parameters
    ----------
    args : :class:`sasoptpy.Expression`, string
        Arbitrary elements to be put into log

        Variables, variable groups, and expressions can be printed to log
    names : bool, optional
        When set to `True`, prints the name of the arguments in the log

    Examples
    --------

    Regular operation:

    >>> with so.Workspace('w') as w:
    >>>     for i in for_loop(range(1, 3)):
    >>>         for j in for_loop(['a', 'b']):
    >>>             put_item(i, j)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        for {o2 in 1..2} do;
            for {o5 in {'a','b'}} do;
                put o2 o5;
            end;
        end;
    quit;

    Print with names:

    >>> with so.Workspace('w') as w:
    >>>     x = so.VariableGroup(6, name='x', lb=0)
    >>>     so.Objective(
    >>>         so.expr_sum(x[i] for i in range(6)), name='z', sense=so.MIN)
    >>>     a1 = so.Constraint(x[1] + x[2] + x[3] <= 4, name='a1')
    >>>     for i in cofor_loop(so.exp_range(3, 6)):
    >>>         fix(x[1], i)
    >>>         solve()
    >>>         put_item(i, x[1], so.Symbol('_solution_status_'), names=True)
    proc optmodel;
        var x {{0,1,2,3,4,5}} >= 0;
        min z = x[0] + x[1] + x[2] + x[3] + x[4] + x[5];
        con a1 : x[1] + x[2] + x[3] <= 4;
        cofor {o13 in 3..5} do;
            fix x[1]=o13;
            solve;
            put o13= x[1]= _solution_status_=;
        end;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def expand():
    """
    Prints expanded problem to output

    Examples
    --------
    >>> with so.Workspace(name='w') as w:
    >>>     x = so.VariableGroup(3, name='x')
    >>>     self.assertEqual(x[0].sym.get_conditions_str(), '')
    >>>     # solve
    >>>     x[0].set_value(1)
    >>>     x[1].set_value(5)
    >>>     x[2].set_value(0)
    >>>     c = so.ConstraintGroup(None, name='c')
    >>>     with iterate([0, 1, 2], 's') as i:
    >>>         with condition(x[i].sym > 0):
    >>>             c[i] = x[i] >= 1
    >>>     set_objective(x[0], name='obj', sense=so.MIN)
    >>>     expand()
    >>>     solve()
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x {{0,1,2}};
        x[0] = 1;
        x[1] = 5;
        x[2] = 0;
        con c {s in {0,1,2}: x[s].sol > 0} : x[s] >= 1;
        MIN obj = x[0];
        expand;
        solve;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def drop(*args):
    """
    Drops the specified constraints or constraint groups from model

    Parameters
    ----------
    args : :class:`sasoptpy.Constraint`, :class:`sasoptpy.ConstraintGroup`
        Constraints to be dropped

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x', lb=1)
    >>>     y = so.Variable(name='y', lb=0)
    >>>     c = so.Constraint(sm.sqrt(x) >= 5, name='c')
    >>>     o = so.Objective(x + y, sense=so.MIN, name='obj')
    >>>     s = solve()
    >>>     drop(c)
    >>>     o2 = so.Objective(x, sense=so.MIN, name='obj2')
    >>>     s2 = solve()
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x >= 1;
        var y >= 0;
        con c : sqrt(x) >= 5;
        min obj = x + y;
        solve;
        drop c;
        min obj2 = x;
        solve;
    quit;

    See also
    --------
    :func:`sasoptpy.actions.restore`

    """
    pass


@sasoptpy.containable(standalone=False)
def restore(*args):
    """
    Restores dropped constraint and constraint groups

    Parameters
    ----------
    args : :class:`sasoptpy.Constraint`, :class:`sasoptpy.ConstraintGroup`
        Constraints to be restored

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     x = so.Variable(name='x', lb=-1)
    >>>     set_objective(x**3, name='xcube', sense=so.minimize)
    >>>     c = so.Constraint(x >= 1, name='xbound')
    >>>     solve()
    >>>     drop(c)
    >>>     solve()
    >>>     restore(c)
    >>>     solve()
    >>> print(so.to_optmodel(w))
    proc optmodel;
        var x >= -1;
        MIN xcube = (x) ^ (3);
        con xbound : x >= 1;
        solve;
        drop xbound;
        solve;
        restore xbound;
        solve;
    quit;

    See also
    --------
    :func:`sasoptpy.actions.drop`

    """
    pass


@sasoptpy.containable(standalone=False)
def union(*args):
    """
    Aggregates the specified sets and set expressions

    Parameters
    ----------
    args : :class:`sasoptpy.abstract.Set` and :class:`sasoptpy.abstract.InlineSet`
        Objects to be aggregated

    Examples
    --------

    >>> from sasoptpy.actions import union, put_item
    >>> with so.Workspace('w') as w:
    >>>     n = so.Parameter(name='n', value=11)
    >>>     S = so.Set(name='S', value=so.exp_range(1, n))
    >>>     T = so.Set(name='T', value=so.exp_range(n+1, 20))
    >>>     U = so.Set(name='U', value=union(S, T))
    >>>     put_item(U, names=True)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        num n = 11;
        set S = 1..n;
        set T = n+1..20;
        set U = S union T;
        put U=;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def diff(left, right):
    """
    Gets the difference between set and set expressions

    Parameters
    ----------
    left : :class:`sasoptpy.abstract.Set`
        Left operand
    right : :class:`sasoptpy.abstract.Set`
        Right operand

    Examples
    --------

    >>> from sasoptpy.actions import diff, put_item
    >>> with so.Workspace('w') as w:
    >>>     S = so.Set(name='S', value=so.exp_range(1, 20))
    >>>     T = so.Set(name='T', value=so.exp_range(1, 15))
    >>>     U = so.Set(name='U', value=diff(S, T))
    >>>     put_item(U, names=True)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        set S = 1..19;
        set T = 1..14;
        set U = S diff T;
        put U=;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def substring(main_string, first_pos, last_pos):
    """
    Gets the substring of the specified positions

    Parameters
    ----------
    main_string : :class:`sasoptpy.abstract.Parameter` or string
        Main string
    first_pos : integer
        First position of the substring, starting from 1
    last_pos : integer
        Last position of the substring

    Examples
    --------

    >>> with so.Workspace('w') as w:
    >>>     p = so.Parameter(name='p', value='random_string', ptype=so.STR)
    >>>     r = so.Parameter(name='r', value=substring(p, 1, 6), ptype=so.STR)
    >>>     put_item(r)
    >>> print(so.to_optmodel(w))
    proc optmodel;
        str p = 'random_string';
        str r = substr(p, 1, 6);
        put r;
    quit;

    """
    pass


@sasoptpy.containable(standalone=False)
def use_problem(problem):
    """
    Changes the currently active problem

    Parameters
    ----------
    problem : :class:`sasoptpy.Model`
        Model to be activated

    Examples
    --------

    >>> from sasoptpy.actions import use_problem
    >>> with so.Workspace('w') as w:
    >>>     m = so.Model(name='m')
    >>>     m2 = so.Model(name='m2')
    >>>     use_problem(m)
    >>>     x = so.Variable(name='x')
    >>>     use_problem(m2)
    >>>     m.solve()
    >>>     m2.solve()
    >>> print(so.to_optmodel(w))
    proc optmodel;
        problem m;
        problem m2;
        use problem m;
        var x;
        use problem m2;
        use problem m;
        solve;
        use problem m2;
        solve;
    quit;
    """
    pass


condition = sasoptpy.structure.under_condition
inline_condition = sasoptpy.structure.inline_condition
