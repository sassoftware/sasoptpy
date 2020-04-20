import sasoptpy as so
import pandas as pd


def test(cas_conn):

    m = so.Model(name='decentralization', session=cas_conn)

    DEPTS = ['A', 'B', 'C', 'D', 'E']
    CITIES = ['Bristol', 'Brighton', 'London']

    benefit_data = pd.DataFrame([
        ['Bristol', 10, 15, 10, 20, 5],
        ['Brighton', 10, 20, 15, 15, 15]],
        columns=['city'] + DEPTS).set_index('city')

    comm_data = pd.DataFrame([
        ['A', 'B', 0.0],
        ['A', 'C', 1.0],
        ['A', 'D', 1.5],
        ['A', 'E', 0.0],
        ['B', 'C', 1.4],
        ['B', 'D', 1.2],
        ['B', 'E', 0.0],
        ['C', 'D', 0.0],
        ['C', 'E', 2.0],
        ['D', 'E', 0.7]], columns=['i', 'j', 'comm']).set_index(['i', 'j'])

    cost_data = pd.DataFrame([
        ['Bristol', 'Bristol', 5],
        ['Bristol', 'Brighton', 14],
        ['Bristol', 'London', 13],
        ['Brighton', 'Brighton', 5],
        ['Brighton', 'London', 9],
        ['London', 'London', 10]], columns=['i', 'j', 'cost']).set_index(
            ['i', 'j'])

    max_num_depts = 3

    benefit = {}
    for city in CITIES:
        for dept in DEPTS:
            try:
                benefit[dept, city] = benefit_data.loc[city, dept]
            except:
                benefit[dept, city] = 0

    comm = {}
    for row in comm_data.iterrows():
        (i, j) = row[0]
        comm[i, j] = row[1]['comm']
        comm[j, i] = comm[i, j]

    cost = {}
    for row in cost_data.iterrows():
        (i, j) = row[0]
        cost[i, j] = row[1]['cost']
        cost[j, i] = cost[i, j]

    assign = m.add_variables(DEPTS, CITIES, vartype=so.BIN, name='assign')
    IJKL = [(i, j, k, l)
            for i in DEPTS for j in CITIES for k in DEPTS for l in CITIES
            if i < k]
    product = m.add_variables(IJKL, vartype=so.BIN, name='product')

    totalBenefit = so.expr_sum(benefit[i, j] * assign[i, j]
                                for i in DEPTS for j in CITIES)

    totalCost = so.expr_sum(comm[i, k] * cost[j, l] * product[i, j, k, l]
                             for (i, j, k, l) in IJKL)

    m.set_objective(totalBenefit-totalCost, name='netBenefit', sense=so.MAX)

    m.add_constraints((so.expr_sum(assign[dept, city] for city in CITIES)
                      == 1 for dept in DEPTS), name='assign_dept')

    m.add_constraints((so.expr_sum(assign[dept, city] for dept in DEPTS)
                      <= max_num_depts for city in CITIES), name='cardinality')

    product_def1 = m.add_constraints((assign[i, j] + assign[k, l] - 1
                                     <= product[i, j, k, l]
                                     for (i, j, k, l) in IJKL),
                                     name='pd1')

    product_def2 = m.add_constraints((product[i, j, k, l] <= assign[i, j]
                                      for (i, j, k, l) in IJKL),
                                     name='pd2')

    product_def3 = m.add_constraints((product[i, j, k, l] <= assign[k, l]
                                      for (i, j, k, l) in IJKL),
                                     name='pd3')

    m.solve()
    print(m.get_problem_summary())

    m.drop_constraints(product_def1)
    m.drop_constraints(product_def2)
    m.drop_constraints(product_def3)

    m.add_constraints((
        so.expr_sum(product[i, j, k, l]
                     for j in CITIES if (i, j, k, l) in IJKL) == assign[k, l]
        for i in DEPTS for k in DEPTS for l in CITIES if i < k),
        name='pd4')

    m.add_constraints((
        so.expr_sum(product[i, j, k, l]
                     for l in CITIES if (i, j, k, l) in IJKL) == assign[i, j]
        for k in DEPTS for i in DEPTS for j in CITIES if i < k),
        name='pd5')

    m.solve()
    print(m.get_problem_summary())
    totalBenefit.set_name('totalBenefit')
    totalCost.set_name('totalCost')
    print(so.get_solution_table(totalBenefit, totalCost))
    print(so.get_solution_table(assign).unstack(level=-1))

    return m.get_objective_value()
