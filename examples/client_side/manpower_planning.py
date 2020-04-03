import sasoptpy as so
import pandas as pd
import math


def test(cas_conn):
    # Input data
    demand_data = pd.DataFrame([
        [0, 2000, 1500, 1000],
        [1, 1000, 1400, 1000],
        [2, 500, 2000, 1500],
        [3, 0, 2500, 2000]
        ], columns=['period', 'unskilled', 'semiskilled', 'skilled'])\
        .set_index(['period'])
    worker_data = pd.DataFrame([
        ['unskilled',   0.25, 0.10, 500, 200, 1500, 50, 500],
        ['semiskilled', 0.20, 0.05, 800, 500, 2000, 50, 400],
        ['skilled',     0.10, 0.05, 500, 500, 3000, 50, 400]
        ], columns=['worker', 'waste_new', 'waste_old', 'recruit_ub',
                    'redundancy_cost', 'overmanning_cost', 'shorttime_ub',
                    'shorttime_cost']).set_index(['worker'])
    retrain_data = pd.DataFrame([
        ['unskilled', 'semiskilled', 200, 400],
        ['semiskilled', 'skilled', math.inf, 500],
        ], columns=['worker1', 'worker2', 'retrain_ub', 'retrain_cost']).\
        set_index(['worker1', 'worker2'])
    downgrade_data = pd.DataFrame([
        ['semiskilled', 'unskilled'],
        ['skilled', 'semiskilled'],
        ['skilled', 'unskilled']
        ], columns=['worker1', 'worker2'])

    semiskill_retrain_frac_ub = 0.25
    downgrade_leave_frac = 0.5
    overmanning_ub = 150
    shorttime_frac = 0.5

    # Sets
    WORKERS = worker_data.index.tolist()
    PERIODS0 = demand_data.index.tolist()
    PERIODS = PERIODS0[1:]
    RETRAIN_PAIRS = [i for i, _ in retrain_data.iterrows()]
    DOWNGRADE_PAIRS = [(row['worker1'], row['worker2'])
                       for _, row in downgrade_data.iterrows()]

    waste_old = worker_data['waste_old']
    waste_new = worker_data['waste_new']
    redundancy_cost = worker_data['redundancy_cost']
    overmanning_cost = worker_data['overmanning_cost']
    shorttime_cost = worker_data['shorttime_cost']
    retrain_cost = retrain_data['retrain_cost'].unstack(level=-1)

    # Initialization
    m = so.Model(name='manpower_planning', session=cas_conn)

    # Variables
    numWorkers = m.add_variables(WORKERS, PERIODS0, name='numWorkers', lb=0)
    demand0 = demand_data.loc[0]
    for w in WORKERS:
        numWorkers[w, 0].set_bounds(lb=demand0[w], ub=demand0[w])
    numRecruits = m.add_variables(WORKERS, PERIODS, name='numRecruits', lb=0)
    worker_ub = worker_data['recruit_ub']
    for w in WORKERS:
        for p in PERIODS:
            numRecruits[w, p].set_bounds(ub=worker_ub[w])
    numRedundant = m.add_variables(WORKERS, PERIODS, name='numRedundant', lb=0)
    numShortTime = m.add_variables(WORKERS, PERIODS, name='numShortTime', lb=0)
    shorttime_ub = worker_data['shorttime_ub']
    for w in WORKERS:
        for p in PERIODS:
            numShortTime.set_bounds(ub=shorttime_ub[w])
    numExcess = m.add_variables(WORKERS, PERIODS, name='numExcess', lb=0)

    retrain_ub = pd.DataFrame()
    for i in PERIODS:
        retrain_ub[i] = retrain_data['retrain_ub']
    numRetrain = m.add_variables(RETRAIN_PAIRS, PERIODS, name='numRetrain',
                                 lb=0, ub=retrain_ub)

    numDowngrade = m.add_variables(DOWNGRADE_PAIRS, PERIODS,
                                   name='numDowngrade', lb=0)
    # Constraints
    m.add_constraints((numWorkers[w, p]
                      - (1-shorttime_frac) * numShortTime[w, p]
                      - numExcess[w, p] == demand_data.loc[p, w]
                      for w in WORKERS for p in PERIODS), name='demand')
    m.add_constraints((numWorkers[w, p] ==
                      (1 - waste_old[w]) * numWorkers[w, p-1]
                      + (1 - waste_new[w]) * numRecruits[w, p]
                      + (1 - waste_old[w]) * numRetrain.sum('*', w, p)
                      + (1 - downgrade_leave_frac) *
                      numDowngrade.sum('*', w, p)
                      - numRetrain.sum(w, '*', p)
                      - numDowngrade.sum(w, '*', p)
                      - numRedundant[w, p]
                      for w in WORKERS for p in PERIODS),
                      name='flow_balance')
    m.add_constraints((numRetrain['semiskilled', 'skilled', p] <=
                      semiskill_retrain_frac_ub * numWorkers['skilled', p]
                      for p in PERIODS), name='semiskill_retrain')
    m.add_constraints((numExcess.sum('*', p) <= overmanning_ub
                      for p in PERIODS), name='overmanning')
    # Objectives
    redundancy = so.Expression(numRedundant.sum('*', '*'), name='redundancy')
    cost = so.Expression(so.expr_sum(redundancy_cost[w] * numRedundant[w, p] +
                                      shorttime_cost[w] * numShortTime[w, p] +
                                      overmanning_cost[w] * numExcess[w, p]
                                      for w in WORKERS for p in PERIODS)
                         + so.expr_sum(
                             retrain_cost.loc[i, j] * numRetrain[i, j, p]
                             for i, j in RETRAIN_PAIRS for p in PERIODS),
                         name='cost')

    m.set_objective(redundancy, sense=so.MIN, name='redundancy_obj')
    res = m.solve()
    if res is not None:
        print('Redundancy:', redundancy.get_value())
        print('Cost:', cost.get_value())
        print(so.get_solution_table(
            numWorkers, numRecruits, numRedundant, numShortTime, numExcess))
        print(so.get_solution_table(numRetrain))
        print(so.get_solution_table(numDowngrade))

    m.set_objective(cost, sense=so.MIN, name='cost_obj')
    res = m.solve()
    if res is not None:
        print('Redundancy:', redundancy.get_value())
        print('Cost:', cost.get_value())
        print(so.get_solution_table(numWorkers, numRecruits, numRedundant,
                                    numShortTime, numExcess))
        print(so.get_solution_table(numRetrain))
        print(so.get_solution_table(numDowngrade))

    return m.get_objective_value()
