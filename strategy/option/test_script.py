from strategy.option.spred import Spred

import pandas as pd
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
data = data.loc[data['剩余日'] ==  40]

spred = Spred()

up,down = spred.chose_contract(contracts=data, current_price=3.952, spred_type = 'C')

returns = spred.bullspread_call(
    K1 = down['执行价'].squeeze(),
    K2 = up['执行价'].squeeze(),
    C1 = down['最新价'].squeeze(),
    C2 = up['最新价'].squeeze(),
    P0 = 3.952,
    P0_index=3.952,
    Pt_index=3.952,
    N1=1,
    N2=1,
    N_underlying=1
)[-1]

margin = spred.margin(    
    K1 = down['执行价'].squeeze(),
    K2 = up['执行价'].squeeze(),
    C1 = down['最新价'].squeeze(),
    C2 = up['最新价'].squeeze(),)

returns / margin


up,down = spred.chose_contract(contracts=data, current_price=3.952, spred_type = 'P')

returns = spred.bullspread_put(
    K1 = down['执行价'].squeeze(),
    K2 = up['执行价'].squeeze(),
    P1 = down['最新价'].squeeze(),
    P2 = up['最新价'].squeeze(),
    P0 = 3.952,
    P0_index=3.952,
    Pt_index=up['执行价'].squeeze(),
    N1=1,
    N2=1,
    N_underlying=1
)[-1]


margin = spred.margin(    
    K1 = down['执行价'].squeeze(),
    K2 = up['执行价'].squeeze(),
    C1 = down['最新价'].squeeze(),
    C2 = up['最新价'].squeeze(),)

returns / margin
K1 = down['执行价'].squeeze()
K2 = up['执行价'].squeeze()
P1 = down['最新价'].squeeze()
P2 = up['最新价'].squeeze()
Pt_index=up['执行价'].squeeze()
P2 - (K2 - Pt_index) - P1