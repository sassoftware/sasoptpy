import sasoptpy as so
import pandas as pd


def test(cas_conn):

    m = so.Model(name='factory_planning_2', session=cas_conn)

    # Input data
    product_list = ['prod{}'.format(i) for i in range(1, 8)]
    product_data = pd.DataFrame([10, 6, 8, 4, 11, 9, 3],
                                columns=['profit'], index=product_list)
    demand_data = [
        [500, 1000, 300, 300,  800, 200, 100],
        [600,  500, 200,   0,  400, 300, 150],
        [300,  600,   0,   0,  500, 400, 100],
        [200,  300, 400, 500,  200,   0, 100],
        [0,    100, 500, 100, 1000, 300,   0],
        [500,  500, 100, 300, 1100, 500,  60]]
    demand_data = pd.DataFrame(
        demand_data, columns=product_list, index=range(1, 7))
    machine_type_product_data = [
        ['grinder', 0.5,  0.7,  0,    0,    0.3,  0.2, 0.5],
        ['vdrill',  0.1,  0.2,  0,    0.3,  0,    0.6, 0],
        ['hdrill',  0.2,  0,    0.8,  0,    0,    0,   0.6],
        ['borer',   0.05, 0.03, 0,    0.07, 0.1,  0,   0.08],
        ['planer',  0,    0,    0.01, 0,    0.05, 0,   0.05]]
    machine_type_product_data = \
        pd.DataFrame(machine_type_product_data, columns=['machine_type'] +
                     product_list).set_index(['machine_type'])
    machine_types_data = [
        ['grinder', 4, 2],
        ['vdrill',  2, 2],
        ['hdrill',  3, 3],
        ['borer',   1, 1],
        ['planer',  1, 1]]
    machine_types_data = pd.DataFrame(machine_types_data, columns=[
        'machine_type', 'num_machines', 'num_machines_needing_maintenance'])\
        .set_index(['machine_type'])

    store_ub = 100
    storage_cost_per_unit = 0.5
    final_storage = 50
    num_hours_per_period = 24 * 2 * 8

    # Problem definition
    PRODUCTS = product_list
    profit = product_data['profit']
    PERIODS = range(1, 7)
    MACHINE_TYPES = machine_types_data.index.tolist()

    num_machines = machine_types_data['num_machines']

    make = m.add_variables(PRODUCTS, PERIODS, lb=0, name='make')
    sell = m.add_variables(PRODUCTS, PERIODS, lb=0, ub=demand_data.transpose(),
                           name='sell')

    store = m.add_variables(PRODUCTS, PERIODS, lb=0, ub=store_ub, name='store')
    for p in PRODUCTS:
        store[p, 6].set_bounds(lb=final_storage, ub=final_storage)

    storageCost = so.expr_sum(
        storage_cost_per_unit * store[p, t] for p in PRODUCTS for t in PERIODS)
    revenue = so.expr_sum(profit[p] * sell[p, t]
                           for p in PRODUCTS for t in PERIODS)
    m.set_objective(revenue-storageCost, sense=so.MAX, name='total_profit')

    num_machines_needing_maintenance = \
        machine_types_data['num_machines_needing_maintenance']
    numMachinesDown = m.add_variables(MACHINE_TYPES, PERIODS, vartype=so.INT,
                                      lb=0, name='numMachinesDown')

    production_time = machine_type_product_data
    m.add_constraints((
        so.expr_sum(production_time.at[mc, p] * make[p, t] for p in PRODUCTS)
        <= num_hours_per_period *
        (num_machines[mc] - numMachinesDown[mc, t])
        for mc in MACHINE_TYPES for t in PERIODS), name='machine_hours_con')

    m.add_constraints((so.expr_sum(numMachinesDown[mc, t] for t in PERIODS) ==
                       num_machines_needing_maintenance[mc]
                       for mc in MACHINE_TYPES), name='maintenance_con')

    m.add_constraints(((store[p, t-1] if t-1 in PERIODS else 0) + make[p, t] ==
                      sell[p, t] + store[p, t]
                      for p in PRODUCTS for t in PERIODS),
                      name='flow_balance_con')

    res = m.solve()
    if res is not None:
        print(so.get_solution_table(make, sell, store))
        print(so.get_solution_table(numMachinesDown).unstack(level=-1))

    print(m.get_solution_summary())
    print(m.get_problem_summary())

    return m.get_objective_value()

