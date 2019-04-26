

import pandas as pd

Index = pd.Index
DataFrame = pd.DataFrame
MultiIndex = pd.MultiIndex


def convert_dict_to_frame(dictobj, cols=None):
    df = pd.DataFrame.from_dict(dictobj, orient='index')
    if isinstance(cols, list):
        df.columns = cols
    if isinstance(frobj.index[0], tuple):
        df.index = pd.MultiIndex.from_tuples(frobj.index)
    return df





