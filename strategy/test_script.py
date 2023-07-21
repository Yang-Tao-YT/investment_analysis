from strategy.factor_cross_section import calculate_indicator, FCS
from copy import deepcopy
from scipy import optimize
import pandas as pd
from data.generate_data import DataLoader
from utils.basic import rename_dataframe, Bar
from stock_strategy import StockIndex, stock_etf_hist_dataloader
from data.generate_data import DataLoader


fsc = FCS()
fsc.obtain_current_stockindex('sh510300')
fsc.obtain_current_indicator()

def solve_price_for_indicator(indicator):
    def test(x):
        return deepcopy(fsc).obtain_current_indicator(preset_close=x).values[-1] - indicator

    return optimize.root(test, 3).x

solve_price_for_indicator(30)

fsc.clean()