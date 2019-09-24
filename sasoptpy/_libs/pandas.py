

import pandas as pd

Index = pd.Index
MultiIndex = pd.MultiIndex
Series = pd.Series
DataFrame = pd.DataFrame


def convert_dict_to_frame(dictobj, cols=None):
    df = pd.DataFrame.from_dict(dictobj, orient='index')
    if isinstance(cols, list):
        df.columns = cols
    if isinstance(df.index[0], tuple):
        df.index = pd.MultiIndex.from_tuples(df.index)
    return df


def display_dense():
    pd.set_option('display.multi_sparse', False)

def display_all():
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)

concat = pd.concat


