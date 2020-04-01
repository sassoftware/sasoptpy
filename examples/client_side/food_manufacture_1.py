import sasoptpy as so
import pandas as pd


def test(cas_conn):

    # Problem data
    OILS = ['veg1', 'veg2', 'oil1', 'oil2', 'oil3']
    PERIODS = range(1, 7)
    cost_data = [
        [110, 120, 130, 110, 115],
        [130, 130, 110, 90, 115],
        [110, 140, 130, 100,  95],
        [120, 110, 120, 120, 125],
        [100, 120, 150, 110, 105],
        [90, 100, 140,  80, 135]]
    cost = pd.DataFrame(cost_data, columns=OILS, index=PERIODS).transpose()
    hardness_data = [8.8, 6.1, 2.0, 4.2, 5.0]
    hardness = {OILS[i]: hardness_data[i] for i in range(len(OILS))}

    revenue_per_ton = 150
    veg_ub = 200
    nonveg_ub = 250
    store_ub = 1000
    storage_cost_per_ton = 5
    hardness_lb = 3
    hardness_ub = 6
    init_storage = 500

    # Problem initialization
    m = so.Model(name='food_manufacture_1', session=cas_conn)

    # Problem definition
    buy = m.add_variables(OILS, PERIODS, lb=0, name='buy')
    use = m.add_variables(OILS, PERIODS, lb=0, name='use')
    manufacture = m.add_implicit_variable((use.sum('*', p) for p in PERIODS),
                                          name='manufacture')
    last_period = len(PERIODS)
    store = m.add_variables(OILS, [0] + list(PERIODS), lb=0, ub=store_ub,
                            name='store')
    for oil in OILS:
        store[oil, 0].set_bounds(lb=init_storage, ub=init_storage)
        store[oil, last_period].set_bounds(lb=init_storage, ub=init_storage)
    VEG = [i for i in OILS if 'veg' in i]
    NONVEG = [i for i in OILS if i not in VEG]
    revenue = so.expr_sum(revenue_per_ton * manufacture[p] for p in PERIODS)
    rawcost = so.expr_sum(cost.at[o, p] * buy[o, p]
                           for o in OILS for p in PERIODS)
    storagecost = so.expr_sum(storage_cost_per_ton * store[o, p]
                               for o in OILS for p in PERIODS)
    m.set_objective(revenue - rawcost - storagecost, sense=so.MAX,
                    name='profit')

    # Constraints
    m.add_constraints((use.sum(VEG, p) <= veg_ub for p in PERIODS),
                      name='veg_ub')
    m.add_constraints((use.sum(NONVEG, p) <= nonveg_ub for p in PERIODS),
                      name='nonveg_ub')
    m.add_constraints((store[o, p-1] + buy[o, p] == use[o, p] + store[o, p]
                      for o in OILS for p in PERIODS),
                      name='flow_balance')
    m.add_constraints((so.expr_sum(hardness[o]*use[o, p] for o in OILS) >=
                      hardness_lb * manufacture[p] for p in PERIODS),
                      name='hardness_ub')
    m.add_constraints((so.expr_sum(hardness[o]*use[o, p] for o in OILS) <=
                      hardness_ub * manufacture[p] for p in PERIODS),
                      name='hardness_lb')

    # Solver call
    res = m.solve()

    # With other solve options
    m.solve(options={'with': 'lp', 'algorithm': 'PS'})
    m.solve(options={'with': 'lp', 'algorithm': 'IP'})
    m.solve(options={'with': 'lp', 'algorithm': 'NS'})

    if res is not None:
        print(so.get_solution_table(buy, use, store))

    return m.get_objective_value()
