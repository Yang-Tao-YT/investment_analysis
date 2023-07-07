from utils.basic import name_2_symbol, rename_dataframe, Bar
from collections import defaultdict


import numpy as np
import pandas as pd

import config

from option_strategy import Trading
from stock_strategy import StockIndex, barloader, stock_etf_hist_dataloader
from utils.plot import plot_kline_volume_signal_adept


def get_put(data):
    return data.loc[(data.tradecode.str.contains('P'))]

class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
        print(self.datas[0])

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

class BackTest:

    position = {'long':[], 'short':[]}
    trading_history = []
    bar = Bar()

    with open('trade_logs.log', 'w') as file:

        file.write('new logs here')
        
    def __init__(self,) -> None:
        pass

    def long( self, code, position,  price):
        self.on_order('long', code, price, position)
        pass

    def short(self, code, position,  price):
        self.on_order('short', code, price, position)

        pass

    def on_order(self, direction, code, price, position):
        self.trading_history.append([direction, code, price, position])
        self.position[direction].append([code, price, position])
        pass

    def on_trade(self):
        pass
    
    def balance(self, bar = None):
        if bar is None:
            bar = self.bar
        print(self.position)
        value = 0
        for direction in self.position:
            for position in self.position[direction]:
                value += bar.close.loc[position[0]] * position[2]
        
        return value

    def update_bar(self, df):
        self.bar.update_bar(df)

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



if __name__ == '__main__':


    # test = BackTest()

    # load data
    data = return_stockindex('sh515790')
    data = rename_dataframe(data.origin_data)
    data = data.iloc[:, :6]
    data.index = pd.to_datetime(data.index)
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)

    data_feed = bt.feeds.PandasData(dataname=data,
                                    # fromdate=start_date,
                                    # todate=end_date
                                    )
    cerebro.adddata(data_feed)

    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    1