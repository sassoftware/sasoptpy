import sasoptpy as so
import pandas as pd


def test(cas_conn):

    m = so.Model(name='farm_planning', session=cas_conn)

    # Input Data

    cow_data_raw = []
    for age in range(12):
        if age < 2:
            row = {'age': age,
                   'init_num_cows': 10,
                   'acres_needed': 2/3.0,
                   'annual_loss': 0.05,
                   'bullock_yield': 0,
                   'heifer_yield': 0,
                   'milk_revenue': 0,
                   'grain_req': 0,
                   'sugar_beet_req': 0,
                   'labour_req': 10,
                   'other_costs': 50}
        else:
            row = {'age': age,
                   'init_num_cows': 10,
                   'acres_needed': 1,
                   'annual_loss': 0.02,
                   'bullock_yield': 1.1/2,
                   'heifer_yield': 1.1/2,
                   'milk_revenue': 370,
                   'grain_req': 0.6,
                   'sugar_beet_req': 0.7,
                   'labour_req': 42,
                   'other_costs': 100}
        cow_data_raw.append(row)
    cow_data = pd.DataFrame(cow_data_raw).set_index(['age'])
    grain_data = pd.DataFrame([
        ['group1', 20, 1.1],
        ['group2', 30, 0.9],
        ['group3', 20, 0.8],
        ['group4', 10, 0.65]
        ], columns=['group', 'acres', 'yield']).set_index(['group'])
    num_years = 5
    num_acres = 200
    bullock_revenue = 30
    heifer_revenue = 40
    dairy_cow_selling_age = 12
    dairy_cow_selling_revenue = 120
    max_num_cows = 130
    sugar_beet_yield = 1.5
    grain_cost = 90
    grain_revenue = 75
    grain_labour_req = 4
    grain_other_costs = 15
    sugar_beet_cost = 70
    sugar_beet_revenue = 58
    sugar_beet_labour_req = 14
    sugar_beet_other_costs = 10
    nominal_labour_cost = 4000
    nominal_labour_hours = 5500
    excess_labour_cost = 1.2
    capital_outlay_unit = 200
    num_loan_years = 10
    annual_interest_rate = 0.15
    max_decrease_ratio = 0.50
    max_increase_ratio = 0.75

    # Sets

    AGES = cow_data.index.tolist()
    init_num_cows = cow_data['init_num_cows']
    acres_needed = cow_data['acres_needed']
    annual_loss = cow_data['annual_loss']
    bullock_yield = cow_data['bullock_yield']
    heifer_yield = cow_data['heifer_yield']
    milk_revenue = cow_data['milk_revenue']
    grain_req = cow_data['grain_req']
    sugar_beet_req = cow_data['sugar_beet_req']
    cow_labour_req = cow_data['labour_req']
    cow_other_costs = cow_data['other_costs']

    YEARS = list(range(1, num_years+1))
    YEARS0 = [0] + YEARS

    # Variables

    numCows = m.add_variables(AGES + [dairy_cow_selling_age], YEARS0, lb=0,
                              name='numCows')
    for age in AGES:
        numCows[age, 0].set_bounds(lb=init_num_cows[age],
                                   ub=init_num_cows[age])
    numCows[dairy_cow_selling_age, 0].set_bounds(lb=0, ub=0)

    numBullocksSold = m.add_variables(YEARS, lb=0, name='numBullocksSold')
    numHeifersSold = m.add_variables(YEARS, lb=0, name='numHeifersSold')

    GROUPS = grain_data.index.tolist()
    acres = grain_data['acres']
    grain_yield = grain_data['yield']
    grainAcres = m.add_variables(GROUPS, YEARS, lb=0, name='grainAcres')
    for group in GROUPS:
        for year in YEARS:
            grainAcres[group, year].set_bounds(ub=acres[group])
    grainBought = m.add_variables(YEARS, lb=0, name='grainBought')
    grainSold = m.add_variables(YEARS, lb=0, name='grainSold')

    sugarBeetAcres = m.add_variables(YEARS, lb=0, name='sugarBeetAcres')
    sugarBeetBought = m.add_variables(YEARS, lb=0, name='sugarBeetBought')
    sugarBeetSold = m.add_variables(YEARS, lb=0, name='sugarBeetSold')

    numExcessLabourHours = m.add_variables(YEARS, lb=0,
                                           name='numExcessLabourHours')
    capitalOutlay = m.add_variables(YEARS, lb=0, name='capitalOutlay')

    yearly_loan_payment = (annual_interest_rate * capital_outlay_unit) /\
                          (1 - (1+annual_interest_rate)**(-num_loan_years))

    # Objective function

    revenue = {year:
               bullock_revenue * numBullocksSold[year] +
               heifer_revenue * numHeifersSold[year] +
               dairy_cow_selling_revenue * numCows[dairy_cow_selling_age,
                                                   year] +
               so.expr_sum(milk_revenue[age] * numCows[age, year]
                            for age in AGES) +
               grain_revenue * grainSold[year] +
               sugar_beet_revenue * sugarBeetSold[year]
               for year in YEARS}

    cost = {year:
            grain_cost * grainBought[year] +
            sugar_beet_cost * sugarBeetBought[year] +
            nominal_labour_cost +
            excess_labour_cost * numExcessLabourHours[year] +
            so.expr_sum(cow_other_costs[age] * numCows[age, year]
                         for age in AGES) +
            so.expr_sum(grain_other_costs * grainAcres[group, year]
                         for group in GROUPS) +
            sugar_beet_other_costs * sugarBeetAcres[year] +
            so.expr_sum(yearly_loan_payment * capitalOutlay[y]
                         for y in YEARS if y <= year)
            for year in YEARS}
    profit = {year: revenue[year] - cost[year] for year in YEARS}

    totalProfit = so.expr_sum(profit[year] -
                               yearly_loan_payment * (num_years - 1 + year) *
                               capitalOutlay[year] for year in YEARS)

    m.set_objective(totalProfit, sense=so.MAX, name='totalProfit')

    # Constraints

    m.add_constraints((
        so.expr_sum(acres_needed[age] * numCows[age, year] for age in AGES) +
        so.expr_sum(grainAcres[group, year] for group in GROUPS) +
        sugarBeetAcres[year] <= num_acres
        for year in YEARS), name='num_acres')

    m.add_constraints((
        numCows[age+1, year+1] == (1-annual_loss[age]) * numCows[age, year]
        for age in AGES if age != dairy_cow_selling_age
        for year in YEARS0 if year != num_years), name='aging')

    m.add_constraints((
        numBullocksSold[year] == so.expr_sum(
            bullock_yield[age] * numCows[age, year] for age in AGES)
        for year in YEARS), name='numBullocksSold_def')

    m.add_constraints((
        numCows[0, year] == so.expr_sum(
            heifer_yield[age] * numCows[age, year]
            for age in AGES) - numHeifersSold[year]
        for year in YEARS), name='numHeifersSold_def')

    m.add_constraints((
        so.expr_sum(numCows[age, year] for age in AGES) <= max_num_cows +
        so.expr_sum(capitalOutlay[y] for y in YEARS if y <= year)
        for year in YEARS), name='max_num_cows_def')

    grainGrown = {(group, year): grain_yield[group] * grainAcres[group, year]
                  for group in GROUPS for year in YEARS}
    m.add_constraints((
        so.expr_sum(grain_req[age] * numCows[age, year] for age in AGES) <=
        so.expr_sum(grainGrown[group, year] for group in GROUPS)
        + grainBought[year] - grainSold[year]
        for year in YEARS), name='grain_req_def')

    sugarBeetGrown = {(year): sugar_beet_yield * sugarBeetAcres[year]
                      for year in YEARS}
    m.add_constraints((
        so.expr_sum(sugar_beet_req[age] * numCows[age, year] for age in AGES)
        <=
        sugarBeetGrown[year] + sugarBeetBought[year] - sugarBeetSold[year]
        for year in YEARS), name='sugar_beet_req_def')

    m.add_constraints((
        so.expr_sum(cow_labour_req[age] * numCows[age, year]
                     for age in AGES) +
        so.expr_sum(grain_labour_req * grainAcres[group, year]
                     for group in GROUPS) +
        sugar_beet_labour_req * sugarBeetAcres[year] <=
        nominal_labour_hours + numExcessLabourHours[year]
        for year in YEARS), name='labour_req_def')
    m.add_constraints((profit[year] >= 0 for year in YEARS), name='cash_flow')

    m.add_constraint(so.expr_sum(numCows[age, num_years] for age in AGES
                                  if age >= 2) /
                     sum(init_num_cows[age] for age in AGES if age >= 2) ==
                     [1-max_decrease_ratio, 1+max_increase_ratio],
                     name='final_dairy_cows_range')

    res = m.solve()

    if res is not None:
        so.pd.display_all()
        print(so.get_solution_table(numCows))
        revenue_df = so.dict_to_frame(revenue, cols=['revenue'])
        cost_df = so.dict_to_frame(cost, cols=['cost'])
        profit_df = so.dict_to_frame(profit, cols=['profit'])
        print(so.get_solution_table(numBullocksSold, numHeifersSold,
                                    capitalOutlay, numExcessLabourHours,
                                    revenue_df, cost_df, profit_df))
        gg_df = so.dict_to_frame(grainGrown, cols=['grainGrown'])
        print(so.get_solution_table(grainAcres, gg_df))
        sbg_df = so.dict_to_frame(sugarBeetGrown, cols=['sugerBeetGrown'])
        print(so.get_solution_table(
            grainBought, grainSold, sugarBeetAcres,
            sbg_df, sugarBeetBought, sugarBeetSold))
        num_acres = m.get_constraint('num_acres')
        na_df = num_acres.get_expressions()
        max_num_cows_con = m.get_constraint('max_num_cows_def')
        mnc_df = max_num_cows_con.get_expressions()
        print(so.get_solution_table(na_df, mnc_df))

    return m.get_objective_value()
