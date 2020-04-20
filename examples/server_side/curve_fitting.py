import sasoptpy as so
import pandas as pd


def test(cas_conn, sols=False):

    # Upload data to server first
    xy_raw = pd.DataFrame([
        [0.0, 1.0],
        [0.5, 0.9],
        [1.0, 0.7],
        [1.5, 1.5],
        [1.9, 2.0],
        [2.5, 2.4],
        [3.0, 3.2],
        [3.5, 2.0],
        [4.0, 2.7],
        [4.5, 3.5],
        [5.0, 1.0],
        [5.5, 4.0],
        [6.0, 3.6],
        [6.6, 2.7],
        [7.0, 5.7],
        [7.6, 4.6],
        [8.5, 6.0],
        [9.0, 6.8],
        [10.0, 7.3]
        ], columns=['x', 'y'])
    xy_data = cas_conn.upload_frame(xy_raw, casout={'name': 'xy_data',
                                                    'replace': True})

    # Read observations
    from sasoptpy.actions import read_data
    POINTS = so.Set(name='POINTS')
    x = so.ParameterGroup(POINTS, name='x')
    y = so.ParameterGroup(POINTS, name='y')
    read_st = read_data(
        table=xy_data,
        index={'target': POINTS, 'key': so.N},
        columns=[
            {'target': x, 'column': 'x'},
            {'target': y, 'column': 'y'}
        ]
    )

    # Parameters and variables
    order = so.Parameter(name='order')
    beta = so.VariableGroup(so.exp_range(0, order), name='beta')
    estimate = so.ImplicitVar(
        (beta[0] + so.expr_sum(beta[k] * x[i] ** k
                                for k in so.exp_range(1, order))
         for i in POINTS), name='estimate')

    surplus = so.VariableGroup(POINTS, name='surplus', lb=0)
    slack = so.VariableGroup(POINTS, name='slack', lb=0)

    objective1 = so.Expression(
        so.expr_sum(surplus[i] + slack[i] for i in POINTS), name='objective1')
    abs_dev_con = so.ConstraintGroup(
        (estimate[i] - surplus[i] + slack[i] == y[i] for i in POINTS),
        name='abs_dev_con')

    minmax = so.Variable(name='minmax')
    objective2 = so.Expression(minmax + 0.0, name='objective2')
    minmax_con = so.ConstraintGroup(
        (minmax >= surplus[i] + slack[i] for i in POINTS), name='minmax_con')

    order.set_init(1)
    L1 = so.Model(name='L1', session=cas_conn)
    L1.set_objective(objective1, sense=so.MIN, name='L1obj')
    L1.include(POINTS, x, y, read_st)
    L1.include(order, beta, estimate, surplus, slack, abs_dev_con)
    L1.add_postsolve_statement('print x y estimate surplus slack;')

    L1.solve(verbose=True)
    if sols:
        sol_data1 = L1.response['Print1.PrintTable'].sort_values('x')
        print(so.get_solution_table(beta))
        print(sol_data1.to_string())

    Linf = so.Model(name='Linf', session=cas_conn)
    Linf.include(L1, minmax, minmax_con)
    Linf.set_objective(objective2, sense=so.MIN, name='Linfobj')

    Linf.solve()
    if sols:
        sol_data2 = Linf.response['Print1.PrintTable'].sort_values('x')
        print(so.get_solution_table(beta))
        print(sol_data2.to_string())

    order.set_init(2)

    L1.solve()
    if sols:
        sol_data3 = L1.response['Print1.PrintTable'].sort_values('x')
        print(so.get_solution_table(beta))
        print(sol_data3.to_string())

    Linf.solve()
    if sols:
        sol_data4 = Linf.response['Print1.PrintTable'].sort_values('x')
        print(so.get_solution_table(beta))
        print(sol_data4.to_string())

    if sols:
        return (sol_data1, sol_data2, sol_data3, sol_data4)
    else:
        return Linf.get_objective_value()
