from backtesting.stock.risk_indicator import RiskStrategyStatistic, RiskStrategyBacktest
from utils.basic import name_2_symbol, rename_dataframe, Bar
import numpy as np
import pandas as pd

import config

from strategy.stock_strategy import StockIndex
from utils.plot import plot_kline_volume_signal_adept

def calculate_risk(data, setting):
        tool = StockIndex()
        tool.set_am(data)
        if setting is not None:
            tool.update_setting(setting=setting)

        risk = tool.risk()
        return risk.set_index(0)

def load_history_data():
    data = {}
    for key, value in name_2_symbol.items():
        try:
            symbol = value
            data[symbol] =  pd.read_csv(f'{config.path_hist_k_data}/{symbol}.csv')
            print(symbol)
            print('----------------')
        except:
             pass
    return data

def backtest_main():
    data = load_history_data()
    data = pd.concat(data).reset_index()
    data = data.rename(columns={'level_0': 'ticker',
                        '日期' : 'date',
                        '執行時間' : 'time',
                        '开盘' : 'open',
                        '收盘' : 'close',
                        '最高' : 'high',
                        '最低' : 'low',
                        '成交量' : 'volume',})
    # generate signal
    risk = data.groupby('ticker').apply(calculate_risk, {'ma_window' : 3})
    risk = risk.swaplevel().squeeze().unstack()

    signal = pd.DataFrame(np.zeros(risk.shape), index=risk.index, columns=risk.columns)
    signal[(risk.shift(1) > 15) & (risk < 10)] = 1
    signal = signal.reset_index().rename(columns={0 : 'date'})
    
    test = RiskStrategyBacktest(signal)
    test.load_config({
        'start_date' : '2018-01-01',
        'end_date' : '2022-12-31',
        'initial_account' : 10000})
    
    test.load_data(data)
    test.run()
    print(test.return_value_records())

if __name__ == '__main__':

    model = RiskStrategyStatistic()
    data = load_history_data()
    data = pd.concat(data).reset_index()
    data = data.rename(columns={'level_0': 'ticker',
                        '日期' : 'date',
                        '執行時間' : 'time',
                        '开盘' : 'open',
                        '收盘' : 'close',
                        '最高' : 'high',
                        '最低' : 'low',
                        '成交量' : 'volume',})

    model.load_data(data)
    model.generate_signal(data.loc[data['date'] > '20180101'])
    model.generate_trade()
