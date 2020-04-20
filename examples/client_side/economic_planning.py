import sasoptpy as so
import pandas as pd


def test(cas_conn):

    m = so.Model(name='economic_planning', session=cas_conn)

    industry_data = pd.DataFrame([
        ['coal', 150, 300, 60],
        ['steel', 80, 350, 60],
        ['transport', 100, 280, 30]
        ], columns=['industry', 'init_stocks', 'init_productive_capacity',
                    'demand']).set_index(['industry'])

    production_data = pd.DataFrame([
        ['coal', 0.1, 0.5, 0.4],
        ['steel', 0.1, 0.1, 0.2],
        ['transport', 0.2, 0.1, 0.2],
        ['manpower', 0.6, 0.3, 0.2],
        ], columns=['input', 'coal',
                    'steel', 'transport']).set_index(['input'])

    productive_capacity_data = pd.DataFrame([
        ['coal', 0.0, 0.7, 0.9],
        ['steel', 0.1, 0.1, 0.2],
        ['transport', 0.2, 0.1, 0.2],
        ['manpower', 0.4, 0.2, 0.1],
        ], columns=['input', 'coal',
                    'steel', 'transport']).set_index(['input'])

    manpower_capacity = 470
    num_years = 5

    YEARS = list(range(1, num_years+1))
    YEARS0 = [0] + list(YEARS)
    INDUSTRIES = industry_data.index.tolist()

    init_stocks = industry_data['init_stocks']
    init_productive_capacity = industry_data['init_productive_capacity']
    demand = industry_data['demand']

    production_coeff = so.flatten_frame(production_data)
    productive_capacity_coeff = so.flatten_frame(productive_capacity_data)

    static_production = m.add_variables(INDUSTRIES, lb=0,
                                        name='static_production')
    m.set_objective(0, sense=so.MIN, name='Zero')
    m.add_constraints((static_production[i] == demand[i] +
                       so.expr_sum(
                           production_coeff[i, j] * static_production[j]
                           for j in INDUSTRIES) for i in INDUSTRIES),
                      name='static_con')

    m.solve()
    print(so.get_value_table(static_production))

    final_demand = so.get_value_table(
        static_production)['static_production']

    production = m.add_variables(INDUSTRIES, range(0, num_years+2), lb=0,
                                 name='production')
    stock = m.add_variables(INDUSTRIES, range(0, num_years+2), lb=0,
                            name='stock')
    extra_capacity = m.add_variables(INDUSTRIES, range(2, num_years+3), lb=0,
                                     name='extra_capacity')

    productive_capacity = so.ImplicitVar(
        (init_productive_capacity[i] +
         so.expr_sum(extra_capacity[i, y] for y in range(2, year+1))
         for i in INDUSTRIES for year in range(1, num_years+2)),
        name='productive_capacity'
    )

    for i in INDUSTRIES:
        production[i, 0].set_bounds(ub=0)
        stock[i, 0].set_bounds(lb=init_stocks[i], ub=init_stocks[i])

    total_productive_capacity = sum(productive_capacity[i, num_years]
                                    for i in INDUSTRIES)
    total_production = so.expr_sum(production[i, year] for i in INDUSTRIES
                                    for year in [4, 5])
    total_manpower = so.expr_sum(production_coeff['manpower', i] *
                                  production[i, year+1] +
                                  productive_capacity_coeff['manpower', i] *
                                  extra_capacity[i, year+2]
                                  for i in INDUSTRIES for year in YEARS)

    continuity_con = m.add_constraints((
        stock[i, year] + production[i, year] ==
        (demand[i] if year in YEARS else 0) +
        so.expr_sum(production_coeff[i, j] * production[j, year+1] +
                     productive_capacity_coeff[i, j] *
                     extra_capacity[j, year+2] for j in INDUSTRIES) +
        stock[i, year+1]
        for i in INDUSTRIES for year in YEARS0), name='continuity_con')

    manpower_con = m.add_constraints((
        so.expr_sum(production_coeff['manpower', j] * production[j, year] +
                     productive_capacity_coeff['manpower', j] *
                     extra_capacity[j, year+1]
                     for j in INDUSTRIES)
        <= manpower_capacity for year in range(1, num_years+2)),
        name='manpower_con')

    capacity_con = m.add_constraints((production[i, year] <=
                                      productive_capacity[i, year]
                                      for i in INDUSTRIES
                                      for year in range(1, num_years+2)),
                                     name='capacity_con')

    for i in INDUSTRIES:
        production[i, num_years+1].set_bounds(lb=final_demand[i])

    for i in INDUSTRIES:
        for year in [num_years+1, num_years+2]:
            extra_capacity[i, year].set_bounds(ub=0)

    problem1 = so.Model(name='Problem1', session=cas_conn)
    problem1.include(
        production, stock, extra_capacity, continuity_con, manpower_con,
        capacity_con, productive_capacity)
    problem1.set_objective(total_productive_capacity, sense=so.MAX,
                           name='total_productive_capacity')
    problem1.solve()
    so.pd.display_dense()
    print(so.get_value_table(production, stock, extra_capacity,
                                productive_capacity).sort_index())
    print(so.get_value_table(manpower_con.get_expressions()))

    # Problem 2

    problem2 = so.Model(name='Problem2', session=cas_conn)
    problem2.include(problem1)
    problem2.set_objective(total_production, name='total_production',
                           sense=so.MAX)
    for i in INDUSTRIES:
        for year in YEARS:
            continuity_con[i, year].set_rhs(0)
    problem2.solve()
    print(so.get_value_table(production, stock, extra_capacity,
                                productive_capacity).sort_index())
    print(so.get_value_table(manpower_con.get_expressions()))

    # Problem 3

    problem3 = so.Model(name='Problem3', session=cas_conn)
    problem3.include(production, stock, extra_capacity, continuity_con,
                     capacity_con)
    problem3.set_objective(total_manpower, sense=so.MAX, name='total_manpower')
    for i in INDUSTRIES:
        for year in YEARS:
            continuity_con[i, year].set_rhs(demand[i])
    problem3.solve()
    print(so.get_value_table(production, stock, extra_capacity,
                                productive_capacity).sort_index())
    print(so.get_value_table(manpower_con.get_expressions()))

    return problem3.get_objective_value()
