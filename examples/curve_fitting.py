import sasoptpy as so
import pandas as pd


def test(cas_conn):

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
    xy_data = cas_conn.upload_frame(xy_raw, casout='xy_data')

    # Read observations
    POINTS, (x, y), xy_table_ref = so.read_table(xy_data, columns=['x', 'y'])

    # Parameters and variables
    order = so.Parameter(name='order')
    beta = so.VariableGroup(so.exp_range(0, order), name='beta')
    estimate = so.ImplicitVar(
        (beta[0] + so.quick_sum(beta[k] * x[i] ** k
                                for k in so.exp_range(1, order))
         for i in POINTS), name='estimate')

    surplus = so.VariableGroup(POINTS, name='surplus', lb=0)
    slack = so.VariableGroup(POINTS, name='slack', lb=0)

    objective1 = so.Expression(
        so.quick_sum(surplus[i] + slack[i] for i in POINTS), name='objective1')
    abs_dev_con = so.ConstraintGroup(
        (estimate[i] - surplus[i] + slack[i] == y[i] for i in POINTS),
        name='abs_dev_con')

    minmax = so.Variable(name='minmax')
    objective2 = so.Expression(minmax + 0.0, name='objective2')
    minmax_con = so.ConstraintGroup(
        (minmax >= surplus[i] + slack[i] for i in POINTS), name='minmax_con')

    order.set_init(1)
    L1 = so.Model(name='L1', session=cas_conn)
    L1.set_objective(objective1, sense=so.MIN)
    L1.include(POINTS, x, y, xy_table_ref)
    L1.include(order, beta, estimate, surplus, slack, abs_dev_con)
    L1.add_statement('print x y estimate surplus slack;', after_solve=True)

    L1.solve(verbose=True)
    print(so.get_solution_table(beta))
    print(L1.response['Print3.PrintTable'].to_string())

    Linf = so.Model(name='Linf', session=cas_conn)
    Linf.include(L1, minmax, minmax_con)
    Linf.set_objective(objective2, sense=so.MIN)

    Linf.solve()
    print(so.get_solution_table(beta))
    print(Linf.response['Print3.PrintTable'].to_string())

    order.set_init(2)

    L1.solve()
    print(so.get_solution_table(beta))
    print(L1.response['Print3.PrintTable'].to_string())

    Linf.solve()
    print(so.get_solution_table(beta))
    print(L1.response['Print3.PrintTable'].to_string())

    # Add plots
