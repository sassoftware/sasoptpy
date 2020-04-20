import sasoptpy as so
import pandas as pd


def test(cas_conn, data=None):

    # Use default data if not passed
    if data is None:
        data = pd.DataFrame([
            [4, 8, 43.71],
            [62, 5, 351.29],
            [81, 62, 2878.91],
            [85, 75, 3591.59],
            [65, 54, 2058.71],
            [96, 84, 4487.87],
            [98, 29, 1773.52],
            [36, 33, 767.57],
            [30, 91, 1637.66],
            [3, 59, 215.28],
            [62, 57, 2067.42],
            [11, 48, 394.11],
            [66, 21, 932.84],
            [68, 24, 1069.21],
            [95, 30, 1770.78],
            [34, 14, 368.51],
            [86, 81, 3902.27],
            [37, 49, 1115.67],
            [46, 80, 2136.92],
            [87, 72, 3537.84],
        ], columns=['x1', 'x2', 'y'])

    m = so.Model(name='least_squares', session=cas_conn)

    # Regression model: L(a,b,c) = a * x1 + b * x2 + c * x1 * x2
    a = m.add_variable(name='a')
    b = m.add_variable(name='b')
    c = m.add_variable(name='c')

    x1 = data['x1']
    x2 = data['x2']
    y = data['y']

    err = m.add_implicit_variable((
        y[i] - (a * x1[i] + b * x2[i] + c * x1[i]  * x2[i]) for i in data.index
    ), name='error')
    m.set_objective(so.expr_sum(err[i]**2 for i in data.index),
                    sense=so.MIN,
                    name='total_error')
    m.solve(verbose=True, options={'with': 'nlp'})
    return m.get_objective_value()
