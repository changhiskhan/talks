import pandas as pd
import numpy as np
from pandas import DataFrame, Series

def runtest(name, start, end):
    rng = pd.date_range(start, end)
    rets = np.random.normal(0.00025, 0.009, len(rng))
    rs = DataFrame({'Gross' : rets, 'Net Commissions' : rets - 0.0002,
                    'Net Management Fees' : rets - 0.0002 - 0.0005}, rng)
    return rs

def calc_stats(rets):
    def maxdown(x):
        cum = (1 + x).cumprod() - 1
        maxes = pd.expanding_max(cum)
        diff = maxes - rets
        return diff.max()

    stats = {'Mean' : rets.mean(),
             'Std' : rets.std(),
             'Best' : rets.max(),
             'Worst' : rets.min(),
             'Max Drawdown' : maxdown(rets)}
    return DataFrame(stats)
