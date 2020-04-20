import sasoptpy as so
import sasoptpy.abstract.math as sm


def test(cas_conn):

    m = so.Model(name='nlpse02', session=cas_conn)
    N = m.add_parameter(name='N', init=1000)
    x = m.add_variables(so.exp_range(1, N), name='x', init=1)
    m.set_objective(
        so.expr_sum(-4*x[i]+3 for i in so.exp_range(1, N-1)) +
        so.expr_sum((x[i]**2 + x[N]**2)**2 for i in so.exp_range(1, N-1)),
        name='f', sense=so.MIN)

    m.add_statement('print x;', after_solve=True)
    m.solve(options={'with': 'nlp'}, verbose=True)
    print(m.get_solution_summary())
    if m.get_session_type() == 'CAS':
        print(m.response['Print1.PrintTable'].head())

    # Model 2
    so.reset()
    m = so.Model(name='nlpse02_2', session=cas_conn)
    N = m.add_parameter(name='N', init=1000)
    x = m.add_variables(so.exp_range(1, N), name='x', lb=1, ub=2)
    m.set_objective(
        so.expr_sum(sm.cos(-0.5*x[i+1] - x[i]**2) for i in so.exp_range(
            1, N-1)), name='f2', sense=so.MIN)
    m.add_statement('print x;', after_solve=True)
    m.solve(verbose=True, options={'with': 'nlp', 'algorithm': 'activeset'})
    print(m.get_solution_summary())

    return m.get_objective_value()
