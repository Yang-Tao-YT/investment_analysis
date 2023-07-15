from strategy.option.spred import Spred

import pandas as pd
import time
import os
import option_strategy
from data.generate_data import DataLoader
from utils.basic import rename_dataframe, Bar
from stock_strategy import StockIndex, stock_etf_hist_dataloader
from data.generate_data import DataLoader

loader =  DataLoader()
data = loader.current_em()
hs300 = loader.current_hs300sz_em()
greek = loader.current_risk_em()

data = pd.concat([data, hs300])
data = data.set_index('代码')
data = data.apply(pd.to_numeric,args=['ignore'])
data = data.loc[data.名称.str.startswith('300')]
spred = Spred()

spred.chose_contract(contracts=data, current_price=3.952)