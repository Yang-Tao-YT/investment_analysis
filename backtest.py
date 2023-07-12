from utils.basic import name_2_symbol, rename_dataframe, Bar
from collections import defaultdict
from backtesting.stock_backtest import Backtest
from data.database import _get_hs300_history
import numpy as np
import pandas as pd

import config

from stock_strategy import StockIndex
from utils.plot import plot_kline_volume_signal_adept


def get_put(data):
    return data.loc[(data.tradecode.str.contains('P'))]

class RiskStrategyBacktest(Backtest):
    signal : pd.DataFrame

    def __init__(self, signal : pd.DataFrame, **kwargs):
        self.signal = signal
        self.signal['date'] = pd.to_datetime(self.signal['date'])
        pass

    def on_bar(self, date, data):

        signal = self.signal.loc[self.signal['date'] == date].drop('date', axis=1).squeeze()

        if signal[signal == 1]:
            self.long('300', 1000, data['close'].values[-1])
            self.position.loc[self.position['ticker'] == 'cash', 'shares'] -= 1000 * data['close'].values[-1]
        
        pass

def calculate_risk(data, setting):
        tool = StockIndex()
        tool.set_am(data)
        if setting is not None:
            tool.update_setting(setting=setting)

        risk = tool.risk()
        return risk.set_index(0)


def load_history_data(source = 'sina'):
    data = pd.read_csv(f'{config.path_to_save}/history/500etf.csv', index_col=0)
    def funs(strs):
        return strs[strs.rfind('M')-4 : strs.rfind('M')]
    data['expire_date'] = data['tradecode'].apply(funs)
    return data

def return_stockindex(symbol, setting : dict = None) -> StockIndex:
    print('rerun')
    stockindex = StockIndex()
    hist = stock_etf_hist_dataloader(symbol)
    hist = rename_dataframe(hist)
    hist['date'] = pd.to_datetime(hist['date']).dt.date
    stockindex.set_am(hist)
    setattr(stockindex, 'origin_data', hist.set_index('date')) 
    # update setting
    if setting is not None:
        stockindex.update_setting(setting=setting)
    return stockindex

def load_history_data():
    data = {}
    for key, value in name_2_symbol.items():
        symbol = value
        data[symbol] =  pd.read_csv(f'{config.path_hist_k_data}/{symbol}.csv')
        print(symbol)
        print('----------------')

    return data

if __name__ == '__main__':

    # load data
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
    signal[(risk.shift(1) > 12) & (risk < 10)] = 1
    signal = signal.reset_index().rename(columns={0 : 'date'})
    
    test = RiskStrategyBacktest(signal)
    test.load_config({
        'start_date' : '2018-01-01',
        'end_date' : '2022-12-31',
        'initial_account' : 1000000})
    
    test.load_data(data)
    test.run()



    # data = rename_dataframe(data.origin_data)
    # data = data.iloc[:, :6]
    # data.index = pd.to_datetime(data.index)
    # cerebro = bt.Cerebro()
    # cerebro.addstrategy(TestStrategy)

    # data_feed = bt.feeds.PandasData(dataname=data,
    #                                 # fromdate=start_date,
    #                                 # todate=end_date
    #                                 )
    # cerebro.adddata(data_feed)

    # cerebro.broker.setcash(100000.0)

    # # Print out the starting conditions
    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # # Run over everything
    # cerebro.run()

    # # Print out the final result
    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # 1