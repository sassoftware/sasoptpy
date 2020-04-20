import sasoptpy as so
import pandas as pd
from sasoptpy.util import iterate, concat
from sasoptpy.actions import (
    read_data, create_data, cofor_loop, for_loop, solve, if_condition, diff,
    print_item, inline_condition)


def test(cas_conn, get_tables=False):

    input_list = pd.DataFrame(
        ['staff', 'showroom', 'pop1', 'pop2', 'alpha_enq', 'beta_enq'],
        columns=['input'])
    input_data = cas_conn.upload_frame(
        data=input_list, casout={'name': 'input_data', 'replace': True})

    output_list = pd.DataFrame(
        ['alpha_sales', 'beta_sales', 'profit'], columns=['output'])
    output_data = cas_conn.upload_frame(
        data=output_list, casout={'name': 'output_data', 'replace': True})

    problem_data = pd.DataFrame([
        ['Winchester', 7, 8, 10, 12, 8.5, 4, 2, 0.6, 1.5],
        ['Andover', 6, 6, 20, 30, 9, 4.5, 2.3, 0.7, 1.6],
        ['Basingstoke', 2, 3, 40, 40, 2, 1.5, 0.8, 0.25, 0.5],
        ['Poole', 14, 9, 20, 25, 10, 6, 2.6, 0.86, 1.9],
        ['Woking', 10, 9, 10, 10, 11, 5, 2.4, 1, 2],
        ['Newbury', 24, 15, 15, 13, 25, 19, 8, 2.6, 4.5],
        ['Portsmouth', 6, 7, 50, 40, 8.5, 3, 2.5, 0.9, 1.6],
        ['Alresford', 8, 7.5, 5, 8, 9, 4, 2.1, 0.85, 2],
        ['Salisbury', 5, 5, 10, 10, 5, 2.5, 2, 0.65, 0.9],
        ['Guildford', 8, 10, 30, 35, 9.5, 4.5, 2.05, 0.75, 1.7],
        ['Alton', 7, 8, 7, 8, 3, 2, 1.9, 0.7, 0.5],
        ['Weybridge', 5, 6.5, 9, 12, 8, 4.5, 1.8, 0.63, 1.4],
        ['Dorchester', 6, 7.5, 10, 10, 7.5, 4, 1.5, 0.45, 1.45],
        ['Bridport', 11, 8, 8, 10, 10, 6, 2.2, 0.65, 2.2],
        ['Weymouth', 4, 5, 10, 10, 7.5, 3.5, 1.8, 0.62, 1.6],
        ['Portland', 3, 3.5, 3, 2, 2, 1.5, 0.9, 0.35, 0.5],
        ['Chichester', 5, 5.5, 8, 10, 7, 3.5, 1.2, 0.45, 1.3],
        ['Petersfield', 21, 12, 6, 8, 15, 8, 6, 0.25, 2.9],
        ['Petworth', 6, 5.5, 2, 2, 8, 5, 1.5, 0.55, 1.55],
        ['Midhurst', 3, 3.6, 3, 3, 2.5, 1.5, 0.8, 0.2, 0.45],
        ['Reading', 30, 29, 120, 80, 35, 20, 7, 2.5, 8],
        ['Southampton', 25, 16, 110, 80, 27, 12, 6.5, 3.5, 5.4],
        ['Bournemouth', 19, 10, 90, 12, 25, 13, 5.5, 3.1, 4.5],
        ['Henley', 7, 6, 5, 7, 8.5, 4.5, 1.2, 0.48, 2],
        ['Maidenhead', 12, 8, 7, 10, 12, 7, 4.5, 2, 2.3],
        ['Fareham', 4, 6, 1, 1, 7.5, 3.5, 1.1, 0.48, 1.7],
        ['Romsey', 2, 2.5, 1, 1, 2.5, 1, 0.4, 0.1, 0.55],
        ['Ringwood', 2, 3.5, 2, 2, 1.9, 1.2, 0.3, 0.09, 0.4],
    ], columns=['garage_name', 'staff', 'showroom', 'pop1', 'pop2', 'alpha_enq',
                'beta_enq', 'alpha_sales', 'beta_sales', 'profit'])
    garage_data = cas_conn.upload_frame(
        data=problem_data, casout={'name': 'garage_data', 'replace': True})

    with so.Workspace(name='efficiency_analysis', session=cas_conn) as w:
        inputs = so.Set(name='INPUTS', settype=so.string)
        read_data(table=input_data, index={'target': inputs, 'key': 'input'})

        outputs = so.Set(name='OUTPUTS', settype=so.string)
        read_data(table=output_data, index={'target': outputs, 'key': 'output'})

        garages = so.Set(name='GARAGES', settype=so.number)
        garage_name = so.ParameterGroup(garages, name='garage_name', ptype=so.string)
        input = so.ParameterGroup(inputs, garages, name='input')
        output = so.ParameterGroup(outputs, garages, name='output')
        r = read_data(table=garage_data, index={'target': garages, 'key': so.N},
                      columns=[garage_name])
        with iterate(inputs, 'i') as i:
            r.append({'index': i, 'target': input[i, so.N], 'column': i})
        with iterate(outputs, 'i') as i:
            r.append({'index': i, 'target': output[i, so.N], 'column': i})

        k = so.Parameter(name='k', ptype=so.number)
        efficiency_number = so.ParameterGroup(garages, name='efficiency_number')
        weight_sol = so.ParameterGroup(garages, garages, name='weight_sol')

        weight = so.VariableGroup(garages, name='Weight', lb=0)
        inefficiency = so.Variable(name='Inefficiency', lb=0)

        obj = so.Objective(inefficiency, name='Objective', sense=so.maximize)

        input_con = so.ConstraintGroup(
            (so.expr_sum(input[i, j] * weight[j] for j in garages) <= input[i, k]
             for i in inputs), name='input_con')
        output_con = so.ConstraintGroup(
            (so.expr_sum(output[i, j] * weight[j] for j in garages) >= output[i, k] * inefficiency
             for i in outputs), name='output_con')

        for kk in cofor_loop(garages):
            k.set_value(kk)
            solve()
            efficiency_number[k] = 1 / inefficiency.sol
            for j in for_loop(garages):
                def if_block():
                    weight_sol[k, j] = weight[j].sol
                def else_block():
                    weight_sol[k, j] = None
                if_condition(weight[j].sol > 1e-6, if_block, else_block)

        efficient_garages = so.Set(
            name='EFFICIENT_GARAGES',
            value=[j.sym for j in garages if j.sym.under_condition(efficiency_number[j] >= 1)])
        inefficient_garages = so.Set(value=diff(garages, efficient_garages), name='INEFFICIENT_GARAGES')

        p1 = print_item(garage_name, efficiency_number)
        ed = create_data(table='efficiency_data', index={'key': ['garage']}, columns=[
            garage_name, efficiency_number
        ])
        with iterate(inefficient_garages, 'inefficient_garage') as i:
            wd = create_data(table='weight_data_dense',
                             index={'key': [i], 'set': [i.get_set()]},
                             columns=[garage_name, efficiency_number])
            with iterate(efficient_garages, 'efficient_garage') as j:
                wd.append({
                    'name': concat('w', j),
                    'expression': weight_sol[i, j],
                    'index': j
                })

        filtered_set = so.InlineSet(
            lambda: ((g1, g2)
                     for g1 in inefficient_garages
                     for g2 in efficient_garages
                     if inline_condition(weight_sol[g1, g2] != None)))
        wds = create_data(table='weight_data_sparse',
                          index={'key': ['i', 'j'], 'set': [filtered_set]},
                          columns=[weight_sol])

    print(w.to_optmodel())
    w.submit()

    print('Print Table:')
    print(p1.get_response())

    print('Efficiency Data:')
    print(ed.get_response())

    print('Weight Data (Dense):')
    print(wd.get_response())

    print('Weight Data (Sparse):')
    print(wds.get_response())

    if get_tables:
        return obj.get_value(), ed.get_response()
    else:
        return obj.get_value()
