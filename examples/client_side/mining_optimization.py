import sasoptpy as so
import pandas as pd


def test(cas_conn):

    m = so.Model(name='mining_optimization', session=cas_conn)

    mine_data = pd.DataFrame([
        ['mine1', 5, 2, 1.0],
        ['mine2', 4, 2.5, 0.7],
        ['mine3', 4, 1.3, 1.5],
        ['mine4', 5, 3, 0.5],
        ], columns=['mine', 'cost', 'extract_ub', 'quality']).\
        set_index(['mine'])

    year_data = pd.DataFrame([
        [1, 0.9],
        [2, 0.8],
        [3, 1.2],
        [4, 0.6],
        [5, 1.0],
        ], columns=['year', 'quality_required']).set_index(['year'])

    max_num_worked_per_year = 3
    revenue_per_ton = 10
    discount_rate = 0.10

    MINES = mine_data.index.tolist()
    cost = mine_data['cost']
    extract_ub = mine_data['extract_ub']
    quality = mine_data['quality']
    YEARS = year_data.index.tolist()
    quality_required = year_data['quality_required']

    isOpen = m.add_variables(MINES, YEARS, vartype=so.BIN, name='isOpen')
    isWorked = m.add_variables(MINES, YEARS, vartype=so.BIN, name='isWorked')
    extract = m.add_variables(MINES, YEARS, lb=0, name='extract')
    [extract[i, j].set_bounds(ub=extract_ub[i]) for i in MINES for j in YEARS]

    extractedPerYear = {j: extract.sum('*', j) for j in YEARS}
    discount = {j: 1 / (1+discount_rate) ** (j-1) for j in YEARS}

    totalRevenue = revenue_per_ton *\
        so.expr_sum(discount[j] * extractedPerYear[j] for j in YEARS)
    totalCost = so.expr_sum(discount[j] * cost[i] * isOpen[i, j]
                             for i in MINES for j in YEARS)
    m.set_objective(totalRevenue-totalCost, sense=so.MAX, name='totalProfit')

    m.add_constraints((extract[i, j] <= extract[i, j]._ub * isWorked[i, j]
                      for i in MINES for j in YEARS), name='link')

    m.add_constraints((isWorked.sum('*', j) <= max_num_worked_per_year
                      for j in YEARS), name='cardinality')

    m.add_constraints((isWorked[i, j] <= isOpen[i, j] for i in MINES
                      for j in YEARS), name='worked_implies_open')

    m.add_constraints((isOpen[i, j] <= isOpen[i, j-1] for i in MINES
                      for j in YEARS if j != 1), name='continuity')

    m.add_constraints((so.expr_sum(quality[i] * extract[i, j] for i in MINES)
                      == quality_required[j] * extractedPerYear[j]
                      for j in YEARS), name='quality_con')

    res = m.solve()
    if res is not None:
        print(so.get_solution_table(isOpen, isWorked, extract))
        quality_sol = {j: so.expr_sum(quality[i] * extract[i, j].get_value()
                                       for i in MINES)
                       / extractedPerYear[j].get_value() for j in YEARS}
        qs = so.dict_to_frame(quality_sol, ['quality_sol'])
        epy = so.dict_to_frame(extractedPerYear, ['extracted_per_year'])
        print(so.get_solution_table(epy, qs, quality_required))

    return m.get_objective_value()
