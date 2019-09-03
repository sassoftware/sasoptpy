import sasoptpy as so


def test(cas_conn):

    m = so.Model(name='nlpse01', session=cas_conn)
    x = m.add_variables(range(1, 9), lb=0.1, ub=10, name='x')

    f = so.Expression(0.4 * (x[1]/x[7]) ** 0.67 + 0.4 * (x[2]/x[8]) ** 0.67 + 10 - x[1] - x[2], name='f')
    m.set_objective(f, sense=so.MIN, name='f1')

    m.add_constraint(1 - 0.0588*x[5]*x[7] - 0.1*x[1] >= 0, name='c1')
    m.add_constraint(1 - 0.0588*x[6]*x[8] - 0.1*x[1] - 0.1*x[2] >= 0, name='c2')
    m.add_constraint(1 - 4*x[3]/x[5] - 2/(x[3]**0.71 * x[5]) - 0.0588*(x[7]/x[3]**1.3) >= 0, name='c3')
    m.add_constraint(1 - 4*x[4]/x[6] - 2/(x[4]**0.71 * x[6]) - 0.0588*(x[8]/x[4]**1.3) >= 0, name='c4')
    m.add_constraint(f == [0.1, 4.2], name='frange')

    x[1].set_init(6)
    x[2].set_init(3)
    x[3].set_init(0.4)
    x[4].set_init(0.2)
    x[5].set_init(6)
    x[6].set_init(6)
    x[7].set_init(1)
    x[8].set_init(0.5)

    m.solve(verbose=True, options={'with': 'nlp', 'algorithm': 'activeset'})

    print(m.get_problem_summary())
    print(m.get_solution_summary())
    if m.get_session_type() == 'CAS':
        print(m.get_solution()[['var', 'value']])

    return m.get_objective_value()

